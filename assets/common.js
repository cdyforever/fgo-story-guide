/* 共用外壳：游戏切换导航 + 页内播放器 + 回顶按钮 */
const GAMES = [
  { id: "portal",  name: "🏠 首页",     url: "index.html",  color: null,   status: "live" },
  { id: "fgo",     name: "FGO",         url: "fgo.html",    color: "#d8b45a", status: "live" },
  { id: "genshin", name: "原神",        url: "genshin.html", color: "#5aa893", status: "live" },
  { id: "hsr",     name: "星穹铁道",    url: null,          color: null,   status: "soon" },
];

function renderGameNav() {
  const holders = document.querySelectorAll(".game-nav[data-game]");
  holders.forEach(h => {
    const cur = h.getAttribute("data-game");
    h.innerHTML = GAMES.map(g => {
      if (g.status === "soon") return `<span class="gsoon" title="制作中，敬请期待">${g.name}（筹备中）</span>`;
      return `<a class="gtab${g.id === cur ? " current" : ""}" href="${g.url}">${g.name}</a>`;
    }).join("");
  });
}

/* 页内播放器 */
function play(bv, p, title) {
  const dock = document.getElementById("dock");
  if (!dock) return;
  document.getElementById("dockTitle").textContent = "▶ " + title + "（Bilibili 播放器）";
  document.getElementById("dockFrame").innerHTML =
    '<iframe src="https://player.bilibili.com/player.html?bvid=' + bv + '&p=' + (p || 1) +
    '&autoplay=0&danmaku=1&high_quality=1" allowfullscreen scrolling="no"></iframe>';
  dock.style.display = "block";
}
function closeDock() {
  const dock = document.getElementById("dock");
  if (dock) { dock.style.display = "none"; document.getElementById("dockFrame").innerHTML = ""; }
}

window.addEventListener("DOMContentLoaded", () => {
  renderGameNav();
  const topBtn = document.getElementById("topBtn");
  if (topBtn) window.addEventListener("scroll", () => {
    topBtn.style.display = window.scrollY > 600 ? "block" : "none";
  });
});
