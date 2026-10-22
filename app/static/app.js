const $ = (s) => document.querySelector(s);
const LEVELS = ["clean", "light", "moderate", "heavy", "cross-script"];
const GCOL = { word: "#2a78d6", char: "#eb6834", subword: "#1baf7a" };
const LABEL_TXT = { scam: "Scam", legit: "Genuine", promo: "Promotion" };

let original = $("#msg").value;
let current = original;
let level = 0;
let seed = 7;
let chart = null;

// ---------- tabs
document.querySelectorAll(".tabs button").forEach((b) =>
  b.addEventListener("click", () => {
    document.querySelectorAll(".tabs button").forEach((x) => x.setAttribute("aria-selected", x === b));
    document.querySelectorAll(".tab-panel").forEach((p) => (p.hidden = p.id !== b.dataset.tab));
    if (b.dataset.tab === "results") loadResults();
  })
);

async function api(path, body) {
  const r = await fetch(path, body ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) } : {});
  if (!r.ok) throw new Error((await r.text()) || r.statusText);
  return r.json();
}

// ---------- bubble rendering with obfuscation highlights
const ZW = /[​‌‍⁠﻿]/;
const isHomo = (c) => /[Ͱ-ϿЀ-ӿ]/.test(c);
const isScript = (c) => /[ऀ-౿]/.test(c);
function esc(s) { return s.replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c])); }

function renderBubble(text) {
  const out = [];
  for (const tok of text.split(/(\s+)/)) {
    const protectedTok = /[\/:]|@[a-z]+$|\.[a-z]{2,}|^(rs|inr|₹)/i.test(tok) || /^\W*\d[\d,.\-\/]*\W*$/.test(tok);
    const leetTok = level > 0 && !protectedTok && /[a-z]/i.test(tok) && /[@$!0-9]/.test(tok);
    let html = "";
    for (const ch of tok) {
      if (ZW.test(ch)) html += '<span class="zw" title="invisible character"></span>';
      else if (isHomo(ch)) html += `<span class="homo" title="look-alike letter U+${ch.codePointAt(0).toString(16).toUpperCase()}">${esc(ch)}</span>`;
      else if (isScript(ch)) html += `<span class="script">${esc(ch)}</span>`;
      else if (leetTok && /[@$!0-9]/.test(ch)) html += `<span class="leet">${esc(ch)}</span>`;
      else html += esc(ch);
    }
    out.push(html);
  }
  $("#bubble").innerHTML = out.join("");
}

async function refreshObfuscation() {
  $("#level-name").textContent = `L${level} · ${LEVELS[level]}`;
  if (level === 0) {
    current = original;
  } else {
    try {
      const r = await api("/api/obfuscate", { text: original, level, seed });
      current = r.text;
    } catch (e) { current = original; }
  }
  renderBubble(current);
}

let debounce;
$("#msg").addEventListener("input", (e) => {
  original = e.target.value;
  clearTimeout(debounce);
  debounce = setTimeout(refreshObfuscation, 250);
});
$("#level").addEventListener("input", (e) => { level = +e.target.value; refreshObfuscation(); });
$("#reshuffle").addEventListener("click", () => { seed = Math.floor(Math.random() * 1e6); refreshObfuscation(); });

document.querySelectorAll("[data-sample]").forEach((b) =>
  b.addEventListener("click", async () => {
    const lang = $("#sample-lang").value;
    const s = await api(`/api/samples?n=1&label=${b.dataset.sample}${lang ? "&lang=" + lang : ""}`);
    if (!s.length) return;
    original = s[0].text;
    $("#msg").value = original;
    await refreshObfuscation();
    classify();
  })
);

// ---------- classification
async function classify() {
  const btn = $("#analyze");
  btn.disabled = true;
  btn.textContent = "Classifying…";
  try {
    const r = await api("/api/predict", { text: current, normalize: $("#norm").checked });
    $("#lang-tag").textContent = `Detected: ${r.lang_name}`;
    const e = r.ensemble;
    const box = $("#ensemble");
    box.className = `ensemble is-${e.prediction}`;
    box.innerHTML = `<div class="big">${LABEL_TXT[e.prediction]}</div>
      <small>${e.scam_votes} of ${e.n_models} models flag this as a scam · average scam probability ${(e.probs.scam * 100).toFixed(0)}%</small>
      ${r.normalized_text ? `<small style="display:block;margin-top:6px">Canonicalised: <i>${esc(r.normalized_text)}</i></small>` : ""}`;
    $("#model-rows").innerHTML = r.results
      .map((m) => {
        const p = m.probs;
        return `<div class="row">
          <div class="name">${m.label}<small>${m.granularity}-level · ${m.latency_ms} ms</small></div>
          <div class="bar" title="genuine ${(p.legit * 100).toFixed(1)}% · promo ${(p.promo * 100).toFixed(1)}% · scam ${(p.scam * 100).toFixed(1)}%">
            <span class="legit" style="width:${p.legit * 100}%"></span><span class="promo" style="width:${p.promo * 100}%"></span><span class="scam" style="width:${p.scam * 100}%"></span>
          </div>
          <div class="verdict c-${m.prediction}">${LABEL_TXT[m.prediction]}</div>
        </div>`;
      })
      .join("");
  } catch (err) {
    $("#ensemble").className = "ensemble";
    $("#ensemble").textContent = `Could not classify: ${err.message}. Check that the server has trained models in artifacts/.`;
  } finally {
    btn.disabled = false;
    btn.textContent = "Classify message";
  }
}
$("#analyze").addEventListener("click", classify);

// ---------- stress test chart
async function runStress() {
  const btn = $("#run-stress");
  btn.disabled = true;
  btn.textContent = "Running…";
  try {
    const r = await api("/api/stress", { text: original, seed });
    const ink2 = getComputedStyle(document.documentElement).getPropertyValue("--ink-2").trim();
    const line = getComputedStyle(document.documentElement).getPropertyValue("--line").trim();
    const datasets = r.models.map((m) => ({
      label: m.label,
      data: r.levels.map((l) => l.scam_prob[m.key]),
      borderColor: GCOL[m.granularity],
      backgroundColor: GCOL[m.granularity],
      borderDash: m.regime === "adv" ? [5, 4] : [],
      borderWidth: 2,
      pointRadius: 4,
      tension: 0.15,
    }));
    if (chart) chart.destroy();
    chart = new Chart($("#stress-chart"), {
      type: "line",
      data: { labels: r.levels.map((l) => `L${l.level} ${l.name}`), datasets },
      options: {
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        scales: {
          y: { min: 0, max: 1, title: { display: true, text: "P(scam)", color: ink2 }, grid: { color: line }, ticks: { color: ink2 } },
          x: { grid: { display: false }, ticks: { color: ink2 } },
        },
        plugins: {
          legend: { position: window.innerWidth < 700 ? "bottom" : "right", labels: { color: ink2, usePointStyle: true, pointStyle: "line", boxWidth: 22, font: { size: 11 } } },
          tooltip: { callbacks: { label: (c) => `${c.dataset.label}: ${(c.parsed.y * 100).toFixed(1)}%` } },
        },
      },
      plugins: [{
        id: "threshold",
        afterDraw(c) {
          const y = c.scales.y.getPixelForValue(0.5);
          const ctx = c.ctx;
          ctx.save(); ctx.strokeStyle = "#c8312b"; ctx.setLineDash([3, 3]); ctx.lineWidth = 1;
          ctx.beginPath(); ctx.moveTo(c.chartArea.left, y); ctx.lineTo(c.chartArea.right, y); ctx.stroke(); ctx.restore();
        },
      }],
    });
  } catch (err) {
    alert("Stress test failed: " + err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = "Run L0 → L4 on this message";
  }
}
$("#run-stress").addEventListener("click", runStress);

// ---------- results tab
const FIG_CAPTIONS = {
  fig1_f1_vs_obfuscation: "Macro-F1 as obfuscation gets heavier. Blue = word-level, orange = character-level, green = subword transformers.",
  fig2_fnr_vs_obfuscation: "Scam false-negative rate — the share of scams that get through.",
  fig3_ece_vs_obfuscation: "Calibration error: how far confidence drifts from accuracy under attack.",
  fig4_adversarial_training_gain: "Gain from adversarial training per level. L4 script-mixing was never seen in training.",
  fig5_crosslingual_transfer: "Train on one language pair (rows), test on each (columns).",
  fig6_latency_vs_robustness: "Robustness against single-message CPU latency.",
};
const TABLES = [
  ["table1_clean", "Clean test performance"],
  ["table2_f1_vs_level_targeted", "Macro-F1 by obfuscation level (scam-only attack)"],
  ["table3_fnr_vs_level_targeted", "Scam false-negative rate by level"],
  ["table5_hypothesis_tests", "Do character-level models degrade less? (paired bootstrap)"],
  ["table6_adversarial_training", "Adversarial training"],
  ["table7_normalisation_defence", "Canonicalisation defence"],
  ["table9_crosslingual", "Cross-lingual transfer"],
  ["table10_latency", "Latency"],
];
let resultsLoaded = false;
async function loadResults() {
  if (resultsLoaded) return;
  const r = await api("/api/results");
  const body = $("#results-body");
  const ds = r.dataset_stats;
  let html = "";
  if (ds) {
    html += `<div class="res-section"><h2>Dataset</h2><p class="hint">Synthetic, template-disjoint corpus of UPI-related SMS in five language settings. Test messages use phrasings never seen in training.</p>
      <div class="stat-line"><span><b>${ds.n_total.toLocaleString()}</b>messages</span><span><b>5</b>language settings</span>
      <span><b>${ds.by_label.scam.toLocaleString()}</b>scams</span><span><b>${ds.by_label.legit.toLocaleString()}</b>genuine</span>
      <span><b>${ds.by_label.promo.toLocaleString()}</b>promotions</span><span><b>${(ds.mixed_script_share * 100).toFixed(1)}%</b>mixed-script</span></div></div>`;
  }
  for (const f of r.figures) {
    const k = f.replace(".png", "");
    html += `<div class="res-section"><h2>${FIG_CAPTIONS[k] ? FIG_CAPTIONS[k].split(".")[0] : k}</h2>
      <p class="hint">${FIG_CAPTIONS[k] || ""}</p><img src="/figures/${f}" alt="${k}" loading="lazy"></div>`;
  }
  for (const [k, title] of TABLES) {
    const t = r.tables[k];
    if (!t) continue;
    html += `<div class="res-section"><h2>${title}</h2><div class="table-scroll"><table><thead><tr>${t.columns.map((c) => `<th>${esc(c)}</th>`).join("")}</tr></thead>
      <tbody>${t.data.map((row) => `<tr>${row.map((v) => `<td>${esc(String(v))}</td>`).join("")}</tr>`).join("")}</tbody></table></div></div>`;
  }
  body.innerHTML = html || '<p class="hint">No results yet. Run <code>bash scripts/run_all.sh</code> to produce them.</p>';
  resultsLoaded = true;
}

refreshObfuscation();
