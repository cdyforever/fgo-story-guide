# -*- coding: utf-8 -*-
"""
追更流水线：检测各游戏页面登记的监控合集是否有新增分P。
用法：
  python tools/update.py            # 检测全部游戏，输出报告
  python tools/update.py --game fgo # 只检测某个游戏
检测到新分P时，会在对应HTML的追更区块自动插入"占位卡片"（含直达链接），
站长再补写梗概与名场面即可。发布：git add -A && git commit -m "..." && git push
"""
import json, re, sys, time, urllib.request, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
UA = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.bilibili.com/"}
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def api(bvid):
    req = urllib.request.Request(f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}", headers=UA)
    for _ in range(3):
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception:
            time.sleep(2)
    return None

PLACEHOLDER = '''
  <div class="chapter" id="auto-{bvid}-{p}">
    <div class="head"><div class="emblem">新</div>
      <div><h3>{label} · 新分P（梗概待补）</h3>
      <div class="subtitle">由追更脚本自动添加于 {date}</div></div>
    </div>
    <p class="gray">检测到监控合集更新：<b>P{p} {title}</b>。点击下方按钮直达观看；站长补写梗概与名场面后，本卡片会被合并进对应章节。</p>
    <div class="linkrow"><a class="btn gold" href="https://www.bilibili.com/video/{bvid}?p={p}" target="_blank">▶ 观看 P{p}</a></div>
  </div>
  <!-- AUTO-UPDATE-ANCHOR -->'''

def process(path):
    html = open(path, encoding="utf-8").read()
    m = re.search(r'<script type="application/json" id="watch-meta">(.*?)</script>', html, re.S)
    if not m:
        return
    meta = json.loads(m.group(1))
    game, updates = meta.get("game"), []
    for c in meta.get("collections", []):
        d = api(c["bvid"])
        if not d or d.get("code") != 0:
            print(f"  [{game}] {c['label']}: API失败，跳过")
            continue
        pages = d["data"].get("pages", [])
        n = len(pages)
        if n > c["known_p"]:
            new = pages[c["known_p"]:]
            print(f"  [{game}] {c['label']}: {c['known_p']}P -> {n}P，新增 {len(new)} 个分P")
            for pg in new:
                print(f"      P{pg['page']}: {pg['part']}")
                updates.append((c, pg))
        else:
            print(f"  [{game}] {c['label']}: 无更新（{n}P）")
        time.sleep(0.8)
    if updates:
        date = time.strftime("%Y-%m-%d")
        if "--fix" in sys.argv:
            # 在页面第一个 anchor 处插入占位卡片，并把 known_p 更新到当前值
            blocks = []
            for c, pg in updates:
                blocks.append(PLACEHOLDER.format(bvid=c["bvid"], p=pg["page"], title=pg["part"],
                                                 label=c["label"], date=date))
            html = html.replace("<!-- AUTO-UPDATE-ANCHOR -->", "".join(blocks), 1)
            for c, pg in updates:
                html = html.replace(
                    '{"bvid":"%s","label":"%s","known_p":%d' % (c["bvid"], c["label"], c["known_p"]),
                    '{"bvid":"%s","label":"%s","known_p":%d' % (c["bvid"], c["label"], len(api(c["bvid"])["data"]["pages"])),
                )
            open(path, "w", encoding="utf-8").write(html)
            print(f"  -> 已向 {os.path.basename(path)} 插入 {len(updates)} 张占位卡片（补写梗概后 git 提交）")
        else:
            print("  -> 使用 --fix 参数可自动插入占位卡片")

def main():
    only = None
    if "--game" in sys.argv:
        only = sys.argv[sys.argv.index("--game") + 1]
    files = [f for f in os.listdir(ROOT) if re.match(r".*\.html$", f)]
    for f in sorted(files):
        p = os.path.join(ROOT, f)
        if "watch-meta" not in open(p, encoding="utf-8").read():
            continue
        game = re.search(r'data-game="([a-z]+)"', open(p, encoding="utf-8").read())
        if only and (not game or game.group(1) != only):
            continue
        print(f"== {f}")
        process(p)

if __name__ == "__main__":
    main()
