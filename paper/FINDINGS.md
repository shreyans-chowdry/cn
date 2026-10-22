# Key findings (draft material for the Results and Discussion sections)

All numbers are macro-F1 on the template-disjoint test set (n = 3,971) unless stated. Full tables are in `results/RESULTS.md`; CSVs in `results/tables/`, figures in `results/figures/`.

## 1. Clean performance
- **XLM-R is the best clean model** (macro-F1 0.838, scam FNR 0.052, the lowest scam false-positive rate at 0.141). Character n-gram logistic regression is next (0.812) and is about 70 times faster (1.0 ms against 73 ms per message on CPU).
- Hard negatives dominate the errors. Every model wrongly flags 14–31% of genuine and promotional messages as scams (scam FPR) (genuine KYC/OTP advisories and bank loan offers share the scam vocabulary).
- Neural models trained from scratch (word BiGRU 0.668, char CNN 0.673) generalise poorly to unseen phrasings. Their in-template validation F1 is ≈1.0, which shows they over-fit to template wording.

## 2. Robustness to obfuscation (RQ1)
- Under the **targeted** threat (only scam text is obfuscated), every model degrades except DistilmBERT. Going from L0 to L4, word models lose 0.07–0.16, XLM-R loses 0.12, and the character models lose 0.06–0.07.
- **Scam false-negative rate rises steeply.** For Word LR it goes from 0.08 to 0.30. For the BiGRU it goes from 0.19 to 0.69. For XLM-R it goes from 0.05 to 0.44, so XLM-R is the best clean model but misses 44% of cross-script scams.
- **Cross-script rewriting (L4) is the strongest attack** for most models. Subword transformers and the char-n-gram models drop most sharply there.
- **DistilmBERT behaves unusually: it treats obfuscation itself as a scam signal.** Its scam FNR stays around 0.07–0.09 at every level. Under the uniform threat, though, its scam false-positive rate climbs from 0.25 to 0.41, because obfuscated genuine messages are also called scams. Its flat targeted curve therefore does not mean it is robust. Every other model moves the opposite way (obfuscated text looks *less* like a scam to them).

## 3. Character vs word representations (RQ2: the hypothesis)
- **The hypothesis is supported in 20 of the 24 paired tests.** In those, the character model degrades significantly less than its word or subword counterpart (paired bootstrap, p < 0.001). The comparisons are Char LR vs Word LR, Char SVM vs Word SVM, Char CNN vs BiGRU, CANINE vs DistilmBERT, CANINE vs XLM-R and Char LR vs XLM-R, at L3 and L4 under both threats.
- The largest effect is Char CNN vs Word BiGRU: under uniform L3 the drop is 0.036 against 0.229 (Δ = −0.19).
- **There are 4 exceptions, and they are informative:**
  - Char LR vs Word LR (Δ = −0.003, p = 0.21) and Char SVM vs Word SVM (Δ = +0.008, p = 0.97), both under targeted L4. Cross-script rewriting replaces whole words with characters the n-gram model never saw, so the advantage of character features disappears.
  - CANINE vs DistilmBERT under targeted L3 and L4. This only reflects DistilmBERT's "obfuscation means scam" bias (section 2). Under the uniform threat CANINE degrades far less (Δ = −0.07 at L3 and −0.11 at L4).
- Conclusion for the paper: character-level representations are more resistant to *character-level* perturbations (L1–L3). The protection weakens against *script-level* substitution (L4).

## 4. Cross-lingual transfer (RQ3)
- **Linear models transfer almost perfectly** between language pairs. For Char LR, in-language F1 is 0.789 and cross-language F1 is 0.809. Payment vocabulary in code-mixed SMS is largely English (KYC, PIN, link, refund, account), so a model trained on Hinglish already knows the key cues for Tanglish.
- **Neural models do not transfer.** For the word BiGRU, in-language F1 is 0.61 and cross-language F1 is 0.48. For DistilmBERT trained on ~700 messages of one language, the figures are 0.59 and 0.53.
- After L2 obfuscation, the character models keep their cross-language advantage (0.783 against 0.710 for Word LR).

## 5. Adversarial training (RQ4)
- Adversarial training (50% L1–L3 copies) **cuts scam FNR at L3 by roughly 20–65%** for classical and neural models: Word LR goes from 0.28 to 0.17, the BiGRU from 0.64 to 0.22, Char SVM from 0.28 to 0.17.
- **It generalises to the unseen L4 attack.** Word LR improves from 0.703 to 0.735 at L4, the BiGRU from 0.513 to 0.673, Char LR from 0.749 to 0.774.
- **It has a clean-accuracy cost** for the strong linear models: Word SVM drops from 0.788 to 0.751 and Char SVM from 0.807 to 0.783.
- For DistilmBERT, adversarial training *raises* scam FNR (0.07 to 0.15) and lowers clean F1. The model unlearns its "noise means scam" shortcut.

## 6. Canonicalisation defence
- A simple normaliser (NFKC, zero-width removal, homoglyph folding, de-leet) with no knowledge of the attack lexicon **matches or beats adversarial training for linear models at no clean-accuracy cost**. Word LR at L3 scores 0.761 with the normaliser against 0.734 with adversarial training. Char LR scores 0.805 against 0.785 at L3, and 0.784 against 0.774 at L4.
- The best robust configuration overall is **Char LR + canonicalisation**: 0.824 clean and 0.784 at L4, in about 1 ms per message.

## 7. Calibration and latency (RQ5)
- Char LR is the best-calibrated model (ECE 0.035). The transformers and from-scratch neural models have ECE between 0.12 and 0.32 and are overconfident.
- Latency on 2 CPU cores, median per message: linear models 0.5–4 ms, Char CNN 1.3 ms, DistilmBERT 37 ms, XLM-R and MuRIL 73 ms, CANINE 100 ms. All of them are fast enough for on-device SMS filtering, but only the linear models suit high-throughput gateway filtering.

## 8. Cue ablation
- Masking URLs, phone numbers, UPI IDs and amounts changes clean F1 by at most 0.065 (two models are unchanged), so most of the signal is in the code-mixed language itself and not in the links. Character models lose the most (Char SVM −0.065), because they also read the character patterns of look-alike domains.

## Suggested one-line conclusion
Character-level representations are significantly more robust to character-level obfuscation than word-level and subword representations, but not to cross-script substitution. Of the defences tested, a cheap canonicalisation step in front of a character n-gram model gives the best mix of robustness, calibration and latency.
