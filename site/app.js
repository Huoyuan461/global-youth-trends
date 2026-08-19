/* 全球 + 中国青年关注榜 — 前端渲染（读取 window.DATA） */
(function () {
  "use strict";
  var DATA = window.DATA || { items: [], status: {}, count: 0, updated_at: "" };

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function fmtHeat(h) {
    if (h === null || h === undefined || h === "") return "";
    h = Number(h);
    if (!isFinite(h)) return "";
    if (h >= 1e8) return (h / 1e8).toFixed(1) + "亿";
    if (h >= 1e4) return (h / 1e4).toFixed(1) + "万";
    return String(h);
  }
  function regionChip(r) {
    return r === "cn"
      ? '<span class="chip cn">🇨🇳国内</span>'
      : '<span class="chip global">🌍全球</span>';
  }
  function byRegion(region) {
    return DATA.items.filter(function (i) { return i.region === region; });
  }
  function groupByPlatform(items) {
    var m = {};
    items.forEach(function (i) {
      (m[i.platform] = m[i.platform] || []).push(i);
    });
    return m;
  }
  function rowsHtml(items, opts) {
    opts = opts || {};
    if (!items.length) return '<div class="empty">暂无数据（数据源可能延迟）。</div>';
    return items.map(function (it, i) {
      var extra = "";
      if (opts.platform) extra += '<span class="pf">' + esc(it.platform) + "</span>";
      if (opts.region) extra += regionChip(it.region);
      if (opts.category) extra += '<span class="tag">' + esc(it.category) + "</span>";
      var heat = fmtHeat(it.heat);
      var scoreCell = opts.score ? '<td class="heat">' + (heat || it.score) + "</td>" : "";
      var heatCell = !opts.score ? '<td class="heat">' + (heat || "—") + "</td>" : "";
      var catCell = !opts.category ? '<td><span class="tag">' + esc(it.category) + "</span></td>" : "";
      return "<tr>" +
        '<td class="rank">' + (i + 1) + "</td>" +
        "<td>" + extra +
          '<a href="' + esc(it.url) + '" target="_blank" rel="noopener">' + esc(it.title) + "</a></td>" +
        catCell + heatCell + scoreCell +
        "</tr>";
    }).join("");
  }
  function tableHtml(items, opts) {
    var head = "<tr><th>#</th><th>话题</th>";
    if (!opts.category) head += "<th>行业</th>";
    if (!opts.score) head += "<th>热度</th>";
    if (opts.score) head += "<th>评分</th>";
    head += "</tr>";
    return "<table>" + head + rowsHtml(items, opts) + "</table>";
  }

  // ---- 头部 + 横幅 ----
  function renderHeader() {
    var u = DATA.updated_at ? DATA.updated_at.replace("T", " ").slice(0, 16) + " UTC" : "—";
    document.getElementById("meta-updated").textContent = "更新时间：" + u;
    document.getElementById("meta-count").textContent = "已采集 " + DATA.count + " 条";
  }
  function renderBanner() {
    var bad = [];
    Object.keys(DATA.status || {}).forEach(function (k) {
      var v = DATA.status[k];
      if (v.indexOf("fail") === 0) bad.push(k + " 失败");
      else if (v.indexOf("no-key") === 0) bad.push(k + " 未配置");
    });
    var el = document.getElementById("banner");
    if (bad.length) {
      el.style.display = "block";
      el.textContent = "⚠️ 数据延迟提示：部分数据源暂不可用（" + bad.join("、") +
        "）。其余面板正常展示，下一次自动刷新将重试。";
    }
  }

  // ---- 综合热榜 ----
  function renderCombined() {
    var sorted = DATA.items.slice().sort(function (a, b) { return b.score - a.score; }).slice(0, 60);
    var html = sorted.map(function (it, i) {
      return "<tr>" +
        '<td class="rank">' + (i + 1) + "</td>" +
        "<td>" + regionChip(it.region) +
          '<span class="pf">' + esc(it.platform) + "</span>" +
          '<a href="' + esc(it.url) + '" target="_blank" rel="noopener">' + esc(it.title) + "</a>" +
          '<span class="tag">' + esc(it.category) + "</span></td>" +
        '<td class="heat">' + (fmtHeat(it.heat) || it.score) + "</td>" +
        "</tr>";
    }).join("");
    document.getElementById("combined-body").innerHTML =
      "<table><tr><th>#</th><th>话题</th><th>评分</th></tr>" + html + "</table>";
  }

  // ---- 中国 ----
  function renderCn() {
    var groups = groupByPlatform(byRegion("cn"));
    var html = Object.keys(groups).map(function (p) {
      return '<div class="card"><h3>' + esc(p) + "</h3>" +
        tableHtml(groups[p].slice(0, 30), { category: true }) + "</div>";
    }).join("");
    document.getElementById("cn-body").innerHTML = html || '<div class="empty">暂无国内数据。</div>';
  }

  // ---- 全球（带地区筛选）----
  var geoState = "ALL";
  function renderGlobal() {
    var items = byRegion("global");
    var geos = ["ALL", "US", "GB", "JP", "world"];
    var labels = { ALL: "全部", US: "美国", GB: "英国", JP: "日本", world: "其他" };
    var fhtml = geos.map(function (g) {
      return '<button data-geo="' + g + '" class="' + (g === geoState ? "active" : "") + '">' + labels[g] + "</button>";
    }).join("");
    document.getElementById("geo-filter").innerHTML = fhtml;

    var filtered = items.filter(function (i) {
      if (geoState === "ALL") return true;
      if (geoState === "world") return i.sub_region === "world";
      return i.sub_region === geoState;
    });
    var groups = groupByPlatform(filtered);
    var html = Object.keys(groups).map(function (p) {
      return '<div class="card"><h3>' + esc(p) + " · " + esc(labels[geoState]) + "</h3>" +
        tableHtml(groups[p].slice(0, 30), { category: true }) + "</div>";
    }).join("");
    document.getElementById("global-body").innerHTML = html || '<div class="empty">该区域暂无数据。</div>';

    Array.prototype.forEach.call(document.querySelectorAll("#geo-filter button"), function (b) {
      b.addEventListener("click", function () {
        geoState = b.getAttribute("data-geo");
        renderGlobal();
      });
    });
  }

  // ---- 搜索趋势 ----
  function renderSearch() {
    var cn = DATA.items.filter(function (i) { return i.platform === "百度"; });
    var gl = DATA.items.filter(function (i) { return i.platform === "Google Trends"; });
    document.getElementById("search-cn").innerHTML =
      tableHtml(cn.slice(0, 30), { category: true });
    document.getElementById("search-global").innerHTML =
      tableHtml(gl.slice(0, 30), { category: true });
  }

  // ---- 行业排行 ----
  function categoryCounts(region) {
    var cnt = {};
    byRegion(region).forEach(function (i) { cnt[i.category] = (cnt[i.category] || 0) + 1; });
    return cnt;
  }
  function topTopic(region, cat) {
    var list = byRegion(region).filter(function (i) { return i.category === cat; });
    list.sort(function (a, b) { return b.score - a.score; });
    return list[0];
  }
  function renderIndustry() {
    renderDoughnut("chart-cn", categoryCounts("cn"));
    renderDoughnut("chart-global", categoryCounts("global"));
    var cn = categoryCounts("cn"), gl = categoryCounts("global");
    document.getElementById("ind-cn").innerHTML = listHtml("cn", cn);
    document.getElementById("ind-global").innerHTML = listHtml("global", gl);
  }
  function listHtml(region, cnt) {
    var entries = Object.keys(cnt).sort(function (a, b) { return cnt[b] - cnt[a]; });
    return entries.map(function (cat) {
      var t = topTopic(region, cat);
      var title = t ? '<a href="' + esc(t.url) + '" target="_blank" rel="noopener">' + esc(t.title) + "</a>" : "—";
      return "<div style='font-size:13px;padding:4px 0;border-bottom:1px solid var(--border)'>" +
        "<b>" + esc(cat) + "</b> · " + cnt[cat] + " 条 &nbsp; 热门：" + title + "</div>";
    }).join("");
  }
  var charts = {};
  function renderDoughnut(id, cnt) {
    var entries = Object.keys(cnt).sort(function (a, b) { return cnt[b] - cnt[a]; });
    var ctx = document.getElementById(id);
    if (!ctx) return;
    if (charts[id]) charts[id].destroy();
    charts[id] = new Chart(ctx, {
      type: "doughnut",
      data: {
        labels: entries,
        datasets: [{ data: entries.map(function (e) { return cnt[e]; }),
          backgroundColor: entries.map(function (_, i) { return "hsl(" + (i * 37 % 360) + ",70%,60%)"; }) }]
      },
      options: { plugins: { legend: { position: "right", labels: { font: { size: 11 } } } } }
    });
  }

  // ---- 历史趋势 ----
  function renderHistory() {
    fetch("history_index.json").then(function (r) {
      if (!r.ok) throw new Error("no history");
      return r.json();
    }).then(function (hist) {
      var dates = hist.map(function (h) { return h.date; });
      var cnTot = hist.map(function (h) {
        return Object.keys(h.cn).reduce(function (s, k) { return s + h.cn[k]; }, 0);
      });
      var glTot = hist.map(function (h) {
        return Object.keys(h.global).reduce(function (s, k) { return s + h.global[k]; }, 0);
      });
      var ctx = document.getElementById("chart-history");
      if (charts.history) charts.history.destroy();
      charts.history = new Chart(ctx, {
        type: "line",
        data: {
          labels: dates,
          datasets: [
            { label: "国内热门数", data: cnTot, borderColor: "#ef4444", tension: .3, fill: false },
            { label: "全球热门数", data: glTot, borderColor: "#0ea5e9", tension: .3, fill: false }
          ]
        },
        options: { scales: { y: { beginAtZero: true } } }
      });
      var days = hist.length;
      document.getElementById("history-note").textContent =
        "已累积 " + days + " 天数据；每日由 Actions 自动快照。" +
        (days < 3 ? "（运行数天后趋势线才明显）" : "");
    }).catch(function () {
      document.getElementById("history-note").textContent =
        "历史数据暂不可用（本地预览需在站点根目录访问，或等待首次 Actions 运行后产生 history_index.json）。";
    });
  }

  // ---- Tab 切换 ----
  function initTabs() {
    var buttons = document.querySelectorAll("nav.tabs button");
    Array.prototype.forEach.call(buttons, function (b) {
      b.addEventListener("click", function () {
        var tab = b.getAttribute("data-tab");
        Array.prototype.forEach.call(buttons, function (x) { x.classList.remove("active"); });
        b.classList.add("active");
        Array.prototype.forEach.call(document.querySelectorAll(".section"), function (s) {
          s.classList.remove("active");
        });
        document.getElementById("sec-" + tab).classList.add("active");
      });
    });
  }

  function init() {
    renderHeader();
    renderBanner();
    renderCombined();
    renderCn();
    renderGlobal();
    renderSearch();
    renderIndustry();
    renderHistory();
    initTabs();
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
