# -*- coding: utf-8 -*-
"""
Markdown → 静态HTML 构建器（剧情指南内容管线）
用法：python tools/build.py                # 构建全部 content/*.md
     python tools/build.py hsr-amphoreus  # 只构建指定 page-id

格式约定见 content/hsr-amphoreus.md 顶部注释与 tools/build.py 头注释。
"""
import os, re, sys, io, glob, html as H

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT = os.path.join(ROOT, "content")

def esc(s): return H.escape(s, quote=False)

def inline(s):
    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2" target="_blank">\1</a>', s)
    return s

def attrs_parse(s):
    d = {}
    m = re.search(r"p:\s*\[\s*(\d+)\s*,\s*(\d+)\s*\]", s)
    if m:
        d["p"] = "[%s,%s]" % (m.group(1), m.group(2))
        s = s[:m.start()] + s[m.end():]
    for part in s.split(","):
        part = part.strip()
        if not part: continue
        if ":" in part:
            k, v = part.split(":", 1)
            d[k.strip()] = v.strip()
        else:
            d[part.strip()] = "1"
    return d

LVL = {"light": ("轻剧透", "lvl-e"), "mid": ("中度剧透", "lvl-m"), "heavy": ("重度剧透", "lvl-f")}
def chip(lvl):
    if lvl in LVL:
        t, c = LVL[lvl]
        return f'<span class="lvl {c}">{t}</span>'
    return ""

def parse(md_path):
    text = open(md_path, encoding="utf-8").read()
    parts = re.split(r"^---\s*$", text, maxsplit=2, flags=re.M)
    fm_raw, body = (parts[1], parts[2]) if len(parts) >= 3 else ("", text)
    meta, navs, stats = {}, [], []
    for ln in fm_raw.strip().splitlines():
        if ":" not in ln: continue
        k, v = ln.split(":", 1); k, v = k.strip(), v.strip()
        if k == "nav": navs.append(tuple(v.split("=", 1)))
        elif k == "stat": stats.append(tuple(v.split("|", 1)))
        else: meta[k] = v
    # 分词：h2 / h3 / fence / p / ul
    toks, i, lines = [], 0, body.splitlines()
    while i < len(lines):
        s = lines[i].strip()
        if not s: i += 1; continue
        if s.startswith(":::"):
            kind, buf = s[3:].strip(), []
            i += 1
            while i < len(lines) and lines[i].strip() != ":::":
                buf.append(lines[i]); i += 1
            i += 1
            toks.append(("fence", kind, buf))
        elif s.startswith("## "):
            t = s[3:]
            m = re.search(r"\{(.+)\}$", t)
            at = attrs_parse(m.group(1)) if m else {}
            toks.append(("h2", t[:m.start()].strip() if m else t, at)); i += 1
        elif s.startswith("### "):
            t = s[4:]
            m = re.search(r"\{(.+)\}$", t)
            at = attrs_parse(m.group(1)) if m else {}
            buf = []
            i += 1
            while i < len(lines) and lines[i].strip() and not lines[i].strip().startswith(("### ", "## ", ":::", "- ")):
                buf.append(lines[i].strip()); i += 1
            toks.append(("h3", t[:m.start()].strip() if m else t, at, buf))
        elif s.startswith("- "):
            items = []
            while i < len(lines) and lines[i].strip().startswith("- "):
                items.append(lines[i].strip()[2:]); i += 1
            toks.append(("ul", items))
        else:
            buf = [s]; i += 1
            while i < len(lines) and lines[i].strip() and not lines[i].strip().startswith(("### ", "## ", ":::", "- ")):
                buf.append(lines[i].strip()); i += 1
            toks.append(("p", " ".join(buf)))
    return meta, navs, stats, toks

def fence_html(kind, buf, bv):
    if kind == "note":
        return f'<div class="note">{"".join(inline(x) for x in buf)}</div>'
    if kind == "pbtns":
        out = ['<div class="pbtns">']
        for ln in buf:
            m = re.match(r"\[([^\]]+)\|(\d+(?:-\d+)?)\]", ln.strip())
            if m:
                out.append(f'<a class="pbtn" href="https://www.bilibili.com/video/{bv}?p={m.group(2).split("-")[0]}" target="_blank">▶ {esc(m.group(1))}</a>')
        out.append("</div>")
        return "\n".join(out)
    if kind == "cards2":
        cards, cur_t, cur_b = [], None, []
        for ln in buf:
            s = ln.strip()
            if s.startswith("### "):
                if cur_t is not None: cards.append((cur_t, cur_b))
                cur_t, cur_b = s[4:], []
            elif cur_t is not None and s:
                cur_b.append(s)
        if cur_t is not None: cards.append((cur_t, cur_b))
        inner = "".join(f'<div class="card"><div class="body"><h4>{inline(t)}</h4><p class="gray" style="font-size:13px">{inline(" ".join(b))}</p></div></div>' for t, b in cards)
        return f'<div class="grid g2">{inner}</div>'
    if kind == "personas":
        out, cur = [], None
        for ln in buf:
            s = ln.strip()
            if not s: continue
            m = re.match(r"^(.+?)\s*\{(light|mid|heavy)\}$", s)
            if m:
                if cur: out.append(cur)
                name, lvl = m.group(1), m.group(2)
                cur = {"name": name, "lvl": lvl, "desc": "", "btns": []}
            elif cur is not None:
                m2 = re.match(r"^(.*?)\|(\d+(?:-\d+)?)$", s)
                if m2:
                    cur["btns"].append((m2.group(1), m2.group(2)))
                elif not cur["desc"]:
                    cur["desc"] = s
                else:
                    cur["btns"].append((s, None))
        if cur: out.append(cur)
        inner = ""
        for c in out:
            btns = "".join(f'<a class="pbtn" href="https://www.bilibili.com/video/{bv}?p={(b[1] or "1").split("-")[0]}" target="_blank">▶ {esc(b[0])}</a>' for b in c["btns"] if b[1])
            inner += (f'<div class="persona"><h5>{inline(c["name"])}{chip(c["lvl"])}</h5>'
                      f'<p>{inline(c["desc"])}</p><div class="pbtns">{btns}</div></div>')
        return f'<div class="grid g2">{inner}</div>'
    if kind == "reveal":
        inner = "".join(f"<p>{inline(x)}</p>" if not x.strip().startswith("### ") else f"<h4>{inline(x.strip()[4:])}</h4>" for x in buf if x.strip())
        return ('<div class="reveal" data-lvl="heavy"><div class="reveal-mask">🔒 重度剧透内容已遮挡 — 点击显影</div>'
                f'<div class="reveal-body">{inner}</div></div>')
    if kind == "fold":
        t = buf[0].strip() if buf else "展开"
        inner = "".join(inline(x) for x in buf[1:])
        return f'<details class="fold"><summary>{inline(t)}</summary><div>{inner}</div></details>'
    return ""

def render(meta, navs, stats, toks):
    bv = meta.get("source-bv", "")
    page_id = meta.get("page-id", "page")
    o = []
    o.append(f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(meta.get("page-title","剧情指南"))}</title>
<link rel="stylesheet" href="assets/style.css">
</head>
<body class="theme-{esc(meta.get("theme","fgo"))}">
<div class="hero"><div class="wrap">
<h1><small>{esc(meta.get("hero-eyebrow",""))}</small>{esc(meta.get("hero-title",""))}</h1>''')
    if meta.get("hero-lead"):
        o.append(f'<p class="lead">{inline(meta["hero-lead"])}</p>')
    if stats:
        o.append('<div class="stats">' + "".join(f'<div class="stat"><b>{esc(a)}</b><span>{esc(b)}</span></div>' for a, b in stats) + '</div>')
    o.append('</div></div>')
    o.append(f'<nav class="game-nav" data-game="{esc(meta.get("game","fgo"))}"></nav>')
    nav_html = "".join(f'<a href="#{esc(i)}">{esc(t)}</a>' for i, t in navs)
    o.append(f'<nav><div class="wrap">{nav_html}</div></nav>')
    # 观看进度条（由 reader.js 填充）
    o.append(f'<div class="read-progress" data-page="{esc(page_id)}" style="display:none"><div class="wrap"><span class="rp-label"></span><div class="rp-bar"><div class="rp-fill"></div></div><button class="rp-unspoiled">👁 我已看完 · 展开全部剧透</button></div></div>')
    o.append('<div class="wrap">')

    sec_open, act_open = False, False
    used_acts = set()
    def close_act():
        nonlocal act_open
        if act_open:
            o.append('<div class="act-foot"><label class="watch"><input type="checkbox" class="watch-ck"> 本幕已看</label></div>')
            o.append('</div>')  # chapter
        act_open = False
    for tok in toks:
        kind = tok[0]
        if kind == "h2":
            close_act()
            if sec_open: o.append('</section>')
            _, title, at = tok
            o.append(f'<section id="{esc(at.get("id",""))}">')
            o.append(f'<h2 class="sec">{inline(title)}{chip(at.get("spoiler"))}</h2>')
            if at.get("sub"): o.append(f'<p class="sec-sub">{inline(at["sub"])}</p>')
            if at.get("type") == "sourcecard":
                o.append(f'''<div class="card" style="margin-top:34px;">
<img class="cover" src="{esc(meta.get("source-cover",""))}" referrerpolicy="no-referrer" alt="">
<div class="body"><span class="tag">本页唯一片源</span>
<h4>{esc(meta.get("source-label",""))}</h4><div class="meta">{esc(meta.get("source-meta",""))}</div>
<p class="gray" style="font-size:13px">{inline(meta.get("source-note",""))}</p>
<div class="btns"><a class="btn gold" href="https://www.bilibili.com/video/{bv}" target="_blank">↗ 打开合集</a></div></div></div>''')
            sec_open = True
        elif kind == "h3":
            _, title, at, buf = tok
            if "act" in at:
                close_act()
                ver = at.get("ver", "")
                act_id = "act-" + ver.replace(".", "")
                n = 2
                while act_id in used_acts:
                    act_id = "act-%s-%d" % (ver.replace(".", ""), n)
                    n += 1
                used_acts.add(act_id)
                pr = re.match(r"\[(\d+),\s*(\d+)\]", at.get("p", "[]"))
                o.append(f'<div class="chapter act" data-act="{act_id}" id="{act_id}">')
                o.append(f'<div class="head"><div class="emblem">{esc(ver)}</div><div><h3>{inline(title)}{chip(at.get("spoiler"))}</h3>')
                if at.get("sub"): o.append(f'<div class="subtitle">{inline(at["sub"])}</div>')
                o.append('</div></div>')
                for ln in buf:
                    if ln.strip().startswith("**"):
                        o.append(f'<div class="lbl">{inline(ln.strip().strip("*"))}</div>')
                    else:
                        o.append(f'<p>{inline(ln)}</p>')
                if pr:
                    o.append(f'<div class="pbtns"><a class="pbtn" href="https://www.bilibili.com/video/{bv}?p={pr.group(1)}" target="_blank">▶ 本幕从P{pr.group(1)}看</a></div>')
                act_open = True
            else:
                o.append(f'<h3>{inline(title)}{chip(at.get("spoiler"))}</h3>')
        elif kind == "fence":
            k, buf = tok[1], tok[2]
            if k == "pbtns" and act_open:
                o.append(fence_html("pbtns", buf, bv))
            elif k == "note" and act_open:
                o.append(fence_html("note", buf, bv)); close_act()
            else:
                close_act()
                o.append(fence_html(k, buf, bv))
        elif kind == "p":
            o.append(f'<p>{inline(tok[1])}</p>')
        elif kind == "ul":
            o.append('<ul class="hl">' + "".join(f"<li>{inline(x)}</li>" for x in tok[1]) + '</ul>')
    close_act()
    if sec_open: o.append('</section>')
    o.append('</div><!-- /wrap -->')
    o.append(f'''<footer><div class="wrap"><p>{inline(meta.get("footer",""))}</p>
<p>内容源文件 content/{page_id}.md · 构建于 {__import__("time").strftime("%Y-%m-%d %H:%M")} · 视频版权归原作者与各 UP 主所有</p></div></footer>
<button class="top-btn" id="topBtn" onclick="window.scrollTo({{top:0,behavior:'smooth'}})">▲ 回到顶部</button>
<div id="dock"><div class="bar"><span id="dockTitle">页面内播放</span><button onclick="closeDock()">✕ 关闭</button></div><div id="dockFrame"></div></div>
<script src="assets/common.js"></script>
<script src="assets/reader.js"></script>
</body></html>''')
    return "\n".join(o)

def main():
    os.makedirs(CONTENT, exist_ok=True)
    targets = sys.argv[1:]
    built = 0
    for md in sorted(glob.glob(os.path.join(CONTENT, "*.md"))):
        pid = os.path.basename(md)[:-3]
        if targets and pid not in targets:
            continue
        meta, navs, stats, toks = parse(md)
        html = render(meta, navs, stats, toks)
        out = os.path.join(ROOT, pid + ".html")
        open(out, "w", encoding="utf-8").write(html)
        print(f"built {pid}.html ({len(html)} chars)")
        built += 1
    if not built:
        print("no matching content files")

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    main()
