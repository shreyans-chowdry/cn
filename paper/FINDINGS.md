# Key findings (draft material for the Results and Discussion sections)

All numbers are macro-F1 on the template-disjoint UPI-BiSMS test set (n = 3,240: 1,590 English and 1,650 Tamil–English) unless stated otherwise.
The full tables are in `results/RESULTS.md`, the CSVs in `results/tables/` and the figures in `results/figures/`.
"Targeted" means only the scam messages are disguised. "Uniform" means every message is disguised.

## 1. Clean performance
- **XLM-R is the most accurate model on clean text**, with macro-F1 0.851 (English 0.857, Tamil–English 0.844). The next group is close together: Word NB 0.794, Word LR 0.785, Word SVM 0.782, DistilmBERT 0.778, CANINE-S 0.778, Char LR 0.777, Char SVM 0.772 and MuRIL 0.749. The from-scratch neural models trail: Word BiGRU 0.574 ± 0.093 and Char CNN 0.660.
- **Character n-gram LR is roughly 70–190 times faster than the transformers**: about 0.8 ms per message against 59–155 ms on 2 CPU cores. It is also the best calibrated model (ECE 0.046).
- **Hard negatives cause most of the errors.** Every model flags 14–38% of genuine and promotional messages as scams (the scam false-positive rate). These are genuine KYC/OTP advisories, AutoPay mandates and bank loan offers that share the scam vocabulary.
- **Tamil–English is not harder than English.** For most models it scores the same or better: Word LR scores 0.828 on Tamil–English and 0.738 on English. In Tamil–English messages, 49% of the words are Tamil and the code-mixing index is 40.

## 2. Robustness to disguise (RQ1)
- **Under the uniform threat, every word and subword model loses accuracy steadily from L0 to L4**:
  - Word LR −0.118, Word SVM −0.101, Word RF −0.299, BiGRU −0.152
  - XLM-R −0.174, DistilmBERT −0.090

  The character n-gram models lose less (Char LR −0.064, Char SVM −0.061).
- **Under the targeted threat, the word models start missing scams.** Word LR's scam false-negative rate rises from 0.129 to 0.234 at L4 and Word SVM's from 0.080 to 0.232. **XLM-R, the best clean model, goes from missing 7% of scams to missing 31%.**
- **Character n-gram models are almost untouched by targeted disguises.** Char LR misses 13.2% of scams on clean text, 8.9% at L3 and 12.9% at L4. The disguised scam text still shares enough character n-grams with scam training data.
- **L4 (cross-script transliteration) is the strongest attack** for most models. The scam false-negative rate is highest at L4 for Word NB, Word LR, Word SVM, XLM-R, MuRIL, CANINE-S and Char SVM.
- **DistilmBERT and CANINE-S treat disguise itself as a sign of a scam.** Their scam false-negative rate stays flat or falls under the targeted threat (DistilmBERT 0.045 → 0.049). But when genuine messages are disguised too, they get flagged:
  - CANINE-S false-positive rate 0.236 → 0.362
  - DistilmBERT false-positive rate 0.191 → 0.368 at L2

  So a flat targeted curve does not mean the model is robust.

## 3. Character vs word representations (RQ2: the hypothesis)
- **The hypothesis holds for the classical and from-scratch models in 10 of 12 paired tests** (p < 0.01). The pairs are Char LR vs Word LR, Char SVM vs Word SVM and Char CNN vs BiGRU, at L3 and L4 under both threats. The other two point the same way but are weaker: Char SVM uniform L3 p = 0.07 and Char CNN targeted L3 p = 0.04.
  - The largest effect is Char CNN vs BiGRU under uniform L3: a drop of 0.021 against 0.173 (Δ = −0.15).
- **Char LR also degrades significantly less than XLM-R in all 4 tests** (Δ between −0.05 and −0.11, p < 0.001).
- **For the pretrained character transformer, the result depends on the threat:**
  - Targeted: CANINE-S degrades less than XLM-R and MuRIL (4 of 4 tests, p < 0.001).
  - Uniform: CANINE-S degrades more than MuRIL and DistilmBERT, because of the "disguise = scam" bias in section 2.
- **Overall, 18 of 28 tests support the hypothesis at p < 0.01.** For the paper: character representations do resist character-level disguise better than word and subword representations. A character-level transformer also needs to be checked for false alarms on noisy genuine messages, not only for missed scams.

## 4. English ↔ Tamil–English transfer (RQ3)
- **Character n-gram models transfer best.** Char LR trained on one language and tested on the other scores 0.795, which is above its in-language score of 0.750. The banking vocabulary (KYC, account, PIN, link, refund) stays in English inside Tamil–English messages, and character n-grams pick it up in either language.
- **Word models lose 0.06–0.07 across languages. DistilmBERT loses 0.24** (0.822 → 0.583), and the BiGRU and Char CNN collapse.
- **MuRIL is the exception among transformers**, with a transfer gap of only 0.005. It was pretrained on Indian languages, including Tamil and transliterated text.

## 5. Defences (RQ4)
- **Adversarial training** (half of the training set replaced by L1–L3 disguised copies):
  - Reduces the scam false-negative rate at L3 for most word models: Word LR 0.192 → 0.103, Word SVM 0.164 → 0.110, Word NB 0.217 → 0.151. Word RF is unchanged.
  - Rescues the BiGRU (0.574 → 0.675 clean).
  - Generalises to the unseen L4 transliteration: Word LR 0.758 → 0.768, BiGRU 0.546 → 0.661.
  - Costs the character SVM 0.03 of clean accuracy.
  - For DistilmBERT it raises every level by about 0.025 (0.778 → 0.806 clean, 0.782 → 0.805 at L4).
- **Script-aware canonicalisation** needs no retraining and matches or beats adversarial training for the linear word models:
  - Word LR at L3: 0.795 with canonicalisation, 0.781 with adversarial training, 0.770 with neither
  - Word SVM at L4: 0.770 / 0.761 / 0.744
  - Word NB at L3: 0.800 / 0.791 / 0.770
- **The production recipe** (char n-grams + canonicalisation + disguised copies + real public data):
  - Macro-F1 stays flat across all disguise levels: 0.792 / 0.790 / 0.787 / 0.783 / 0.789 for L0–L4. This is the most stable curve of any model.
  - On real smishing it scores 0.883 (Mishra & Soni, held out).

## 6. External validity with real SMS corpora (RQ5; Ayushmaan's datasets)
- **A model trained only on the synthetic corpus does not work on real SMS.**
  - On held-out Mishra & Soni messages: macro-F1 0.149, and it flags 84% of genuine messages as scams.
  - On the translated multilingual stress test: binary F1 0.45.
- **A model trained only on public corpora does not work on UPI scams.**
  - On UPI-BiSMS it scores 0.41 (English) and 0.30 (Tamil–English), missing 70–89% of the scams.
  - English-only public corpora contain neither UPI-specific fraud nor Tamil.
- **Joint training fixes both directions:**
  - UPI-BiSMS: 0.783 (English) and 0.744 (Tamil–English)
  - Mishra & Soni: 0.869 (genuine false-positive rate 0.7%)
  - Translated stress test: binary F1 0.94
- **ExAIS stays hard (binary F1 0.58).** Its "spam" is mostly Nigerian telecom marketing, which falls outside the scam classes.

## 7. Link intelligence and cues
- **Adding link intelligence to the text model** lowers the scam false-negative rate on UPI-BiSMS from 0.183 to 0.151, with no change in false positives (0.249 → 0.251).
- **On Mishra & Soni (2000s-era SMS) it has no effect**: only 31 of 1,142 messages contain a link.
- **Hiding all non-language cues** (URLs, UPI IDs, phone numbers, amounts) changes word-model accuracy by at most ±0.03. Most of the signal is in the bilingual text itself.
  - Character models lose about 0.05, because they also read the character patterns of look-alike domains.

## 8. Networking results (N1–N6)
- **N1 Error detection.**
  - CRC-32 and CRC-16 caught every corrupted frame in every condition.
  - A parity bit misses every even-numbered bit error and about half of all bursts.
  - The Internet checksum misses 3% of random 2-bit errors.
  - Hamming(7,4) recovers the 16-byte header at a bit error rate of 10⁻² in 94.5% of cases (uncoded: 28.3%), at the cost of 75% more bits.
- **N2 ARQ under loss** (window 8, round trip ≈ 10 ms):
  - At 0% loss: Selective Repeat and Go-Back-N each deliver about 620 messages/s; Stop-and-Wait 85.
  - At 2–10% loss, Go-Back-N's goodput stays close to Selective Repeat's, but it retransmits 2.5–4× more frames:
    - efficiency at 10% loss: 0.53 (Go-Back-N) vs 0.82 (Selective Repeat)
    - at 20% loss: 0.42 vs 0.67
  - Stop-and-Wait has Selective Repeat's efficiency but a fraction of its throughput.
- **N3 Window size.** Goodput rises from about 38 messages/s at window 1 to about 150–177 at windows 16–32. This is pipelining over the bandwidth-delay product.
- **N4 Congestion** (400 packets/s bottleneck, 12-packet queue):
  - A fixed window of 48 overflows the queue: 972 drops, 492 retransmissions, 74 messages/s.
  - AIMD gets 129 messages/s with 376 drops, finding a working point on its own (the sawtooth in figure 10).
  - A window of 4, matched to the bandwidth-delay product, is best (198 messages/s, no drops).
- **N5 TCP vs UDP.**
  - Transport alone: a UDP request/response takes 0.19 ms median against 0.32 ms over TCP.
  - With the real detector, the model dominates: about 2 ms round trip, of which 1.07 ms is the model, and 480–540 messages/s for pipelined batches.
- **N6 DNS.**
  - A cached lookup takes 0.14 ms against 20.7 ms over the network.
  - An answer too big for UDP sets the TC bit and is fetched again over TCP automatically.
  - At 30% packet loss, 0 / 1 / 2 / 3 retransmissions give 52% / 72% / 82% / 90% success, with mean latency rising from 32 ms to 162 ms.

## 9. The deployed system
- **The Android app gives the same answers as Python.** On 300 messages the canonicaliser output is identical, the labels are identical, and the largest probability difference is 7×10⁻⁷.
- **It is light.** The APK is 4.3 MB and an on-device check takes a few milliseconds.

## Suggested one-line conclusion
Character-level representations hold up significantly better than word-level and subword representations when bilingual Tamil–English UPI scams are disguised at the character level. Cross-script transliteration remains the strongest attack, and some pretrained models learn to treat any disguise as a scam. A script-aware canonicaliser in front of a character n-gram model, trained jointly on synthetic and real SMS and fused with network-level link intelligence, gives a robust, calibrated, millisecond-latency detector. It runs identically on a phone and behind a CRC-protected protocol over TCP and UDP.
