/**
 * FGO剧情追剧指南 - 本地预览服务器
 * 作用：1) 以 http 方式提供页面（避免 file:// 直接触发B站风控）
 *      2) 封面图走本地代理转发（补上 Referer，绕过防盗链）
 * 直接双击「启动FGO剧情指南.bat」即可，页面会自动在浏览器打开。
 */
const http = require("http");
const fs = require("fs");
const path = require("path");
const { exec } = require("child_process");

const PORT_START = 8765;
const HTML_FILE = path.join(__dirname, "FGO剧情追剧指南.html");
const UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36";
const imgCache = new Map(); // url -> Buffer

function rewriteHtml() {
  let html = fs.readFileSync(HTML_FILE, "utf-8");
  // 把 hdslb 封面图替换为本地代理地址
  html = html.replace(
    /(src=")(https?:\/\/i\d\.hdslb\.com\/[^"]+)(")/g,
    (m, a, url, c) => a + "/px?u=" + encodeURIComponent(url) + c
  );
  return html;
}

function proxyImage(url, res) {
  const cached = imgCache.get(url);
  if (cached) {
    res.writeHead(200, { "Content-Type": url.endsWith(".png") ? "image/png" : "image/jpeg", "Cache-Control": "public, max-age=86400" });
    return res.end(cached);
  }
  const req = require("https").get(url, { headers: { "User-Agent": UA, "Referer": "https://www.bilibili.com/" } }, (up) => {
    if (up.statusCode !== 200) {
      res.writeHead(502); return res.end("image upstream " + up.statusCode);
    }
    const chunks = [];
    up.on("data", (c) => chunks.push(c));
    up.on("end", () => {
      const buf = Buffer.concat(chunks);
      if (imgCache.size > 500) imgCache.clear();
      imgCache.set(url, buf);
      res.writeHead(200, { "Content-Type": up.headers["content-type"] || "image/jpeg", "Cache-Control": "public, max-age=86400" });
      res.end(buf);
    });
  });
  req.on("error", (e) => { res.writeHead(502); res.end("proxy error"); });
  req.setTimeout(15000, () => req.destroy());
}

function openBrowser(url) {
  const cmd = process.platform === "win32" ? `start "" "${url}"`
            : process.platform === "darwin" ? `open "${url}"`
            : `xdg-open "${url}"`;
  exec(cmd, () => {});
}

function start(port) {
  const server = http.createServer((req, res) => {
    const u = new URL(req.url, "http://127.0.0.1");
    if (u.pathname === "/px") {
      const target = u.searchParams.get("u");
      if (!target || !/^https?:\/\/i\d\.hdslb\.com\//.test(target)) { res.writeHead(400); return res.end(); }
      return proxyImage(target, res);
    }
    if (u.pathname === "/" || u.pathname === "/index.html") {
      try {
        const html = rewriteHtml();
        res.writeHead(200, { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-cache" });
        return res.end(html);
      } catch (e) {
        res.writeHead(500); return res.end("读取 HTML 失败: " + e.message);
      }
    }
    res.writeHead(404); res.end();
  });

  server.on("error", (e) => {
    if (e.code === "EADDRINUSE" && port < PORT_START + 20) return start(port + 1);
    console.error("启动失败:", e.message);
  });

  server.listen(port, "127.0.0.1", () => {
    const url = `http://127.0.0.1:${port}/`;
    console.log("================================================");
    console.log("  FGO 剧情追剧指南已启动");
    console.log("  地址: " + url);
    console.log("  浏览器将自动打开；看完后关闭本窗口即可退出。");
    console.log("================================================");
    openBrowser(url);
  });
}

start(PORT_START);
