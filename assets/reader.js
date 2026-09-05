/* 阅读器：观看进度 + 剧透遮罩（红遮黄露）+ 全局展开开关 */
(function () {
  var bar = document.querySelector(".read-progress");
  if (!bar) return;
  var page = bar.getAttribute("data-page");
  var LSK = "watched:" + page, USK = "unspoiled";

  var acts = Array.prototype.slice.call(document.querySelectorAll(".act"));

  function getW() { try { return JSON.parse(localStorage.getItem(LSK) || "{}"); } catch (e) { return {}; } }
  function setW(o) { try { localStorage.setItem(LSK, JSON.stringify(o)); } catch (e) {} }

  function paint() {
    var w = getW();
    var n = acts.filter(function (a) { return w[a.getAttribute("data-act")]; }).length;
    bar.querySelector(".rp-label").textContent = "观看进度 " + n + "/" + acts.length;
    bar.querySelector(".rp-fill").style.width = (acts.length ? 100 * n / acts.length : 0) + "%";
  }

  if (acts.length) {
    bar.style.display = "flex";
    var w0 = getW();
    acts.forEach(function (a) {
      var id = a.getAttribute("data-act");
      var ck = a.querySelector(".watch-ck");
      if (!ck) return;
      ck.checked = !!w0[id];
      ck.addEventListener("change", function () {
        var w = getW();
        if (ck.checked) w[id] = 1; else delete w[id];
        setW(w); paint();
      });
    });
  }

  var btn = bar.querySelector(".rp-unspoiled");
  function paintUS() {
    var on = false;
    try { on = localStorage.getItem(USK) === "1"; } catch (e) {}
    document.body.classList.toggle("unspoiled", on);
    btn.classList.toggle("on", on);
    btn.textContent = on ? "🙈 恢复剧透遮挡" : "👁 我已看完 · 展开全部剧透";
  }
  btn.addEventListener("click", function () {
    try { localStorage.setItem(USK, localStorage.getItem(USK) === "1" ? "0" : "1"); } catch (e) {}
    paintUS();
  });

  Array.prototype.forEach.call(document.querySelectorAll(".reveal"), function (r) {
    var mask = r.querySelector(".reveal-mask");
    if (mask) mask.addEventListener("click", function () { r.classList.add("revealed"); });
  });

  paint(); paintUS();
})();
