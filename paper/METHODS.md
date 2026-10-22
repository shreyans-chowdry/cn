# Methods (reference for writing the paper)

Everything here describes exactly what the code does, so it can be lifted into the paper's
Dataset, Method and Experimental Setup sections.

## 1. Research questions

- **RQ1 (Obfuscation robustness).** How do word-level, subword and character-level scam classifiers degrade as character-level obfuscation of SMS text increases?
- **RQ2 (Representation hypothesis).** Do character-level representations degrade less than word-level / subword representations under character-based obfuscation?
- **RQ3 (Cross-lingual transfer).** Does a detector trained on one code-mixed language pair transfer to others, and does obfuscation change that?
- **RQ4 (Adversarial training).** Does training on obfuscated copies restore performance, including on an obfuscation family not seen in training (cross-script, L4)?
- **RQ5 (Deployment cost).** What are the calibration and latency costs of each model family?

## 2. Dataset: UPI-CMX

**Classes.** `scam` (positive class for FNR), `legit` (transaction alerts, OTPs, genuine payment requests, personal payment chats, bank security advisories, bill confirmations), `promo` (cashback, sales, bank loan offers, telecom recharge, reward-point reminders).

**Language settings (5).** Indian English (en), Hindi-English (hi), Tamil-English (ta), Bengali-English (bn), Telugu-English (te). All code-mixed text is romanised/transliterated as typed on phones; a fraction is mixed-script.

**Intents (21 subtypes).** Scam: KYC/PAN block, refund or cashback collect-request PIN fraud, lottery/prize, "wrong transfer" refund, task/part-time job, electricity disconnection, customs parcel/FIR threat, fake customer support (AnyDesk/OTP/CVV), instant loan fee, reward-points phishing. Legit: debit alert, credit alert, OTP, genuine collect request, personal chat, security advisory, bill paid. Promo: cashback offer, sale, bank loan promotion, recharge plan, reward points.

**Hard negatives.** Genuine messages deliberately reuse scam vocabulary: OTP messages that say "do not share", advisories mentioning KYC/PIN/link, genuine reward-point expiry reminders, genuine bank pre-approved loan offers, genuine payment requests and "I sent you money" chats. These are the realistic source of false positives.

**Templates.** Each subtype has 3–4 templates written in parallel across all five languages (same intent, same slots), so 315 template-language pairs in total. Slots are filled with realistic values: bank names, UPI apps, UPI IDs (`name1234@ybl`), Indian amounts in six formats (`Rs.1,200`, `₹1,200`, `INR 1200.00`, `Rs.1200/-` …), Indian mobile numbers, 12-digit UPI references, dates, merchants, electricity boards, couriers. Scam links are look-alike domains (`sbi-kyc.xyz`, `refundhdfc.click`) or URL shorteners; legitimate links are official domains (with some shorteners, so a shortener is not a give-away).

**Natural variation (in clean data).** Per-language informal spelling variants (`hai→h`, `karein→kre`, `pannunga→panunga`, `please→plz` …, applied to 35% of eligible tokens), random lower/upper-casing, punctuation drift, generic prefixes/suffixes and spoofable DLT sender headers (`VM-ABCDEF:`) shared by all classes. 15% of messages have native-script words substituted (Devanagari, Tamil, Bengali, Telugu), giving ~9% mixed-script messages.

**Size.** 11,986 messages after de-duplication: legit 5,393, scam 4,199, promo 2,394; ~2,400 per language.

**Template-disjoint split.** For every subtype one template index is held out *in all languages* for the test set; train and validation draw only from the remaining templates (validation = random 15% of the train pool). Test: 3,971; train: 6,813; val: 1,202. Test messages are therefore new phrasings of intents seen only in other wordings — this prevents template memorisation from inflating scores. Consequence: validation is in-template and cannot detect over-fitting to phrasing (relevant to from-scratch neural models).

## 3. Obfuscation scheme (L0–L4)

Each eligible token (not a URL, UPI ID or number) is perturbed with probability *p*; **salient fraud words** (KYC, PIN, OTP, refund, link, block, prize, loan, CVV, update, urgent, the native words for "money"/"immediately" …) are perturbed with probability 2*p* (capped at 0.95), modelling scammers who target filter trigger words. A perturbed token receives 1…max_ops operations sampled from the level's operator set, with operators introduced at that level weighted ×3 (script-mixing ×6 at L4), so each level adds a new family of tricks.

| Level | Name | p | ops/word | Operators |
|---|---|---|---|---|
| L0 | clean | 0 | 0 | – |
| L1 | light | 0.15 | 1 | vowel drop (`updt`), character repeat (`blooock`), case flip (`kYc`), adjacent swap, phonetic respelling (`ph↔f`, `ee↔i`, `w↔v`, `c→k`) |
| L2 | moderate | 0.30 | 1 | + leetspeak (`a→@/4`, `o→0`, `i→1/!`, `s→$/5`), separator insertion (`K.Y.C`, `P-I-N`, `l i n k`) |
| L3 | heavy | 0.45 | 1–2 | + Unicode homoglyphs (Latin→Cyrillic/Greek, e.g. `е` U+0435), zero-width characters (U+200B/C/D, U+2060), random insertion/deletion |
| L4 | cross-script | 0.60 | 1–3 | + script mixing: salient English words rewritten phonetically in the message's Indic script (`account→अकाउंट`, `refund→ரீஃபண்ட்`, `link→লিংক`, `PIN→పిన్`) |

Measured on 1,500 test messages (character edit rate = normalised Levenshtein distance): L1 3.3%, L2 8.3%, L3 11.0%, L4 20.1%; words changed 12%, 35%, 43%, 55%.

**Threat models.** *Targeted*: only scam messages are obfuscated (the attacker controls only scam text; genuine messages stay clean). *Uniform*: every message is obfuscated (a noisy-channel stress test). For a given seed a scam message receives the identical perturbation in both settings, so scam FNR is identical across threat models and the difference in macro-F1 is entirely due to perturbing genuine/promo messages.

**Seeds.** Three obfuscation seeds per (level, threat); results are averaged.

## 4. Models

| Model | Representation | Details |
|---|---|---|
| Word NB | word | bag of word 1–2-grams (counts), Multinomial NB α=0.3 |
| Word RF | word | word 1–2-gram TF-IDF, random forest, 300 trees, balanced |
| Word LR | word | word 1–2-gram TF-IDF (sublinear), logistic regression C=10, balanced |
| Word SVM | word | as above, linear SVM C=0.5 with sigmoid (Platt) calibration, 3-fold |
| Word BiGRU | word | 128-d embeddings, 1-layer BiGRU (128), max+mean pooling, dropout 0.3, trained from scratch |
| Char LR | char | char_wb 2–5-gram TF-IDF (≤200k features), logistic regression C=10 |
| Char SVM | char | char_wb 2–5-gram TF-IDF, calibrated linear SVM |
| Char CNN | char | 64-d char embeddings, parallel conv 3/5/7 (128 filters), pool, conv 256, global max pool; from scratch |
| DistilmBERT | subword (WordPiece) | distilbert-base-multilingual-cased, fine-tuned |
| XLM-R | subword (SentencePiece) | xlm-roberta-base, fine-tuned |
| MuRIL | subword | google/muril-base-cased (Indian languages + transliterated), fine-tuned |
| CANINE-S | character (tokenizer-free) | google/canine-s, fine-tuned |

Neural from-scratch models: AdamW lr 2e-3, batch 64, up to 12 epochs with early stopping on validation macro-F1 (patience 3), class-weighted cross-entropy, 3 training seeds. Transformers: AdamW (lr 5e-5 DistilmBERT/CANINE, 3e-5 XLM-R/MuRIL), linear warm-up 10%, 1 epoch, batch 16, max 96 subword tokens (320 characters for CANINE), class-weighted loss, length-bucketed batches; because of CPU compute, fine-tuned on a stratified 50% subset of the training set (every template × language kept) and evaluated on obfuscation seed 0. For XLM-R and MuRIL (250k/197k-token vocabularies) the input word-embedding matrix is frozen so optimiser state fits in 8 GB RAM. Transformer coverage in the shipped results: DistilmBERT (standard + adversarial training, cross-lingual matrix), CANINE-S, XLM-R and MuRIL (standard training). `scripts/run_all.sh` runs the full grid on a faster machine.

**Training regimes.** *Standard*: clean training data. *Adversarial training (AT)*: each training message is replaced, with probability 0.5, by an obfuscated copy at a level drawn uniformly from {L1, L2, L3}; L4 cross-script is never seen, so L4 measures generalisation to an unseen attack family. *Canonicalisation defence (+norm)*: train and test text passed through a generic normaliser — Unicode NFKC, zero-width removal, homoglyph→Latin folding, removal of separators inside words, leetspeak undoing inside alphabetic tokens, squeezing of 3+ repeated letters, lower-casing. The normaliser has no access to the script-mixing lexicon.

## 5. Metrics

- **Macro-F1** over the three classes (primary).
- **Scam false-negative rate** = scams predicted as legit/promo ÷ scams (the costliest error). Scam false-positive rate also reported.
- **Expected calibration error** (top-label, 15 equal-width bins).
- **Latency**: median and p95 single-message CPU latency over 200 messages after 10 warm-up calls, plus batch throughput; 2-core Intel Xeon 2.8 GHz, PyTorch 2.x CPU.
- **Uncertainty**: 95% bootstrap CIs (500 resamples) for clean macro-F1; mean ± std across obfuscation seeds (and training seeds for neural models).
- **Hypothesis test for RQ2**: paired bootstrap (1,000 resamples of test messages) on the difference in *degradation*, Δdrop = [F1(A,L0) − F1(A,Lk)] − [F1(B,L0) − F1(B,Lk)] for character model A vs word/subword model B; one-sided p for H1: A degrades less. McNemar exact test on attacked predictions as a secondary test.

## 6. Experiments

- **E1** Robustness curves L0–L4 under both threat models (all models).
- **E2** Cross-lingual transfer (word/char LR, SVM, BiGRU, CNN, DistilmBERT): train on a single language's training data (~1,300 messages), test on each language's test messages, clean and L2-targeted; reports in-language (diagonal) vs cross-language (off-diagonal) macro-F1.
- **E3** Adversarial training vs standard training, including the unseen L4.
- **E4** Canonicalisation defence vs adversarial training (classical + neural).
- **E5** Latency and model size.
- **E6** Cue ablation: URLs, UPI IDs, phone numbers, amounts, sender headers and remaining digits replaced by placeholders in train and test, to measure reliance on non-linguistic cues.

## 7. Limitations to state in the paper

- The corpus is synthetic and template-based; absolute scores do not transfer to real SMS traffic, though the controlled design isolates the effect of obfuscation.
- Transliteration conventions are one plausible romanisation per language; real users vary more.
- Transformers were fine-tuned for one epoch on half the training set on CPU, so their absolute numbers are conservative.
- Validation is in-template, so early stopping cannot detect phrase over-fitting; from-scratch neural models are therefore weak on the template-disjoint test set.
- The obfuscator is random, not an optimising adversary; a gradient- or query-based attacker would be stronger.
