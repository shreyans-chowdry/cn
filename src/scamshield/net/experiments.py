"""
Computer-networks experiments on the ScamShield protocol stack (all on real sockets, localhost,
with the impaired-link emulator; deterministic seeds).

  N1  error detection: parity vs Internet checksum vs CRC-16 vs CRC-32 on SSP frames, random
      multi-bit errors and burst errors; Hamming(7,4) single-error correction       (Module 3, Lab 2)
  N2  Stop-and-Wait vs Go-Back-N vs Selective Repeat under increasing packet loss    (Lab 3, Lab 8)
  N3  sliding-window size sweep: goodput vs window (bandwidth-delay product)          (Lab 3)
  N4  congestion: fixed windows vs AIMD through a bottleneck with a drop-tail queue   (Module 6, Lab 8)
  N5  TCP vs UDP: request latency and throughput; end-to-end latency breakdown        (Lab 6)
  N6  DNS: correctness, cache, TCP fallback, retransmissions over a lossy link        (Module 7, Lab 9)

    python -m scamshield.experiments network
"""
import asyncio
import json
import random
import statistics
import time
from pathlib import Path

import numpy as np
import pandas as pd

from . import errorcodes as E
from . import protocol as P
from . import service as S
from .channel import LinkConfig, LossyUDPProxy
from .client import ArqClient, TcpClient, udp_classify
from .dns import DnsServer, Resolver, demo_zone

ROOT = Path(__file__).resolve().parents[3]
MESSAGES = None


def _messages(n=400):
    global MESSAGES
    if MESSAGES is None:
        df = pd.read_csv(ROOT / "data" / "upi_mixsms.csv")
        MESSAGES = df[df.split == "test"].text.tolist()
    return MESSAGES[:n]


# ------------------------------------------------------------------ N1
def exp_error_detection(trials=3000, seed=0):
    rng = random.Random(seed)
    frames = [P.encode(P.FrameType.CLASSIFY_REQ, {"text": t[:40]}) for t in _messages(200)]
    rows = []

    def flip(buf, positions):
        b = bytearray(buf)
        for p in positions:
            b[p // 8] ^= 1 << (7 - p % 8)
        return bytes(b)

    conditions = [("random", k) for k in (1, 2, 3, 4, 8)] + [("burst", L) for L in (2, 4, 8, 16, 17, 24, 32, 33, 48)]
    for kind, k in conditions:
        undetected = {name: 0 for name in E.CHECKS}
        for _ in range(trials):
            f = rng.choice(frames)
            data = f[:-4]
            nbits = len(data) * 8
            if kind == "random":
                pos = rng.sample(range(nbits), k)
            else:
                start = rng.randrange(nbits - k)
                inner = [start + i for i in range(1, k - 1) if rng.random() < 0.5]
                pos = [start, start + k - 1] + inner          # a burst starts and ends with an error
            bad = flip(data, pos)
            for name, (fn, _) in E.CHECKS.items():
                if fn(bad) == fn(data):
                    undetected[name] += 1
        for name, (_, bits) in E.CHECKS.items():
            rows.append({"error": kind, "size": k, "check": name, "check_bits": bits,
                         "undetected_rate": undetected[name] / trials, "trials": trials})
    # Hamming(7,4): correction of the 16-byte SSP header
    ham = []
    headers = [f[:P.HEADER_LEN] for f in frames]
    for ber in (1e-3, 5e-3, 1e-2, 2e-2, 5e-2):
        ok_plain = ok_ham = 0
        for _ in range(trials):
            h = rng.choice(headers)
            code = E.hamming_encode_bytes(h)
            noisy_plain = bytes(b ^ sum(1 << i for i in range(8) if rng.random() < ber) for b in h)
            noisy_code = bytes(b ^ sum(1 << i for i in range(7) if rng.random() < ber) for b in code)
            ok_plain += noisy_plain == h
            ok_ham += E.hamming_decode_bytes(noisy_code)[0] == h
        ham.append({"ber": ber, "header_intact_uncoded": ok_plain / trials, "header_recovered_hamming74": ok_ham / trials,
                    "overhead": "7/4 = 75% more bits"})
    return pd.DataFrame(rows), pd.DataFrame(ham)


# ------------------------------------------------------------------ helpers
async def _udp_server(handler=None, **arq_kwargs):
    t, proto, st = await S.start_udp(handler or S.Handler(stub=True), "127.0.0.1", 0, **arq_kwargs)
    return t, proto, t.get_extra_info("sockname")[:2]


async def _arq_run(server_addr, cfg, mode, window, n, congestion="fixed", rto=0.15):
    proxy = LossyUDPProxy(server_addr, cfg)
    addr = await proxy.start()
    texts = _messages(n)
    try:
        res, elapsed, st = await ArqClient(addr, mode=mode, window=window, congestion=congestion, rto=rto,
                                           min_rto=0.1).run(texts, timeout=300)
        ok = all(r["id"] == i for i, r in enumerate(res))
    finally:
        proxy.close()
    return {"mode": mode, "window": window, "congestion": congestion, "n": n, "ok": ok, "seconds": elapsed,
            "goodput_msgs_s": n / elapsed, "client_data_frames": st.data_sent, "retransmissions": st.retransmissions,
            "timeouts": st.timeouts, "efficiency": n / max(st.data_sent + st.retransmissions, 1),
            "link_dropped_loss": proxy.stats.dropped_loss, "link_dropped_queue": proxy.stats.dropped_queue,
            "mean_rtt_ms": 1000 * statistics.mean(st.rtt_samples) if st.rtt_samples else None,
            "cwnd_trace": st.cwnd_trace}


# ------------------------------------------------------------------ N2 / N3 / N4
async def exp_arq(seeds=(1, 2), n=300):
    t, proto, server = await _udp_server(rto=0.15, min_rto=0.1)
    rows = []
    for loss in (0.0, 0.02, 0.05, 0.1, 0.2):
        for mode in ("saw", "gbn", "sr"):
            for s in seeds:
                cfg = LinkConfig(loss=loss, delay_ms=5, jitter_ms=1, seed=s)
                r = await _arq_run(server, cfg, mode, 8, n)
                r.update(loss=loss, seed=s)
                r.pop("cwnd_trace")
                rows.append(r)
                print(f"  N2 {mode:3s} loss={loss:.2f} seed={s}: {r['seconds']:.2f}s goodput={r['goodput_msgs_s']:.0f}/s "
                      f"rtx={r['retransmissions']}", flush=True)
    burst = []
    for mode in ("gbn", "sr"):
        for s in seeds:
            cfg = LinkConfig(ge_p_gb=0.02, ge_p_bg=0.25, ge_loss_bad=0.7, delay_ms=5, seed=s)
            r = await _arq_run(server, cfg, mode, 8, n)
            r.update(loss="gilbert-elliott", seed=s)
            r.pop("cwnd_trace")
            burst.append(r)
    proto.close_all(); t.close()
    return pd.DataFrame(rows + burst)


async def exp_window(seeds=(1, 2), n=300):
    t, proto, server = await _udp_server(rto=0.15, min_rto=0.1)
    rows = []
    for mode in ("gbn", "sr"):
        for w in (1, 2, 4, 8, 16, 32):
            for s in seeds:
                cfg = LinkConfig(loss=0.02, delay_ms=10, seed=s)
                r = await _arq_run(server, cfg, mode, w, n)
                r.update(loss=0.02, seed=s)
                r.pop("cwnd_trace")
                rows.append(r)
                print(f"  N3 {mode} W={w:2d}: goodput={r['goodput_msgs_s']:.0f}/s", flush=True)
    proto.close_all(); t.close()
    return pd.DataFrame(rows)


async def exp_congestion(seeds=(1, 2), n=600):
    t, proto, server = await _udp_server(rto=0.15, min_rto=0.1, window=48)
    rows, traces = [], {}
    for variant, (w, cc) in {"fixed W=4": (4, "fixed"), "fixed W=16": (16, "fixed"), "fixed W=48": (48, "fixed"),
                             "AIMD (max 48)": (48, "aimd")}.items():
        for s in seeds:
            cfg = LinkConfig(delay_ms=5, rate_pps=400, queue=12, seed=s)
            r = await _arq_run(server, cfg, "sr", w, n, congestion=cc)
            if cc == "aimd" and s == seeds[0]:
                t0 = r["cwnd_trace"][0][0] if r["cwnd_trace"] else 0
                traces[variant] = [(round(a - t0, 4), b) for a, b in r["cwnd_trace"]]
            r.pop("cwnd_trace")
            r.update(variant=variant, seed=s, bottleneck_pps=400, queue=12)
            rows.append(r)
            print(f"  N4 {variant:14s}: goodput={r['goodput_msgs_s']:.0f}/s queue drops={r['link_dropped_queue']} "
                  f"rtx={r['retransmissions']}", flush=True)
    proto.close_all(); t.close()
    return pd.DataFrame(rows), traces


# ------------------------------------------------------------------ N5
async def exp_tcp_udp(n=500, detector=None):
    loop = asyncio.get_running_loop()
    rows = []
    for label, handler in (("stub (transport only)", S.Handler(stub=True)),
                           ("production detector", S.Handler(detector) if detector else None)):
        if handler is None:
            continue
        tcp, _ = await S.start_tcp(handler, "127.0.0.1", 0)
        tport = tcp.sockets[0].getsockname()[1]
        ut, uproto, ust = await S.start_udp(handler, "127.0.0.1", 0, rto=0.05)
        uport = ut.get_extra_info("sockname")[1]
        texts = _messages(n)

        def tcp_sequential():
            c = TcpClient("127.0.0.1", tport)
            lat, model = [], []
            for tx in texts[:200]:
                t0 = time.perf_counter()
                r = c.classify(tx, dns=False)
                lat.append((time.perf_counter() - t0) * 1000)
                model.append(r.get("model_ms", 0.0))
            t0 = time.perf_counter()
            c.classify_many(texts, dns=False)
            el = time.perf_counter() - t0
            c.close()
            return lat, model, el

        def udp_sequential():
            lat = []
            for tx in texts[:200]:
                t0 = time.perf_counter()
                udp_classify(tx, "127.0.0.1", uport, dns=False)
                lat.append((time.perf_counter() - t0) * 1000)
            return lat

        lat_tcp, model_ms, el_tcp = await loop.run_in_executor(None, tcp_sequential)
        lat_udp = await loop.run_in_executor(None, udp_sequential)
        _, el_sr, _ = await ArqClient(("127.0.0.1", uport), mode="sr", window=16, rto=0.05).run(texts)
        _, el_gbn, _ = await ArqClient(("127.0.0.1", uport), mode="gbn", window=16, rto=0.05).run(texts)
        for transport, lat, el in (("TCP (persistent, pipelined batch)", lat_tcp, el_tcp),
                                   ("UDP request/response", lat_udp, None),
                                   ("UDP + Selective Repeat (W=16)", None, el_sr),
                                   ("UDP + Go-Back-N (W=16)", None, el_gbn)):
            rows.append({"server": label, "transport": transport,
                         "rtt_p50_ms": float(np.median(lat)) if lat else None,
                         "rtt_p95_ms": float(np.percentile(lat, 95)) if lat else None,
                         "batch_msgs_s": n / el if el else None,
                         "model_ms_p50": float(np.median(model_ms)) if label != "stub (transport only)" and lat is lat_tcp else None})
        tcp.close()
        uproto.close_all()
        ut.close()
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ N6
async def exp_dns(trials=200):
    loop = asyncio.get_running_loop()
    srv = DnsServer(demo_zone(), delay_ms=20)               # 20 ms, like a resolver across the Internet
    addr = await srv.start()
    r = Resolver(addr, timeout=0.5, retries=1)
    correctness = []
    for name, qt in [("onlinesbi.sbi", "A"), ("onlinesbi.sbi", "AAAA"), ("www.hdfcbank.com", "A"),
                     ("kyc.verify-hdfc.top", "A"), ("sbi-kyc-update.xyz", "A"), ("refundhdfc.click", "A"),
                     ("does-not-exist.example", "A"), ("bigrecord.test", "TXT")]:
        res = await loop.run_in_executor(None, r.resolve, name, qt)
        correctness.append({"query": f"{name} {qt}", "rcode": res["rcode"], "answer": ", ".join(res["addresses"] or
                            [a["data"][:40] for a in res["answers"] if a["type"] in ("TXT", "PTR")]),
                            "cname_chain": " -> ".join(res["cname_chain"]), "min_ttl": res["min_ttl"],
                            "udp_truncated_then_tcp": res["truncated_over_udp"], "ms": res["elapsed_ms"]})
    ptr = await loop.run_in_executor(None, r.reverse, "198.51.100.10")
    correctness.append({"query": "198.51.100.10 PTR", "rcode": ptr["rcode"], "answer": ptr["answers"][0]["data"],
                        "cname_chain": "", "min_ttl": ptr["min_ttl"], "udp_truncated_then_tcp": False, "ms": ptr["elapsed_ms"]})
    # cache effect
    cold, warm = [], []
    for i in range(30):
        rc = Resolver(addr, timeout=0.5)
        t0 = time.perf_counter(); await loop.run_in_executor(None, rc.resolve, "onlinesbi.sbi", "A"); cold.append((time.perf_counter() - t0) * 1000)
        t0 = time.perf_counter(); await loop.run_in_executor(None, rc.resolve, "onlinesbi.sbi", "A"); warm.append((time.perf_counter() - t0) * 1000)
    cache = pd.DataFrame([{"lookup": "cold (network)", "p50_ms": np.median(cold), "p95_ms": np.percentile(cold, 95)},
                          {"lookup": "cached (TTL 3600 s)", "p50_ms": np.median(warm), "p95_ms": np.percentile(warm, 95)}])
    # retransmission over a lossy path
    rows = []
    for loss in (0.0, 0.1, 0.3):
        px = LossyUDPProxy(addr, LinkConfig(loss=loss, delay_ms=5, seed=3))
        paddr = await px.start()
        for retries in (0, 1, 2, 3):
            rr = Resolver(paddr, timeout=0.15, retries=retries, use_cache=False)
            ok, lat = 0, []
            for i in range(trials // 4):
                t0 = time.perf_counter()
                try:
                    await loop.run_in_executor(None, rr.resolve, "onlinesbi.sbi", "A")
                    ok += 1
                    lat.append((time.perf_counter() - t0) * 1000)
                except Exception:
                    pass
            rows.append({"loss": loss, "retries": retries, "success_rate": ok / (trials // 4),
                         "mean_ms_when_answered": float(np.mean(lat)) if lat else None})
        px.close()
    srv.close()
    return pd.DataFrame(correctness), cache, pd.DataFrame(rows)


# ------------------------------------------------------------------ driver + figures
def _figures(res_dir, err, arq, win, cong, traces):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig_dir = res_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    INK2, GRID = "#52514e", "#e4e3df"
    COL = {"parity": "#e87ba4", "inet_checksum": "#eda100", "crc16": "#1baf7a", "crc32": "#2a78d6",
           "saw": "#e34948", "gbn": "#eda100", "sr": "#2a78d6"}

    def style(ax):
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        ax.yaxis.grid(True, color=GRID, lw=0.8)
        ax.set_axisbelow(True)
        ax.tick_params(colors=INK2, labelsize=8.5)

    b = err[err.error == "burst"]
    fig, ax = plt.subplots(figsize=(7.5, 3.4))
    sizes = sorted(b["size"].unique())
    w = 0.2
    for i, chk in enumerate(["parity", "inet_checksum", "crc16", "crc32"]):
        vals = [b[(b["size"] == s) & (b.check == chk)].undetected_rate.iloc[0] for s in sizes]
        ax.bar(np.arange(len(sizes)) + (i - 1.5) * w, vals, w * 0.9, color=COL[chk], label=chk)
    ax.set_xticks(range(len(sizes)))
    ax.set_xticklabels([str(s) for s in sizes])
    ax.set_xlabel("burst length (bits)")
    ax.set_ylabel("undetected error rate")
    ax.set_title("Burst errors that slip past each frame check", loc="left")
    ax.legend(frameon=False, ncol=4, fontsize=8)
    style(ax)
    fig.tight_layout(); fig.savefig(fig_dir / "fig7_error_detection.png", dpi=200); fig.savefig(fig_dir / "fig7_error_detection.pdf"); plt.close(fig)

    a = arq[arq.loss != "gilbert-elliott"].copy()
    a["loss"] = a.loss.astype(float)
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 3.4))
    for mode, name in (("saw", "Stop-and-Wait"), ("gbn", "Go-Back-N"), ("sr", "Selective Repeat")):
        g = a[a["mode"] == mode].groupby("loss")[["goodput_msgs_s", "efficiency"]].mean()
        axes[0].plot(g.index * 100, g.goodput_msgs_s, marker="o", color=COL[mode], lw=2, label=name)
        axes[1].plot(g.index * 100, g.efficiency, marker="o", color=COL[mode], lw=2, label=name)
    axes[0].set_ylabel("goodput (messages/s)"); axes[1].set_ylabel("useful / transmitted frames")
    for ax in axes:
        ax.set_xlabel("packet loss (%)"); style(ax)
    axes[0].set_title("Throughput under loss (W = 8, RTT ≈ 10 ms)", loc="left")
    axes[1].set_title("Transmission efficiency", loc="left")
    axes[0].legend(frameon=False, fontsize=8)
    fig.tight_layout(); fig.savefig(fig_dir / "fig8_arq_loss.png", dpi=200); fig.savefig(fig_dir / "fig8_arq_loss.pdf"); plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.2, 3.4))
    for mode, name in (("gbn", "Go-Back-N"), ("sr", "Selective Repeat")):
        g = win[win["mode"] == mode].groupby("window").goodput_msgs_s.mean()
        ax.plot(g.index, g.values, marker="o", color=COL[mode], lw=2, label=name)
    ax.set_xscale("log", base=2); ax.set_xticks([1, 2, 4, 8, 16, 32]); ax.set_xticklabels(["1", "2", "4", "8", "16", "32"])
    ax.set_xlabel("sliding window (frames)"); ax.set_ylabel("goodput (messages/s)")
    ax.set_title("Pipelining: goodput vs window (2% loss, RTT ≈ 20 ms)", loc="left")
    ax.legend(frameon=False, fontsize=8); style(ax)
    fig.tight_layout(); fig.savefig(fig_dir / "fig9_window_sweep.png", dpi=200); fig.savefig(fig_dir / "fig9_window_sweep.pdf"); plt.close(fig)

    if traces:
        fig, ax = plt.subplots(figsize=(6.2, 3.2))
        for name, tr in traces.items():
            ts, cw = zip(*tr)
            ax.step(ts, cw, where="post", color="#2a78d6", lw=1.6)
        ax.set_xlabel("time (s)"); ax.set_ylabel("congestion window (frames)")
        ax.set_title("AIMD congestion window through a 400 pkt/s bottleneck", loc="left")
        style(ax)
        fig.tight_layout(); fig.savefig(fig_dir / "fig10_aimd_cwnd.png", dpi=200); fig.savefig(fig_dir / "fig10_aimd_cwnd.pdf"); plt.close(fig)


def run_all(res_dir):
    res_dir = Path(res_dir)
    tab = res_dir / "tables"
    tab.mkdir(parents=True, exist_ok=True)
    print("[network] N1 error detection", flush=True)
    err, ham = exp_error_detection()
    err.to_csv(tab / "net1_error_detection.csv", index=False)
    ham.to_csv(tab / "net1_hamming.csv", index=False)
    detector = None
    try:
        from ..detector import Detector
        detector = Detector()
    except Exception as e:
        print("  (production detector not found, N5 uses the stub only):", e)

    async def go():
        print("[network] N2 ARQ vs loss", flush=True)
        arq = await exp_arq()
        print("[network] N3 window sweep", flush=True)
        win = await exp_window()
        print("[network] N4 congestion", flush=True)
        cong, traces = await exp_congestion()
        print("[network] N5 TCP vs UDP", flush=True)
        tu = await exp_tcp_udp(detector=detector)
        print("[network] N6 DNS", flush=True)
        dns_c, dns_cache, dns_loss = await exp_dns()
        return arq, win, cong, traces, tu, dns_c, dns_cache, dns_loss

    arq, win, cong, traces, tu, dns_c, dns_cache, dns_loss = asyncio.run(go())
    arq.to_csv(tab / "net2_arq_loss.csv", index=False)
    win.to_csv(tab / "net3_window.csv", index=False)
    cong.to_csv(tab / "net4_congestion.csv", index=False)
    json.dump(traces, open(res_dir / "net4_cwnd_trace.json", "w"))
    tu.to_csv(tab / "net5_tcp_vs_udp.csv", index=False)
    dns_c.to_csv(tab / "net6_dns_queries.csv", index=False)
    dns_cache.to_csv(tab / "net6_dns_cache.csv", index=False)
    dns_loss.to_csv(tab / "net6_dns_loss.csv", index=False)
    _figures(res_dir, err, arq, win, cong, traces)
    print("[network] done", flush=True)
