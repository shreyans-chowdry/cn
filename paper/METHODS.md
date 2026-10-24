# Methods (reference for writing the paper)

Everything here describes exactly what the code does, so it can be lifted into the Dataset, Method, System and
Experimental Setup sections. Results and their interpretation are in `FINDINGS.md`; the syllabus mapping and
novelty statement are in `CN_MAPPING_AND_NOVELTY.md`.

## 1. Research questions

- **RQ1 Obfuscation robustness.** How do word-level, subword and character-level scam classifiers degrade as SMS text is increasingly disguised?
- **RQ2 Representation hypothesis.** Do character-level representations degrade less than word-level and subword representations under character-level obfuscation?
- **RQ3 Bilingual transfer.** Does a detector trained on English transfer to Tamil–English and vice versa, and does obfuscation change that?
- **RQ4 Defences.** Does adversarial training, or script-aware canonicalisation, restore performance, including against an attack family not seen in training (cross-script transliteration, L4)?
- **RQ5 External validity.** How does a model trained on the synthetic corpus behave on real public SMS corpora, and vice versa?
- **RQ6 Networked deployment.** What do reliability, error detection, congestion control and DNS-based link checks cost and buy when the detector is served over the network?

## 2. Dataset: UPI-BiSMS

**Classes.** `scam` (positive class for the false-negative rate), `legit` (transaction alerts, OTPs, AutoPay mandates, genuine payment requests, personal payment chats, bank security advisories, bill confirmations) and `promo` (cashback, sales, bank loan offers, telecom recharge, reward points).

**Language settings.** English (en) and Tamil–English (ta). In the Tamil–English setting, Tamil is written in Tamil script and the banking vocabulary (KYC, account, link, OTP, PIN, refund, app and bank names) stays in Latin script, often with a Tamil case suffix attached (link-ஐ, account-க்கு, Swiggy-ல்). This is intra-word code-mixing. Romanised Tamil ("Tanglish") is not a language setting; it only appears as the L4 transliteration attack.

**Intents (23 subtypes).** Scam: KYC/PAN block, refund or cashback collect-request PIN fraud, lottery/prize, "wrong transfer" refund, task/part-time job, electricity disconnection, customs parcel/FIR threat, fake customer support (AnyDesk/OTP/CVV), instant loan fee, reward-points phishing, QR-code "scan to receive" fraud. Legit: debit alert, credit alert, OTP, genuine collect request, UPI AutoPay mandate, personal chat, security advisory, bill paid. Promo: cashback offer, sale, bank loan promotion, recharge plan, reward points.

**Hard negatives.** Genuine messages deliberately reuse scam vocabulary: OTP messages saying "do not share", advisories that mention KYC/PIN/link, genuine reward-point expiry reminders, genuine bank pre-approved loan offers, genuine AutoPay mandates ("approve", "debit") and "I sent you money" chats.

**Templates.** 3–4 templates per subtype, written in parallel in both languages (same intent, same slots). Slots are filled with realistic values: bank names, UPI apps, UPI IDs (`name1234@ybl`), Indian amounts in six formats, mobile numbers, 12-digit UPI references, dates, merchants, electricity boards and couriers. Scam links are look-alike domains (`sbi-kyc-update.xyz`, `refundhdfc.click`) or URL shorteners. Genuine links are official domains, plus some shorteners, so a shortener on its own does not give a message away.

**Natural variation (clean data).** English: informal spellings (ur, pls, u), random casing and punctuation drift. Tamil: formal ↔ colloquial register (செய்யவும் / செய்யுங்க / பண்ணுங்க, உள்ளது / இருக்கு) at rate 0.5, and English loanwords occasionally typed in Tamil script (account → அக்கவுண்ட், rate 0.08). Both: shared prefixes/suffixes and spoofable DLT sender headers (`VM-ABCDEF:`).

**Size and split.** 9,970 messages after de-duplication (4,980 English, 4,990 Tamil–English; 4,377 legit, 3,596 scam, 1,997 promo). In Tamil–English messages, the mean Code-Mixing Index (Das & Gambäck 2014) is 40.5 and 49% of the language tokens are Tamil. The split is template-disjoint: for each subtype, one template index is held out for test in both languages. Test 3,240, train 5,721, validation 1,009 (a random 15% of the training pool).

**Public corpora (integrated by Ayushmaan Nayak).** Mishra & Soni SMS phishing dataset (5,971 English SMS labelled ham/spam/smishing → legit/promo/scam), UCI SMS Spam Collection (ham/spam), ExAIS (20 users' handset logs, received messages only, ham/spam), and the machine-translated multilingual UCI (21 languages, used only as a stress test). Exact duplicates are removed inside and across corpora on a normalised key, and texts with conflicting labels are dropped. Splits are 80/20 and grouped, so every translation of a message stays on one side. UCI and ExAIS "spam" mixes scams and adverts, so it is used for binary evaluation only.

## 3. Obfuscation scheme (L0–L4)

Each eligible token (not a URL, UPI ID or number) is perturbed with probability *p*; **salient fraud words** (KYC, PIN, OTP, refund, link, block, prize … and Tamil உடனே, பணம், பரிசு, அனுப்பவும், காலாவதியாகிறது …) with probability 2*p* (capped at 0.95). Operators are chosen by the token's script. Operators introduced at a level are weighted ×3 (transliteration ×6 at L4). A Latin stem with a Tamil case suffix (PIN-ஐ) has only its stem perturbed.

| Level | Name | p | ops | Latin-script tokens | Tamil-script tokens |
|---|---|---|---|---|---|
| L0 | clean | 0 | 0 | – | – |
| L1 | light | 0.15 | 1 | vowel drop, letter repeat, case flip, adjacent swap, phonetic respelling | confusable letters (ல/ள/ழ, ண/ந/ன, ர/ற), vowel-length swaps (ி/ீ, ு/ூ, ெ/ே, ொ/ோ), pulli (்) dropped or added |
| L2 | moderate | 0.30 | 1 | + leetspeak (a→@/4, o→0, i→1/!, s→$/5), separators (K.Y.C, P-I-N) | + separators between graphemes (உ.ட.னே) |
| L3 | heavy | 0.45 | 1–2 | + Latin→Cyrillic/Greek homoglyphs, zero-width characters, random insert/delete | + Tamil-digit homoglyphs (க→௧, உ→௨, அ→௮, எ→௭), ZWJ/ZWNJ, grapheme deletion |
| L4 | cross-script | 0.60 | 1–3 | + English word written in Tamil script (account → அக்கவுண்ட்) | + Tamil word transliterated to Latin, Tanglish style (உடனே → udane) |

Measured character edit rate (normalised Levenshtein) on test messages: L1 2.8%, L2 7.9%, L3 11.6%, L4 25.6%. Words changed: 13%, 37%, 47%, 58%.

**Threat models.** *Targeted*: only scam messages are obfuscated, because the attacker controls only scam text. *Uniform*: every message is obfuscated, a noisy-channel stress test. For a given seed, a scam message receives the same perturbation in both settings. The scam FNR is therefore identical across the two threat models, and the scam FPR changes only under the uniform threat. Three obfuscation seeds are used per (level, threat).

**Automatic language identification.** Each token is tagged by script and lexicon: Tamil script, English, romanised Tamil (a lexicon plus Tamil romanisation patterns that do not occur in the English vocabulary), "mix" (an English stem with a Tamil suffix, counted for both languages) or language-independent (numbers, URLs, IDs). The message label (English / Tamil / Tamil–English / Tamil romanised) follows from the token mix. Accuracy on clean UPI-BiSMS is 100%.

## 4. Models

| Model | Representation | Details |
|---|---|---|
| Word NB / RF / LR / SVM | word | word 1–2-gram counts or TF-IDF (Tamil-aware tokeniser: `[\w஀-௿]+`, because `\w` alone splits Tamil words at vowel signs) |
| Word BiGRU | word | 128-d embeddings, BiGRU(128), max+mean pooling, trained from scratch, 3 seeds |
| Char LR / SVM | character | char_wb 2–5-gram TF-IDF (≤200k features) |
| Char CNN | character | char embeddings, parallel conv 3/5/7, from scratch, 3 seeds |
| DistilmBERT | subword | distilbert-base-multilingual-cased |
| XLM-R | subword | xlm-roberta-base (input embeddings frozen to fit CPU memory) |
| MuRIL | subword | google/muril-base-cased, pretrained on 17 Indian languages incl. Tamil, plus transliterated text (input embeddings frozen) |
| CANINE-S | character | google/canine-s, tokenizer-free |

Transformers: AdamW, linear warm-up 10%, 1 epoch, batch 16, class-weighted loss, full training set, CPU; evaluated on obfuscation seed 0. Coverage: all four with standard training; DistilmBERT also with adversarial training; DistilmBERT and MuRIL in the bilingual-transfer experiment. Regimes: *standard*; *adversarial training* (each training message replaced with probability 0.5 by an L1–L3 obfuscated copy, so L4 transliteration is never seen); *canonicalisation* (+norm, train and test text passed through the defence below).

**Script-aware canonicalisation.** NFKC normalisation; zero-width removal; Latin look-alikes (Cyrillic/Greek) folded to Latin; Tamil digits used as letters folded to letters; separators inside words removed in both scripts; leetspeak undone in alphabetic Latin tokens; Tamil-script spellings of English loanwords mapped back to English; letter runs squeezed; lower-cased. It has no access to the attack's random choices, and it cannot undo Tamil→Latin transliteration.

**Production detector** (`scamshield/detector.py`, served by the web app, the TCP/UDP services and the Android app). Char 2–5-gram TF-IDF (60k features) on canonicalised text, followed by multinomial logistic regression (C = 10, class-balanced). It is trained on UPI-BiSMS train+val, plus an obfuscated copy (L1–L4) of 50% of it, plus the Mishra & Soni train split (3-class) and the UCI/ExAIS genuine messages. Fusion with link intelligence: P'(scam) = 1 − (1 − P(scam))(1 − 0.6·risk), with the other classes rescaled; the verdict is scam if P'(scam) ≥ 0.5, otherwise the larger of legit and promo. Bilingual rule cues (PIN to receive money, OTP sharing, urgency, threats, fee-first, remote access apps, prizes, QR scanning, wrong transfer, job lures) only explain verdicts; they never change scores.

## 5. Networked system

**SSP, the ScamShield Protocol.** Big-endian frame: MAGIC 'SS' (2 B) | VER (1) | TYPE (1) | FLAGS (1) | WIN (1) | SEQ (4) | ACK (4) | LEN (2) | payload (LEN, UTF-8 JSON) | CRC-32 (4, IEEE 802.3 polynomial, computed over header + payload). Types: CLASSIFY_REQ/RESP, DATA, ACK, NAK, PING/PONG, ERROR, FIN. Over TCP, frames are sent back to back and reassembled from the stream by LEN. Over UDP, one datagram carries one frame. A frame with a bad CRC is dropped.

**Transport options.** (a) TCP with a persistent connection, sequential or pipelined requests. (b) UDP request/response with application-level retry. (c) UDP with our ARQ layer: Stop-and-Wait, Go-Back-N (cumulative ACKs, one timer, the whole window resent on timeout) or Selective Repeat (per-frame ACKs and timers, out-of-order frames buffered). The ARQ layer adds advertised receive windows (flow control), Jacobson/Karels RTO (SRTT, RTTVAR, RTO = SRTT + 4·RTTVAR, minimum 100 ms), Karn's rule, exponential back-off cleared when new data is acknowledged, a 15-retry abort, and optional AIMD congestion control (slow start, congestion avoidance, cwnd → 1 and ssthresh → cwnd/2 on timeout, at most one decrease per window).

**Impaired-link emulator.** A UDP proxy with Bernoulli or Gilbert-Elliott burst loss, bit errors, one-way delay with FIFO-preserving jitter, and a bottleneck (service rate in packets/s with a drop-tail queue). Seeds are deterministic.

**DNS.** Client: RFC 1035 wire format, name compression, A/AAAA/CNAME/NS/PTR/TXT, transaction-ID check, timeout and retries, TCP fallback on the TC bit, positive and negative TTL cache, reverse lookups via in-addr.arpa/ip6.arpa. Server: authoritative for a small demo zone (documentation address ranges, RFC 5737/3849), NXDOMAIN otherwise, CNAME chasing, TC for answers over 512 bytes, UDP and TCP, optional forwarding.

**Link intelligence.** URL extraction (handling Tamil case suffixes such as link-ல் and excluding UPI IDs), then lexical features: shortener, raw IP host, punycode/IDN, risky TLD, a brand name in a non-official domain, hyphens/digits, deep subdomains, http. Network features: NXDOMAIN, TTL < 120 s, and resolution into a special-purpose CIDR block (private, loopback, link-local, CGNAT, reserved, multicast, unique-local) by longest-prefix match. The risk is the capped sum of the feature weights.

**Android app.** Kotlin/Jetpack Compose, minSdk 26. A BroadcastReceiver for SMS_RECEIVED joins multi-part messages, classifies them on the phone (a Kotlin port of the canonicaliser, the char_wb analyser, TF-IDF and the logistic regression, plus link intelligence with system DNS and CIDR checks), stores the history and posts a high-priority notification for scams. Server mode sends CLASSIFY_REQ frames over TCP and falls back to on-device checks if the server is unreachable. Parity test: on 300 messages (clean, obfuscated, public), the Kotlin canonicaliser output is identical to Python on all 300, predicted labels are identical, and the maximum probability difference is 7×10⁻⁷.

## 6. Metrics and statistics

Macro-F1 (primary); scam false-negative rate (scams missed) and scam false-positive rate; expected calibration error (top-label, 15 bins); latency (median and p95 of single-message CPU time over 200 messages, plus batch throughput). 95% bootstrap CIs (500 resamples) for clean macro-F1. Mean ± std over obfuscation seeds (and training seeds for the from-scratch neural models). For RQ2, a paired bootstrap (1,000 resamples) on the difference in degradation Δdrop = [F1(A,L0) − F1(A,Lk)] − [F1(B,L0) − F1(B,Lk)] between a character model A and a word/subword model B, with a one-sided p for "A degrades less", plus an exact McNemar test on the attacked predictions. Network metrics: goodput (classified messages/s), completion time, retransmissions, efficiency (useful frames / transmitted frames), queue drops, RTT percentiles, and the undetected-error rate.

## 7. Experiments

- **E1** Robustness curves L0–L4, both threat models, all models.
- **E2** Bilingual transfer: train on one language's training data, test on both (clean and L2 targeted).
- **E3** Adversarial training vs standard training, including the unseen L4.
- **E4** Canonicalisation defence vs adversarial training.
- **E5** Latency and model size.
- **E6** Cue ablation: URLs, UPI IDs, phone numbers, amounts, sender headers and digits masked in training and test.
- **E7** External validity: train on UPI-BiSMS / public corpora / both, test on UPI-BiSMS (per language) and held-out public corpora (binary), plus the translated multilingual stress test; link-intelligence ablation.
- **N1** Error detection: parity, Internet checksum, CRC-16, CRC-32 on real SSP frames; random 1–8-bit errors and bursts of length 2–48; Hamming(7,4) on headers at BER 10⁻³–5·10⁻².
- **N2** Stop-and-Wait / Go-Back-N / Selective Repeat at 0–20% loss and under Gilbert-Elliott bursts (window 8, RTT ≈ 10 ms, 300 messages, 2 seeds).
- **N3** Window sweep 1–32 at 2% loss, RTT ≈ 20 ms.
- **N4** Fixed windows 4/16/48 vs AIMD through a 400 packets/s bottleneck with a 12-packet drop-tail queue.
- **N5** TCP vs UDP: request RTT and batch throughput, with a transport-only stub and with the production detector.
- **N6** DNS: query correctness (A, AAAA, CNAME chain, NXDOMAIN, TXT truncation → TCP, PTR), cold vs cached latency (20 ms server delay), and success rate vs retries at 0/10/30% loss.

## 8. Limitations to state in the paper

- UPI-BiSMS is synthetic and template-based. The controlled design isolates the effect of obfuscation, but absolute scores do not transfer to real SMS traffic. E7 quantifies this gap with real public corpora, all of which are English.
- The Tamil–English templates use one natural register per template plus systematic register variation. Real users vary more (other dialects, spelling habits).
- Transformers were fine-tuned for one epoch on CPU (XLM-R and MuRIL with frozen input embeddings), so their absolute numbers are conservative.
- Validation is in-template, so early stopping cannot detect over-fitting to phrasing.
- The obfuscator is random, not an optimising adversary.
- Network experiments run on localhost through an emulator; absolute throughputs reflect a 2-core CPU, and the comparisons between protocols are what matters.
- The DNS checks in the experiments use a demo zone (real scam domains from these corpora no longer resolve). The deployed system can query any resolver.
