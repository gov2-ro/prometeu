/* Chart.js editorial theme — paper-and-ink, Plex Sans, tabular numerals.
 * Include AFTER chart.umd.min.js. Safe to include on pages without Chart.js.
 */
(function () {
  if (typeof window === "undefined" || typeof window.Chart === "undefined") return;
  var css = getComputedStyle(document.documentElement);
  function v(name, fallback) {
    var val = css.getPropertyValue(name).trim();
    return val || fallback;
  }
  var ink       = v("--ink",       "#1a1a1a");
  var inkSoft   = v("--ink-soft",  "#55524b");
  var inkSofter = v("--ink-softer","#888377");
  var rule      = v("--rule",      "#d9d5c8");
  var paper     = v("--paper",     "#faf8f2");

  window.PR_PALETTE = [
    v("--c-1","#1e5b6b"), v("--c-2","#b45c39"), v("--c-3","#5d6b8a"),
    v("--c-4","#b09240"), v("--c-5","#7b4e7a"), v("--c-6","#4a7c4e"),
  ];
  window.PR_ACCENT = v("--accent", "#1e5b6b");
  window.PR_INK    = ink;
  window.PR_RULE   = rule;
  window.PR_PAPER  = paper;
  window.PR_GOOD   = v("--good","#4a7c4e");
  window.PR_WARN   = v("--warn","#b09240");
  window.PR_BAD    = v("--bad", "#a8323a");

  var C = window.Chart;
  C.defaults.color = ink;
  C.defaults.borderColor = rule;
  C.defaults.font.family = '"IBM Plex Sans", ui-sans-serif, system-ui, sans-serif';
  C.defaults.font.size = 13;
  C.defaults.font.weight = 400;
  C.defaults.animation = false;
  C.defaults.responsive = true;
  C.defaults.maintainAspectRatio = false;

  C.defaults.plugins.legend.position = "bottom";
  C.defaults.plugins.legend.labels.boxWidth = 10;
  C.defaults.plugins.legend.labels.boxHeight = 10;
  C.defaults.plugins.legend.labels.color = inkSoft;
  C.defaults.plugins.legend.labels.padding = 14;
  C.defaults.plugins.legend.labels.font = { size: 12, family: C.defaults.font.family };

  C.defaults.plugins.tooltip.backgroundColor = paper;
  C.defaults.plugins.tooltip.titleColor = ink;
  C.defaults.plugins.tooltip.bodyColor = ink;
  C.defaults.plugins.tooltip.borderColor = rule;
  C.defaults.plugins.tooltip.borderWidth = 1;
  C.defaults.plugins.tooltip.cornerRadius = 0;
  C.defaults.plugins.tooltip.padding = 10;
  C.defaults.plugins.tooltip.titleFont = { size: 12, weight: 600, family: C.defaults.font.family };
  C.defaults.plugins.tooltip.bodyFont  = { size: 12, family: '"IBM Plex Mono", ui-monospace, monospace' };
  C.defaults.plugins.tooltip.displayColors = true;
  C.defaults.plugins.tooltip.boxPadding = 4;

  if (C.defaults.scales && C.defaults.scales.linear) {
    C.defaults.scales.linear.grid   = { color: "rgba(26,26,26,0.06)", drawBorder: false, drawTicks: false };
    C.defaults.scales.linear.border = { display: false };
    C.defaults.scales.linear.ticks  = { color: inkSoft, padding: 8, font: { size: 11 } };
  }
  if (C.defaults.scales && C.defaults.scales.category) {
    C.defaults.scales.category.grid   = { display: false, drawBorder: false };
    C.defaults.scales.category.border = { display: false };
    C.defaults.scales.category.ticks  = { color: inkSoft, padding: 8, font: { size: 11 } };
  }

  C.defaults.datasets = C.defaults.datasets || {};
  var bar  = C.defaults.datasets.bar  = C.defaults.datasets.bar  || {};
  var line = C.defaults.datasets.line = C.defaults.datasets.line || {};
  bar.borderRadius = 0;
  bar.borderSkipped = false;
  bar.barPercentage = 0.78;
  bar.categoryPercentage = 0.78;
  line.borderWidth = 2;
  line.pointRadius = 0;
  line.pointHoverRadius = 4;
  line.tension = 0.25;
})();
