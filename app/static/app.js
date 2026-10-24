const $ = (s) => document.querySelector(s);
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const LEVELS = ["clean", "light", "moderate", "heavy", "cross-script"];
const WORD = { scam: "Likely scam", promo: "Promotion", legit: "Looks genuine" };
const ADVICE = {
  scam: "Don't reply, don't open the link, and never enter your UPI PIN to receive money.",
  promo: "An advertisement. Safe to ignore.",
  legit: "No scam pattern found. Even so, never share your PIN or OTP with anyone.",
};
const SAMPLES = {
  "ta-scam": "உங்கள் SBI account இன்று இரவு 12 மணிக்கு block செய்யப்படும். உடனே KYC update செய்ய இந்த link-ஐ click செய்யவும் http://sbi-kyc-update.xyz/a9",
  pin: "Congratulations! You have received ₹4,999 cashback. To receive the money accept the request on PhonePe and enter your UPI PIN",
  disguised: "Y0ur HDFC acc0unt will be bl0cked t0day. Upd@te K.Y.C n0w: kyc.verify-hdfc.top/k",
  romanised: "Ungal refund ₹2,000 pending. Udane collect request approve panni PIN podunga",
  genuine: "உங்கள் A/c XX4821-லிருந்து 12-10-26 அன்று ₹1,250 VPA swiggy@ybl-க்கு debit செய்யப்பட்டது. UPI Ref 412398765432. நீங்கள் செய்யவில்லையா? 1800-123-4567 அழைக்கவும் -SBI",
  promo: "Swiggy Diwali sale is live! Up to 60% off on all orders. Shop now https://swiggy.onelink.me/x7",
};

async function api(path, body) {
  const r = await fetch(path, body ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) } : {});
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(j.detail || r.statusText);
  return j;
}

// ---------------------------------------------------------------- tabs
const loaded = {};
document.querySelectorAll(".tabs button").forEach((b) =>
  b.addEventListener("click", () => {
    document.querySelectorAll(".tabs button").forEach((x) => x.setAttribute("aria-selected", x === b));
    document.querySelectorAll(".panel").forEach((p) => (p.hidden = p.id !== b.dataset.tab));
    if (b.dataset.tab === "results" && !loaded.results) loadResults();
    if (b.dataset.tab === "network" && !loaded.network) loadNetwork();
    if (b.dataset.tab === "lab" && !loaded.lab) { loaded.lab = true; refreshLab(); }
  })
);

// ---------------------------------------------------------------- check
function bar(p) {
  return `<div class="bar"><span class="legit" style="width:${p.legit * 100}%"></span><span class="promo" style="width:${p.promo * 100}%"></span><span class="scam" style="width:${p.scam * 100}%"></span></div>
    <div class="bar-labels"><span class="c-legit">Genuine ${Math.round(p.legit * 100)}%</span><span class="c-promo">Promotion ${Math.round(p.promo * 100)}%</span><span class="c-scam">Scam ${Math.round(p.scam * 100)}%</span></div>`;
}

function renderAnalysis(r) {
  const v = $("#verdict");
  v.className = `verdict ${r.label}`;
  v.innerHTML = `<div class="word">${WORD[r.label]}</div><p class="advice">${ADVICE[r.label]}</p>${bar(r.probs)}
    <div class="meta" style="margin-top:10px"><span>Language: <b>${esc(r.language.name)}</b> (detected)</span><span>${r.total_ms.toFixed(1)} ms</span></div>`;

  const reasons = [...(r.cues || []).map((c) => c.text)];
  r.links.filter((l) => l.risk >= 0.5).forEach((l) => reasons.push(`Contains a dangerous link (${l.host}), details below.`));
  let html = "";
  if (reasons.length) html += `<div class="block"><h3>Why</h3><ul class="reasons">${reasons.map((x) => `<li>${esc(x)}</li>`).join("")}</ul></div>`;
  else if (r.label === "legit") html += `<div class="block"><h3>Why</h3><ul class="reasons"><li class="ok">No pressure tactics, no requests for PIN/OTP, no suspicious links.</li></ul></div>`;

  const maxAbs = Math.max(1e-6, ...r.highlights.map((h) => Math.abs(h.score)));
  html += `<div class="block"><h3>The message, as the model read it</h3><div class="read">${r.highlights.map((h) => {
    const s = h.score / maxAbs;
    const bg = s > 0.15 ? `background:color-mix(in srgb, var(--scam) ${Math.round(10 + 32 * s)}%, transparent)` : s < -0.15 ? `background:color-mix(in srgb, var(--legit) ${Math.round(8 + 22 * -s)}%, transparent)` : "";
    return `<span style="${bg}" title="${h.score > 0 ? "pushes towards scam" : "pushes towards genuine"} (${h.score.toFixed(2)})">${esc(h.token)}</span>`;
  }).join(" ")}</div><p class="hint">Red words push the model towards “scam”, green words towards “genuine”.</p></div>`;

  html += `<div class="block"><h3>Language, word by word · code-mixing index ${Math.round(r.language.cmi)}</h3><div class="tokens">${r.language.tokens.map(([t, tag]) => `<span class="tok ${tag}">${esc(t)}</span>`).join("")}</div>
    <div class="langline"><span><i style="background:var(--english)"></i>English</span><span><i style="background:var(--tamil)"></i>Tamil</span><span><i style="background:var(--mixtok)"></i>both in one word (link-ஐ)</span><span><i style="background:var(--ink-3)"></i>numbers, links, IDs</span></div></div>`;

  if (r.links.length) {
    html += `<div class="block"><h3>Links in the message</h3>${r.links.map((l) => {
      const d = l.dns;
      let dnsLine = "";
      if (d && !d.error) dnsLine = d.rcode === "NXDOMAIN" ? "DNS: NXDOMAIN (no such domain)" : `DNS: ${(d.addresses || []).join(", ") || "no A record"}${d.cname_chain && d.cname_chain.length ? " via " + d.cname_chain.join(" → ") : ""} · TTL ${d.min_ttl}s · ${d.cached ? "cached" : d.elapsed_ms + " ms"}`;
      return `<div class="link"><span class="risk ${l.risk >= 0.5 ? "c-scam" : ""}">risk ${Math.round(l.risk * 100)}%</span><div class="host">${esc(l.host)}</div>${dnsLine ? `<div class="dnsline">${esc(dnsLine)}</div>` : ""}${l.reasons.length ? `<ul class="reasons">${l.reasons.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>` : `<div class="hint">Nothing suspicious about this link.</div>`}</div>`;
    }).join("")}</div>`;
  }
  html += `<p class="foot">Model ${r.model_ms.toFixed(2)} ms · canonicalised: <span class="mono">${esc(r.normalized)}</span></p>`;
  $("#details").innerHTML = html;
}

async function analyze() {
  const text = $("#msg").value.trim();
  if (!text) return;
  const b = $("#analyze");
  b.disabled = true; b.textContent = "Checking…";
  try { renderAnalysis(await api("/api/analyze", { text, dns: $("#dns").checked })); }
  catch (e) { $("#verdict").className = "verdict"; $("#verdict").textContent = `Could not check the message: ${e.message}`; }
  finally { b.disabled = false; b.textContent = "Check message"; }
}
$("#analyze").addEventListener("click", analyze);
$("#msg").addEventListener("keydown", (e) => { if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) analyze(); });
document.querySelectorAll("[data-sample]").forEach((b) => b.addEventListener("click", () => { $("#msg").value = SAMPLES[b.dataset.sample]; analyze(); }));
document.querySelector("[data-random]").addEventListener("click", async () => {
  const s = await api(`/api/samples?label=${["scam", "legit", "promo"][Math.floor(Math.random() * 3)]}&lang=${Math.random() < 0.5 ? "ta" : "en"}`);
  $("#msg").value = s[0].text; analyze();
});

// ---------------------------------------------------------------- lab
let level = 0, seed = 7, labText = "", chart = null;
const isHomo = (c) => /[Ͱ-ϿЀ-ӿ]/.test(c);
const isTamil = (c) => /[஀-௿]/.test(c);
const ZW = /[​‌‍⁠﻿]/;

function renderBubble(text, original) {
  const origTamil = new Set(original.split(/\s+/).filter((t) => [...t].some(isTamil)));
  const origLatin = new Set(original.split(/\s+/));
  $("#bubble").innerHTML = text.split(/(\s+)/).map((tok) => {
    if (/^\s+$/.test(tok)) return tok;
    const hasTa = [...tok].some(isTamil);
    const switched = level > 0 && ((hasTa && !origTamil.has(tok) && /[஀-௿]{3,}/.test(tok) && !original.includes(tok)) ||
      (!hasTa && /^[a-z]{3,}$/i.test(tok.replace(/[.,!?]/g, "")) && !origLatin.has(tok) && original.split(/\s+/).some((o) => [...o].some(isTamil)) && level === 4));
    let h = "";
    const leetTok = level > 0 && /[a-z]/i.test(tok) && /[@$!0-9]/.test(tok) && !/[\/:]|@[a-z]+$|^(rs|inr|₹)/i.test(tok) && !/^\W*\d[\d,.\-\/]*\W*$/.test(tok);
    for (const ch of tok) {
      if (ZW.test(ch)) h += '<span class="zw" title="invisible character"></span>';
      else if (isHomo(ch)) h += `<span class="homo" title="look-alike letter U+${ch.codePointAt(0).toString(16).toUpperCase()}">${esc(ch)}</span>`;
      else if (/[௦-௲]/.test(ch)) h += `<span class="homo" title="Tamil digit used as a letter">${esc(ch)}</span>`;
      else if (leetTok && /[@$!0-9]/.test(ch)) h += `<span class="leet">${esc(ch)}</span>`;
      else h += esc(ch);
    }
    return switched ? `<span class="script">${h}</span>` : h;
  }).join("");
}

async function refreshLab() {
  labText = $("#lab-msg").value;
  $("#level-name").textContent = `L${level} · ${LEVELS[level]}`;
  const r = await api("/api/obfuscate", { text: labText, level, seed });
  renderBubble(r.text, labText);
  $("#bubble").dataset.text = r.text;
  $("#normalized").textContent = r.normalized;
  $("#lab-verdict").textContent = "";
}
let deb;
$("#lab-msg").addEventListener("input", () => { clearTimeout(deb); deb = setTimeout(refreshLab, 250); });
$("#level").addEventListener("input", (e) => { level = +e.target.value; refreshLab(); });
$("#reshuffle").addEventListener("click", () => { seed = Math.floor(Math.random() * 1e6); refreshLab(); });
$("#lab-check").addEventListener("click", async () => {
  const r = await api("/api/analyze", { text: $("#bubble").dataset.text || labText, dns: false });
  $("#lab-verdict").innerHTML = `ScamShield says <b class="c-${r.label}">${WORD[r.label]}</b> (scam ${Math.round(r.probs.scam * 100)}%).`;
});

const GCOL = { word: "#2a78d6", char: "#eb6834", subword: "#1baf7a", production: "#13213a" };
$("#stress").addEventListener("click", async () => {
  const b = $("#stress");
  b.disabled = true; b.textContent = "Running…";
  try {
    const r = await api("/api/stress", { text: $("#lab-msg").value, seed });
    const css = getComputedStyle(document.documentElement);
    const ink2 = css.getPropertyValue("--ink-2").trim(), line = css.getPropertyValue("--line").trim(), ink = css.getPropertyValue("--ink").trim();
    const ds = r.models.map((m) => ({
      label: m.label, data: r.levels.map((l) => l.scam_prob[m.key]),
      borderColor: m.key === "production" ? ink : GCOL[m.granularity], backgroundColor: m.key === "production" ? ink : GCOL[m.granularity],
      borderDash: m.regime === "adv" ? [5, 4] : [], borderWidth: m.key === "production" ? 3.5 : 2, pointRadius: 4, tension: 0.15,
    }));
    if (chart) chart.destroy();
    chart = new Chart($("#stress-chart"), {
      type: "line", data: { labels: r.levels.map((l) => `L${l.level} ${l.name}`), datasets: ds },
      options: {
        maintainAspectRatio: false, interaction: { mode: "index", intersect: false },
        scales: { y: { min: 0, max: 1, title: { display: true, text: "P(scam)", color: ink2 }, grid: { color: line }, ticks: { color: ink2 } },
                  x: { grid: { display: false }, ticks: { color: ink2 } } },
        plugins: { legend: { position: window.innerWidth < 760 ? "bottom" : "right", labels: { color: ink2, usePointStyle: true, pointStyle: "line", boxWidth: 22, font: { size: 11 } } },
                   tooltip: { callbacks: { label: (c) => `${c.dataset.label}: ${(c.parsed.y * 100).toFixed(1)}%` } } },
      },
      plugins: [{ id: "thr", afterDraw(c) { const y = c.scales.y.getPixelForValue(0.5), x = c.ctx; x.save(); x.strokeStyle = "#c62828"; x.setLineDash([3, 3]);
        x.beginPath(); x.moveTo(c.chartArea.left, y); x.lineTo(c.chartArea.right, y); x.stroke(); x.restore(); } }],
    });
  } catch (e) { alert("Could not run: " + e.message); }
  finally { b.disabled = false; b.textContent = "Run levels 0 to 4"; }
});

// ---------------------------------------------------------------- network
async function loadNetwork() {
  loaded.network = true;
  try {
    const s = await api("/api/net/status");
    $("#p-tcp").textContent = s.tcp_port; $("#p-tcp2").textContent = s.tcp_port; $("#p-dns").textContent = s.dns_port;
    const c = s.counters;
    $("#status-line").innerHTML = `Running: SSP on TCP ${s.tcp_port} and UDP ${s.udp_port}, DNS on ${s.dns_port}. Served ${c.tcp_frames} TCP frames, ${c.udp_frames} UDP datagrams; ${c.corrupted} corrupted frames dropped.` + (s.errors.length ? ` <span class="bad-msg">${esc(s.errors.join("; "))}</span>` : "");
    $("#ips").textContent = s.local_ips.length ? s.local_ips.map((ip) => `${ip}:${s.tcp_port}`).join("   ") : "No network interface found";
  } catch (e) { $("#status-line").textContent = "Could not read service status."; }
  buildFrame();
  dnsLookup();
  cidrCalc();
}

async function buildFrame(flip) {
  const r = await api("/api/net/frame", { text: $("#frame-text").value, flip_bit: flip ?? null });
  const bytes = r.hex.split(" ");
  const n = bytes.length;
  const flipped = r.flip ? r.flip.byte : -1;
  const hex = bytes.map((b, i) => `<span class="${i === flipped ? "x" : i < 16 ? "h" : i >= n - 4 ? "c" : ""}">${b}</span>`).join(" ");
  let html = `<table><tr><th>Field</th><th>Bytes</th><th>Value</th></tr>${r.fields.map((f) => `<tr><td>${f.name}</td><td>${f.bytes}</td><td class="mono">${esc(f.value)}</td></tr>`).join("")}</table>
    <div class="hex">${hex}</div><p class="hint">${r.length} bytes: <span style="color:var(--accent)">header</span>, payload, <span style="color:var(--legit)">CRC-32</span>.</p>`;
  if (r.flip) html += `<p>Flipped bit ${r.flip.bit} (byte ${r.flip.byte}). The receiver recomputes CRC-32 = <span class="mono">${r.flip.crc32_recomputed}</span> but the frame says <span class="mono">${r.flip.crc32_received}</span>, so it is <b class="${r.flip.receiver.startsWith("rejected") ? "ok-msg" : "bad-msg"}">${esc(r.flip.receiver)}</b>. A parity bit would ${r.flip.parity_detects ? "also" : "<b>not</b>"} catch this; the Internet checksum would ${r.flip.checksum_detects ? "also" : "<b>not</b>"}.</p>`;
  $("#frame-out").innerHTML = html;
}
$("#frame-build").addEventListener("click", () => buildFrame());
$("#frame-flip").addEventListener("click", () => buildFrame(Math.floor(Math.random() * 100000)));

async function dnsLookup() {
  try {
    const r = await api("/api/net/dns", { name: $("#dns-name").value, type: $("#dns-type").value });
    const rows = r.answers.map((a) => `<tr><td class="mono">${esc(a.name)}</td><td>${a.type}</td><td>${a.ttl}</td><td class="mono">${esc(String(a.data).slice(0, 80))}</td></tr>`).join("");
    const cls = (r.classification || []).map((c) => c.special ? `<li>${esc(c.ip)} is a <b>${esc(c.special)}</b> address (matches ${esc(c.matched_prefix)})</li>` : `<li>${esc(c.ip)} is a public address</li>`).join("");
    $("#dns-out").innerHTML = `<p><b class="${r.rcode === "NOERROR" ? "ok-msg" : "bad-msg"}">${r.rcode}</b> from ${esc(r.server)} in ${r.cached ? "cache" : r.elapsed_ms + " ms"}${r.truncated_over_udp ? " · answer was too big for UDP (TC bit), so it was re-asked over TCP" : ""}</p>
      ${rows ? `<table><tr><th>Name</th><th>Type</th><th>TTL</th><th>Data</th></tr>${rows}</table>` : ""}${cls ? `<ul class="reasons">${cls}</ul>` : ""}
      <div class="hex"><span class="h">${r.query_hex.split(" ").slice(0, 12).join(" ")}</span> ${r.query_hex.split(" ").slice(12).join(" ")}</div><p class="hint">The query as sent on the wire: <span style="color:var(--accent)">12-byte DNS header</span>, then the question.</p>`;
  } catch (e) { $("#dns-out").innerHTML = `<p class="bad-msg">${esc(e.message)}</p>`; }
}
$("#dns-go").addEventListener("click", dnsLookup);
document.querySelectorAll("[data-dns]").forEach((b) => b.addEventListener("click", () => { $("#dns-name").value = b.dataset.dns; $("#dns-type").value = b.dataset.type || "A"; dnsLookup(); }));

async function cidrCalc() {
  try {
    const r = await api("/api/net/cidr", { value: $("#cidr").value });
    const rows = Object.entries(r).filter(([k]) => !["kind", "special"].includes(k)).map(([k, v]) => `<tr><td>${k.replace(/_/g, " ")}</td><td class="mono">${esc(Array.isArray(v) ? v.join(", ") : v ?? "")}</td></tr>`).join("");
    const sp = r.special ? (r.special.special ? `Special-purpose range: ${r.special.special}` : "Public address space") : "";
    $("#cidr-out").innerHTML = `<table>${rows}</table>${sp ? `<p class="hint">${esc(sp)}</p>` : ""}`;
  } catch (e) { $("#cidr-out").innerHTML = `<p class="bad-msg">${esc(e.message)}</p>`; }
}
$("#cidr-go").addEventListener("click", cidrCalc);

// ---------------------------------------------------------------- results
const FIGS = {
  fig1_f1_vs_obfuscation: ["Accuracy as messages are disguised", "Macro-F1 from L0 (clean) to L4 (cross-script). Blue = word models, orange = character models, green = multilingual transformers."],
  fig2_fnr_vs_obfuscation: ["Scams that get through", "Left: share of scams missed as scam messages are disguised. Right: genuine messages wrongly flagged when every message is disguised."],
  fig3_ece_vs_obfuscation: ["Confidence vs accuracy", "Expected calibration error: how far a model's confidence drifts from how often it is right."],
  fig4_adversarial_training_gain: ["Training on disguised messages", "Gain in macro-F1 from adversarial training. L4 is cross-script, a family never seen in training."],
  fig5_crosslingual_transfer: ["English ↔ Tamil–English transfer", "Train on one language setting (rows), test on each (columns)."],
  fig6_latency_vs_robustness: ["Robustness vs speed", "Average macro-F1 across disguise levels against CPU time per message."],
  fig7_error_detection: ["Which frame checks catch burst errors", "Share of corrupted SSP frames that each check fails to detect."],
  fig8_arq_loss: ["Reliable delivery over a lossy link", "Stop-and-Wait vs Go-Back-N vs Selective Repeat as packet loss grows."],
  fig9_window_sweep: ["Why sliding windows matter", "Goodput as the window grows, at 2% loss and 20 ms round trip."],
  fig10_aimd_cwnd: ["Congestion control in action", "The AIMD congestion window probing a 400 packets/s bottleneck."],
};
const TABLES = [
  ["table12_production", "The production detector (web app and phone)"],
  ["table1_clean", "All models on clean messages"],
  ["table2_f1_vs_level_targeted", "Macro-F1 by disguise level (scam messages disguised)"],
  ["table3_fnr_vs_level_targeted", "Scams missed by disguise level"],
  ["table5_hypothesis_tests", "Do character models hold up better? (paired bootstrap)"],
  ["table6_adversarial_training", "Adversarial training"],
  ["table7_normalisation_defence", "Clean-up (canonicalisation) defence"],
  ["table8_per_language", "English vs Tamil–English"],
  ["table13_external", "Real public SMS datasets"],
  ["table14_link_fusion", "Adding link intelligence"],
  ["net1_error_detection", "Error detection codes"],
  ["net2_arq_loss", "ARQ protocols under loss"],
  ["net4_congestion", "Congestion control"],
  ["net5_tcp_vs_udp", "TCP vs UDP"],
  ["net6_dns_loss", "DNS retries over a lossy link"],
  ["table10_latency", "Latency per model"],
];
function tableHtml(t) {
  return `<div class="table-scroll"><table><thead><tr>${t.columns.map((c) => `<th>${esc(c)}</th>`).join("")}</tr></thead><tbody>${t.data.map((row) => `<tr>${row.map((v) => `<td>${esc(v)}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
}
async function loadResults() {
  loaded.results = true;
  const r = await api("/api/results");
  const ds = r.dataset_stats;
  let html = "";
  if (ds) {
    const cm = ds.code_mixing || {};
    html += `<div class="res-section"><h2>Dataset: UPI-BiSMS</h2><p class="hint">Bilingual UPI SMS corpus. Test messages use phrasings never seen in training.</p>
      <div class="stat-line"><span><b>${ds.n_total.toLocaleString()}</b>messages</span><span><b>${ds.by_label.scam.toLocaleString()}</b>scams</span><span><b>${ds.by_label.legit.toLocaleString()}</b>genuine</span><span><b>${ds.by_label.promo.toLocaleString()}</b>promotions</span>
      ${cm.ta ? `<span><b>${Math.round(cm.ta.tamil_token_share * 100)}%</b>Tamil words in Tamil–English messages</span><span><b>${cm.ta.mean_cmi.toFixed(0)}</b>code-mixing index</span>` : ""}</div></div>`;
  }
  const order = Object.keys(FIGS).map((k) => k + ".png").filter((f) => r.figures.includes(f));
  for (const f of order.concat(r.figures.filter((f) => !order.includes(f)))) {
    const k = f.replace(".png", "");
    const [title, cap] = FIGS[k] || [k, ""];
    html += `<div class="res-section"><h2>${esc(title)}</h2><p class="hint">${esc(cap)}</p><img src="/figures/${f}" alt="${esc(title)}" loading="lazy"></div>`;
  }
  for (const [k, title] of TABLES) if (r.tables[k]) html += `<div class="res-section"><h2>${esc(title)}</h2>${tableHtml(r.tables[k])}</div>`;
  $("#results-body").innerHTML = html || '<p class="hint">No results yet. Run <code>bash scripts/run_all.sh</code>.</p>';
}

analyze();
