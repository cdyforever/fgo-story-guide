/**
 * 剧情指南本地预览服务器（多页面版）
 * 1) 提供 index/fgo/genshin 页面与 assets 静态资源
 * 2) 所有 hdslb 封面图走本地代理（补 Referer 绕过防盗链，带缓存）
 * 由「启动FGO剧情指南.bat」调用，启动后自动打开浏览器。
 */
const http = require("http");
const fs = require("fs");
const path = require("path");
const { exec } = require("child_process");

const PORT_START = 8765;
const ROOT = __dirname;
const MIME = { ".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".png": "image/png", ".jpg": "image/jpeg", ".json": "application/json; charset=utf-8" };
const UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36";
const imgCache = new Map();

function rewriteImages(html) {
  return html.replace(
    /(src=")(https?:\/\/i\d\.hdslb\.com\/[^"]+)(")/g,
    (m, a, url, c) => a + "/px?u=" + encodeURIComponent(url) + c
  );
}

function proxyImage(url, res) {
  const cached = imgCache.get(url);
  if (cached) {
    res.writeHead(200, { "Content-Type": url.endsWith(".png") ? "image/png" : "image/jpeg", "Cache-Control": "public, max-age=86400" });
    return res.end(cached);
  }
  const req = require("https").get(url, { headers: { "User-Agent": UA, "Referer": "https://www.bilibili.com/" } }, (up) => {
    if (up.statusCode !== 200) { res.writeHead(502); return res.end(); }
    const chunks = [];
    up.on("data", (c) => chunks.push(c));
    up.on("end", () => {
      const buf = Buffer.concat(chunks);
      if (imgCache.size > 800) imgCache.clear();
      imgCache.set(url, buf);
      res.writeHead(200, { "Content-Type": up.headers["content-type"] || "image/jpeg", "Cache-Control": "public, max-age=86400" });
      res.end(buf);
    });
  });
  req.on("error", () => { res.writeHead(502); res.end(); });
  req.setTimeout(15000, () => req.destroy());
}

function serveFile(rel, res) {
  const file = path.join(ROOT, rel);
  if (!file.startsWith(ROOT) || !fs.existsSync(file) || !fs.statSync(file).isFile()) {
    res.writeHead(404); return res.end("not found");
  }
  const ext = path.extname(file);
  if (ext === ".html") {
    res.writeHead(200, { "Content-Type": MIME[".html"], "Cache-Control": "no-cache" });
    return res.end(rewriteImages(fs.readFileSync(file, "utf-8")));
  }
  res.writeHead(200, { "Content-Type": MIME[ext] || "application/octet-stream" });
  res.end(fs.readFileSync(file));
}

function start(port) {
  const server = http.createServer((req, res) => {
    const u = new URL(req.url, "http://127.0.0.1");
    if (u.pathname === "/px") {
      const target = u.searchParams.get("u");
      if (!target || !/^https?:\/\/i\d\.hdslb\.com\//.test(target)) { res.writeHead(400); return res.end(); }
      return proxyImage(target, res);
    }
    const rel = u.pathname === "/" ? "index.html" : u.pathname.slice(1);
    return serveFile(rel, res);
  });
  server.on("error", (e) => {
    if (e.code === "EADDRINUSE" && port < PORT_START + 20) return start(port + 1);
    console.error("启动失败:", e.message);
  });
  server.listen(port, "127.0.0.1", () => {
    const url = `http://127.0.0.1:${port}/`;
    console.log("================================================");
    console.log("  剧情追剧指南（多游戏版）已启动");
    console.log("  地址: " + url);
    console.log("  浏览器将自动打开；看完后关闭本窗口即可退出。");
    console.log("================================================");
    exec((process.platform === "win32" ? `start "" "${url}"` : process.platform === "darwin" ? `open "${url}"` : `xdg-open "${url}"`), () => {});
  });
}

start(PORT_START);
