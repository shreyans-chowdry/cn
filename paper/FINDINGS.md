# Key findings (draft material for the Results and Discussion sections)

All numbers are macro-F1 on the template-disjoint UPI-MixSMS test set (n = 3,939: 1,319 English, 1,297 Hindi–English,
1,323 Tamil–English) unless stated otherwise. The full tables are in `results/RESULTS.md`, the CSVs in `results/tables/`
and the figures in `results/figures/`. "Targeted" means only the scam messages are disguised; "uniform" means every
message is disguised.

Transformer coverage (CPU budget): DistilmBERT (standard and adversarial training), XLM-R and MuRIL (standard
training) were run on the current dataset. CANINE-S and the transformer cross-language runs were not rerun.

## 1. Clean performance
- **MuRIL and XLM-R are the most accurate on clean text**: 0.872 and 0.870. Next come Word NB 0.845, Word LR 0.835,
  Word SVM 0.807, Char LR 0.784 and Char SVM 0.771. DistilmBERT scores 0.709; the from-scratch BiGRU 0.688 ± 0.052 and
  Char CNN 0.581.
- **Character n-gram LR is 45–75× faster than the transformers** (1.5 ms against 65–108 ms per message on 2 CPU cores)
  and the best calibrated model (ECE 0.066).
- **Hard negatives cause most errors.** Models flag 14–40% of genuine and promotional messages as scams: genuine OTP
  advisories, AutoPay mandates and bank loan offers that share the scam vocabulary.
- **Each language setting is learnable.** Word LR scores 0.867 / 0.784 / 0.850 on English / Hindi–English /
  Tamil–English; MuRIL 0.893 / 0.857 / 0.867. Hindi–English messages have a code-mixing index of 39.0 (56% Hindi
  tokens), Tamil–English 40.6 (49% Tamil tokens). Language identification is 100% accurate on clean messages.

## 2. Robustness to disguise (RQ1)
- **Under the uniform threat every word and subword model loses accuracy steadily from L0 to L4**:
  Word LR −0.143, Word SVM −0.129, Word NB −0.116, BiGRU −0.314, XLM-R −0.255, MuRIL −0.178, DistilmBERT −0.149.
  The character models lose less: Char LR −0.097, Char SVM −0.081, Char CNN −0.067.
- **Under the targeted threat the word and subword models start missing scams.** Scams missed, L0 → L4:
  Word LR 11.8% → 27.9%, Word SVM 11.7% → 28.5%, MuRIL 3.4% → 24.7%, and **XLM-R 5.6% → 51.5%**. Char LR goes from
  10.1% to 18.9% and stays below 12% up to L3.
- **L4 (cross-script transliteration) is the strongest attack** for every model.
- **DistilmBERT treats disguise itself as a sign of a scam.** Its targeted miss rate stays low (0.5% → 5.8%), but when
  genuine messages are disguised too, its false-alarm rate rises from 25% to 41% at L2. A flat targeted curve does not
  mean the model is robust.

## 3. Character vs word representations (RQ2: the hypothesis)
- **20 of 24 paired tests support the hypothesis at p < 0.01** (paired bootstrap, 1,000 resamples).
  - Char LR vs Word LR and Char SVM vs Word SVM: 8 of 8 (Δdrop −0.026 to −0.054).
  - Char LR vs XLM-R: 4 of 4 (Δdrop −0.070 to −0.162; the largest effect).
  - Char LR vs MuRIL: 4 of 4 (Δdrop −0.024 to −0.085).
  - Char CNN vs BiGRU: 2 of 4. Under the uniform threat the CNN degrades far less (Δdrop −0.15, −0.16); under the
    targeted threat the BiGRU's score rises slightly, so the test goes the other way.
  - Char LR vs DistilmBERT: 2 of 4 (uniform threat). Under the targeted threat DistilmBERT's flat curve comes from its
    disguise-as-scam bias.
- For the paper: character representations resist character-level disguise better than word and subword
  representations, including the two strongest multilingual transformers. A model also has to be checked for false
  alarms on noisy genuine messages, not only for missed scams.

## 4. Transfer between languages (RQ3)
- Train on one language setting, test on the other two (classical and from-scratch models):
  **character n-gram models transfer best**. Char SVM loses 0.034 and Char LR 0.049; Word LR loses 0.115 and Word SVM
  0.112; the BiGRU collapses (0.301).
- The banking vocabulary (KYC, account, PIN, link, refund) stays in Latin script in every setting, and character
  n-grams pick it up across languages and scripts. At L2 the ordering holds (Char LR 0.721 cross-language vs Word LR 0.672).

## 5. Defences (RQ4)
- **Script-aware canonicalisation is the strongest defence for word models, with no retraining**. At L3:
  Word NB 0.856 (vs 0.824 adversarial training, 0.803 neither), Word LR 0.839 (0.821 / 0.796), Word SVM 0.835 (0.818 / 0.771).
  It also raises clean scores (Word NB 0.845 → 0.864), because it folds natural spelling variation too.
- **Adversarial training** (half of the training set replaced by L1–L3 disguised copies):
  - lowers scams missed at L3: Word LR 22.8% → 14.3%, Word SVM 22.2% → 14.7%, Word NB 21.2% → 14.4%;
  - rescues the BiGRU (0.688 → 0.752 clean) and Word RF (0.731 → 0.801);
  - generalises to the unseen L4 attack (Word LR 0.779 → 0.809);
  - raises DistilmBERT at every level (0.709 → 0.744 clean, 0.694 → 0.734 at L4).
- **The shipped detector** (char n-grams + canonicalisation + disguised copies + real public data) is the most stable:
  0.810 / 0.805 / 0.798 / 0.795 / 0.787 for L0–L4, ECE ≤ 0.059, and 0.878 on real smishing (Mishra & Soni, held out).

## 6. External validity with real SMS corpora (RQ5)
- **A model trained only on the synthetic corpus does not work on real SMS**: on held-out Mishra & Soni messages it
  scores 0.148 and flags 84% of genuine messages as scams.
- **A model trained only on public corpora does not work on UPI scams**: 0.44 / 0.36 / 0.35 on English / Hindi–English /
  Tamil–English, missing 69–89% of the scams. The public corpora contain neither UPI fraud nor code-mixed Indic text.
- **Joint training fixes both directions**: 0.818 / 0.798 / 0.827 on the three UPI-MixSMS settings and 0.882 on
  Mishra & Soni (genuine false-positive rate 0.5%).
- ExAIS stays hard (binary F1 0.56): its "spam" is mostly telecom marketing outside the scam classes.

## 7. Link intelligence and cues
- **Link intelligence does not lower missed scams on this test set** (10.4% with and without) and adds a few false
  alarms (19.8% → 20.1%), because the text model already catches nearly every scam that carries a link. Its value is
  explanatory (the user sees why a link is dangerous) and for links in otherwise innocent-looking text.
- On Mishra & Soni it has no effect: only 31 of 1,142 messages contain a link.
- **Masking all non-language cues** (URLs, UPI IDs, phone numbers, amounts) changes clean accuracy by at most ±0.02 for
  the linear models: the signal is in the multilingual text itself.

## 8. Networking results (N1–N6)
- **N1 Error detection** (3,000 trials per condition on real SSP frames).
  - CRC-32 and CRC-16 caught every corrupted frame in every condition.
  - A parity bit misses every even-numbered bit error and about half of all bursts of length 4–48.
  - The Internet checksum misses 3.2% of random 2-bit errors.
  - Hamming(7,4) recovers the 16-byte header at a bit error rate of 10⁻² in 94.5% of cases (uncoded: 28.4%), at the
    cost of 75% more bits.
- **N2 ARQ under loss** (window 8, round trip ≈ 10 ms):
  - At 0% loss: Selective Repeat and Go-Back-N each deliver about 590 messages/s; Stop-and-Wait 78.
  - Under loss Go-Back-N keeps up on goodput but retransmits 3–4× more frames:
    - efficiency at 10% loss: 0.52 (Go-Back-N) vs 0.80 (Selective Repeat)
    - at 20% loss: 0.39 vs 0.66
  - Stop-and-Wait has Selective Repeat's efficiency but a fraction of its throughput.
- **N3 Window size** (2% loss, RTT ≈ 20 ms). Goodput rises from 37 messages/s at window 1 to 159–181 at windows
  16–32 (pipelining over the bandwidth–delay product).
- **N4 Congestion** (400 packets/s bottleneck, 12-packet queue):
  - A fixed window of 48 overflows the queue: about 1,040 drops, 500 retransmissions, 61 messages/s.
  - AIMD reaches 120 messages/s at 95% efficiency, finding a working point on its own (the sawtooth in figure 10).
  - A window of 4, matched to the bandwidth–delay product, is best (198 messages/s, no drops).
- **N5 TCP vs UDP.**
  - Transport alone: a UDP request/response takes 0.28 ms median against 0.61 ms over TCP.
  - With the real detector the model dominates: about 3 ms round trip, of which 1.7 ms is the model, and 290–360
    messages/s for pipelined batches over either transport.
- **N6 DNS.**
  - A cached lookup takes 0.20 ms against 21.1 ms over the network.
  - An answer too big for UDP sets the TC bit and is fetched again over TCP automatically.
  - At 30% packet loss, 0 / 1 / 2 / 3 retransmissions give 52% / 72% / 82% / 90% success, with mean latency rising
    from 32 ms to 163 ms.

## 9. The deployed system
- **The Android app gives the same answers as Python**: on 300 messages the canonicaliser output and labels are
  identical, and the largest probability difference is 7×10⁻⁷. Hindi–English and Tamil–English scams are detected on
  the phone with automatic language identification.
- **It is light**: the APK is 4.3 MB and an on-device check takes a few milliseconds.

## Suggested one-line conclusion
Character-level representations hold up significantly better than word-level and subword representations, including
XLM-R and MuRIL, when multilingual code-mixed UPI scams are disguised at the character level. Cross-script
transliteration is the strongest attack, and some pretrained models learn to treat any disguise as a scam. A
script-aware canonicaliser in front of a character n-gram model, trained jointly on synthetic and real SMS, gives a
robust, calibrated, millisecond-latency detector that runs identically on a phone and behind a CRC-protected protocol
over TCP and UDP, and that extends to a new language by registering its script.
