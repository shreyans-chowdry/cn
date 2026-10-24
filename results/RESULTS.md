# Results

All numbers on the template-disjoint test set (n = 3939). Obfuscated conditions are averaged over obfuscation seeds; from-scratch neural models are additionally averaged over training seeds (mean ± std).

## Obfuscation scheme statistics

| Level | Word perturb prob. | Words changed | Char edit rate | Char edit rate after canonicalisation | Top ops |
|---|---|---|---|---|---|
| L1 (light) | 0.15 | 0.128 | 0.028 | 0.021 | phonetic, case, vowel_drop, repeat |
| L2 (moderate) | 0.3 | 0.393 | 0.078 | 0.034 | separator, leet, phonetic, case |
| L3 (heavy) | 0.45 | 0.463 | 0.117 | 0.054 | zero_width, delete, insert, homoglyph |
| L4 (cross-script) | 0.6 | 0.587 | 0.274 | 0.154 | to_native, translit, separator, zero_width |

## Table 1 — Clean test performance (no obfuscation)

| Model | Repr. | Macro-F1 | 95% CI (seed 0) | Scam FNR | Scam FPR | ECE | Latency ms (p50) | Size |
|---|---|---|---|---|---|---|---|---|
| Word NB | word | 0.845 | [0.834, 0.857] | 0.114 | 0.142 | 0.137 | 0.64 | 8.9k features |
| Word RF | word | 0.731 | [0.717, 0.746] | 0.348 | 0.142 | 0.147 | 98.12 | 8.9k features |
| Word LR | word | 0.835 | [0.822, 0.848] | 0.118 | 0.178 | 0.071 | 1.35 | 8.9k features |
| Word SVM | word | 0.807 | [0.794, 0.820] | 0.117 | 0.220 | 0.080 | 4.39 | 8.9k features |
| Word BiGRU | word | 0.688 ± 0.052 | [0.629, 0.663] | 0.248 | 0.172 | 0.211 | 2.71 | 0.5M params |
| DistilmBERT | subword | 0.709 | [0.694, 0.725] | 0.005 | 0.254 | 0.229 | - | - |
| Char LR | char | 0.784 | [0.770, 0.797] | 0.101 | 0.287 | 0.066 | 1.46 | 45.9k features |
| Char SVM | char | 0.771 | [0.757, 0.784] | 0.105 | 0.293 | 0.126 | 4.99 | 45.9k features |
| Char CNN | char | 0.581 ± 0.051 | [0.620, 0.650] | 0.313 | 0.398 | 0.295 | 2.33 | 0.4M params |

## Macro-F1 vs. obfuscation level — targeted threat model (clean training)

| Model | Repr. | L0 | L1 | L2 | L3 | L4 | Mean L0-L4 | Drop L0→L3 | Drop L0→L4 |
|---|---|---|---|---|---|---|---|---|---|
| Word NB | word | 0.845 | 0.843 ± 0.001 | 0.816 ± 0.003 | 0.803 ± 0.003 | 0.789 ± 0.002 | 0.819 | 0.041 | 0.056 |
| Word RF | word | 0.731 | 0.716 ± 0.002 | 0.666 ± 0.002 | 0.683 ± 0.002 | 0.688 ± 0.003 | 0.697 | 0.048 | 0.043 |
| Word LR | word | 0.835 | 0.829 ± 0.002 | 0.795 ± 0.003 | 0.796 ± 0.002 | 0.779 ± 0.002 | 0.807 | 0.038 | 0.055 |
| Word SVM | word | 0.807 | 0.803 ± 0.001 | 0.771 ± 0.000 | 0.771 ± 0.002 | 0.751 ± 0.001 | 0.781 | 0.035 | 0.056 |
| Word BiGRU | word | 0.688 | 0.676 ± 0.042 | 0.630 ± 0.042 | 0.615 ± 0.059 | 0.600 ± 0.072 | 0.642 | 0.073 | 0.088 |
| DistilmBERT | subword | 0.709 | 0.705 | 0.703 | 0.699 | 0.694 | 0.702 | 0.010 | 0.015 |
| Char LR | char | 0.784 | 0.784 ± 0.001 | 0.780 ± 0.001 | 0.779 ± 0.001 | 0.756 ± 0.001 | 0.777 | 0.005 | 0.028 |
| Char SVM | char | 0.771 | 0.771 ± 0.001 | 0.767 ± 0.001 | 0.765 ± 0.002 | 0.742 ± 0.001 | 0.763 | 0.006 | 0.029 |
| Char CNN | char | 0.581 | 0.582 ± 0.043 | 0.579 ± 0.043 | 0.574 ± 0.046 | 0.562 ± 0.037 | 0.576 | 0.007 | 0.019 |

## Macro-F1 vs. obfuscation level — uniform threat model (clean training)

| Model | Repr. | L0 | L1 | L2 | L3 | L4 | Mean L0-L4 | Drop L0→L3 | Drop L0→L4 |
|---|---|---|---|---|---|---|---|---|---|
| Word NB | word | 0.845 | 0.827 ± 0.004 | 0.776 ± 0.004 | 0.746 ± 0.003 | 0.729 ± 0.003 | 0.784 | 0.099 | 0.116 |
| Word RF | word | 0.731 | 0.684 ± 0.001 | 0.581 ± 0.002 | 0.538 ± 0.010 | 0.477 ± 0.010 | 0.602 | 0.193 | 0.254 |
| Word LR | word | 0.835 | 0.813 ± 0.001 | 0.753 ± 0.007 | 0.730 ± 0.004 | 0.692 ± 0.004 | 0.764 | 0.105 | 0.143 |
| Word SVM | word | 0.807 | 0.781 ± 0.002 | 0.729 ± 0.002 | 0.700 ± 0.000 | 0.678 ± 0.002 | 0.739 | 0.107 | 0.129 |
| Word BiGRU | word | 0.688 | 0.630 ± 0.046 | 0.480 ± 0.064 | 0.407 ± 0.056 | 0.374 ± 0.058 | 0.516 | 0.280 | 0.314 |
| DistilmBERT | subword | 0.709 | 0.680 | 0.584 | 0.601 | 0.560 | 0.627 | 0.108 | 0.149 |
| Char LR | char | 0.784 | 0.776 ± 0.001 | 0.752 ± 0.003 | 0.731 ± 0.002 | 0.687 ± 0.008 | 0.746 | 0.053 | 0.097 |
| Char SVM | char | 0.771 | 0.763 ± 0.002 | 0.739 ± 0.006 | 0.715 ± 0.003 | 0.689 ± 0.008 | 0.735 | 0.055 | 0.081 |
| Char CNN | char | 0.581 | 0.569 ± 0.041 | 0.546 ± 0.041 | 0.533 ± 0.046 | 0.514 ± 0.046 | 0.548 | 0.048 | 0.067 |

## Scam false-negative rate vs. obfuscation level — targeted threat model (clean training)

| Model | Repr. | L0 | L1 | L2 | L3 | L4 |
|---|---|---|---|---|---|---|
| Word NB | word | 0.114 | 0.117 ± 0.002 | 0.184 ± 0.009 | 0.212 ± 0.008 | 0.251 ± 0.002 |
| Word RF | word | 0.348 | 0.391 ± 0.005 | 0.535 ± 0.005 | 0.488 ± 0.005 | 0.474 ± 0.010 |
| Word LR | word | 0.118 | 0.134 ± 0.006 | 0.240 ± 0.009 | 0.228 ± 0.005 | 0.279 ± 0.006 |
| Word SVM | word | 0.117 | 0.127 ± 0.003 | 0.230 ± 0.001 | 0.222 ± 0.004 | 0.285 ± 0.004 |
| Word BiGRU | word | 0.248 | 0.283 ± 0.166 | 0.449 ± 0.234 | 0.476 ± 0.308 | 0.510 ± 0.335 |
| DistilmBERT | subword | 0.005 | 0.015 | 0.023 | 0.038 | 0.058 |
| Char LR | char | 0.101 | 0.101 ± 0.003 | 0.113 ± 0.004 | 0.117 ± 0.003 | 0.189 ± 0.002 |
| Char SVM | char | 0.105 | 0.105 ± 0.004 | 0.116 ± 0.004 | 0.124 ± 0.006 | 0.197 ± 0.003 |
| Char CNN | char | 0.313 | 0.311 ± 0.033 | 0.324 ± 0.034 | 0.346 ± 0.021 | 0.387 ± 0.040 |

## Scam false-positive rate (genuine/promo flagged as scam) vs. obfuscation level — uniform threat model (clean training)

| Model | Repr. | L0 | L1 | L2 | L3 | L4 |
|---|---|---|---|---|---|---|
| Word NB | word | 0.142 | 0.132 ± 0.001 | 0.116 ± 0.002 | 0.120 ± 0.007 | 0.123 ± 0.006 |
| Word RF | word | 0.142 | 0.137 ± 0.004 | 0.121 ± 0.003 | 0.164 ± 0.006 | 0.237 ± 0.004 |
| Word LR | word | 0.178 | 0.170 ± 0.005 | 0.140 ± 0.003 | 0.156 ± 0.001 | 0.163 ± 0.002 |
| Word SVM | word | 0.220 | 0.209 ± 0.003 | 0.165 ± 0.003 | 0.178 ± 0.005 | 0.167 ± 0.002 |
| Word BiGRU | word | 0.172 | 0.185 ± 0.141 | 0.175 ± 0.188 | 0.216 ± 0.255 | 0.223 ± 0.275 |
| DistilmBERT | subword | 0.254 | 0.261 | 0.410 | 0.336 | 0.353 |
| Char LR | char | 0.287 | 0.287 ± 0.002 | 0.268 ± 0.004 | 0.267 ± 0.002 | 0.238 ± 0.005 |
| Char SVM | char | 0.293 | 0.297 ± 0.003 | 0.284 ± 0.007 | 0.280 ± 0.002 | 0.247 ± 0.003 |
| Char CNN | char | 0.398 | 0.405 ± 0.097 | 0.384 ± 0.086 | 0.364 ± 0.077 | 0.316 ± 0.077 |

## Expected calibration error vs. obfuscation level — targeted threat model (clean training)

| Model | Repr. | L0 | L1 | L2 | L3 | L4 |
|---|---|---|---|---|---|---|
| Word NB | word | 0.137 | 0.137 ± 0.001 | 0.157 ± 0.004 | 0.162 ± 0.002 | 0.171 ± 0.002 |
| Word RF | word | 0.147 | 0.130 ± 0.001 | 0.087 ± 0.001 | 0.101 ± 0.003 | 0.106 ± 0.002 |
| Word LR | word | 0.071 | 0.053 ± 0.004 | 0.032 ± 0.005 | 0.036 ± 0.003 | 0.035 ± 0.003 |
| Word SVM | word | 0.080 | 0.075 ± 0.002 | 0.097 ± 0.002 | 0.089 ± 0.002 | 0.103 ± 0.001 |
| Word BiGRU | word | 0.211 | 0.223 ± 0.050 | 0.270 ± 0.041 | 0.280 ± 0.051 | 0.294 ± 0.063 |
| DistilmBERT | subword | 0.229 | 0.232 | 0.233 | 0.236 | 0.242 |
| Char LR | char | 0.066 | 0.058 ± 0.002 | 0.043 ± 0.003 | 0.036 ± 0.005 | 0.037 ± 0.005 |
| Char SVM | char | 0.126 | 0.124 ± 0.001 | 0.119 ± 0.000 | 0.117 ± 0.003 | 0.125 ± 0.001 |
| Char CNN | char | 0.295 | 0.293 ± 0.041 | 0.293 ± 0.040 | 0.299 ± 0.044 | 0.308 ± 0.044 |

## Expected calibration error vs. obfuscation level — uniform threat model (clean training)

| Model | Repr. | L0 | L1 | L2 | L3 | L4 |
|---|---|---|---|---|---|---|
| Word NB | word | 0.137 | 0.147 ± 0.002 | 0.185 ± 0.007 | 0.199 ± 0.004 | 0.209 ± 0.004 |
| Word RF | word | 0.147 | 0.114 ± 0.001 | 0.045 ± 0.003 | 0.045 ± 0.011 | 0.055 ± 0.000 |
| Word LR | word | 0.071 | 0.046 ± 0.004 | 0.022 ± 0.006 | 0.023 ± 0.004 | 0.019 ± 0.002 |
| Word SVM | word | 0.080 | 0.085 ± 0.001 | 0.116 ± 0.004 | 0.123 ± 0.003 | 0.132 ± 0.002 |
| Word BiGRU | word | 0.211 | 0.246 ± 0.056 | 0.355 ± 0.052 | 0.389 ± 0.042 | 0.412 ± 0.048 |
| DistilmBERT | subword | 0.229 | 0.243 | 0.321 | 0.295 | 0.314 |
| Char LR | char | 0.066 | 0.054 ± 0.002 | 0.041 ± 0.002 | 0.047 ± 0.003 | 0.030 ± 0.004 |
| Char SVM | char | 0.126 | 0.126 ± 0.000 | 0.120 ± 0.007 | 0.125 ± 0.001 | 0.120 ± 0.004 |
| Char CNN | char | 0.295 | 0.298 ± 0.039 | 0.296 ± 0.036 | 0.292 ± 0.040 | 0.290 ± 0.039 |

## Hypothesis test — do character-level models degrade less than word/subword models?

Paired bootstrap (1000 resamples) over test messages on the *drop* in macro-F1 from L0 to the attacked condition. Negative Δdrop means the character model loses less. One-sided p-value for H1: A degrades less than B.

| A (char) | B (word/subword) | threat | level | drop A | drop B | Δdrop (A−B) | 95% CI | p (A degrades less) | McNemar p (attacked) |
|---|---|---|---|---|---|---|---|---|---|
| Char LR | Word LR | targeted | L3 | 0.006 | 0.0392 | -0.0334 | [-0.040, -0.026] | 0.0 | 7.90e-04 |
| Char LR | Word LR | targeted | L4 | 0.027 | 0.0532 | -0.0262 | [-0.034, -0.019] | 0.0 | 2.01e-06 |
| Char LR | Word LR | uniform | L3 | 0.0511 | 0.1044 | -0.0536 | [-0.068, -0.039] | 0.0 | 4.47e-01 |
| Char LR | Word LR | uniform | L4 | 0.0927 | 0.1413 | -0.0485 | [-0.064, -0.033] | 0.0 | 2.87e-01 |
| Char SVM | Word SVM | targeted | L3 | 0.0081 | 0.036 | -0.028 | [-0.034, -0.021] | 0.0 | 1.20e-01 |
| Char SVM | Word SVM | targeted | L4 | 0.0278 | 0.0547 | -0.0267 | [-0.034, -0.020] | 0.0 | 7.02e-02 |
| Char SVM | Word SVM | uniform | L3 | 0.0547 | 0.1068 | -0.0524 | [-0.066, -0.038] | 0.0 | 1.27e-01 |
| Char SVM | Word SVM | uniform | L4 | 0.0728 | 0.1269 | -0.0541 | [-0.069, -0.040] | 0.0 | 1.46e-02 |
| Char CNN | Word BiGRU | targeted | L3 | 0.0036 | -0.0336 | 0.0368 | [0.026, 0.047] | 1.0 | 1.16e-08 |
| Char CNN | Word BiGRU | targeted | L4 | 0.0291 | -0.0368 | 0.0661 | [0.054, 0.078] | 1.0 | 6.09e-17 |
| Char CNN | Word BiGRU | uniform | L3 | 0.0503 | 0.2034 | -0.1533 | [-0.178, -0.128] | 0.0 | 4.03e-09 |
| Char CNN | Word BiGRU | uniform | L4 | 0.073 | 0.2349 | -0.1617 | [-0.189, -0.134] | 0.0 | 3.39e-08 |

## Adversarial training (train on 50% L1–L3 obfuscated copies; L4 cross-script transliteration never seen) — targeted threat

| Model | Repr. | F1 L0 (std) | F1 L3 (std) | F1 L4 (std) | FNR L3 (std) | F1 L0 (AT) | F1 L3 (AT) | F1 L4 (AT) | FNR L3 (AT) |
|---|---|---|---|---|---|---|---|---|---|
| Word NB | word | 0.845 | 0.803 | 0.789 | 0.212 | 0.837 | 0.824 | 0.813 | 0.144 |
| Word RF | word | 0.731 | 0.683 | 0.688 | 0.488 | 0.801 | 0.788 | 0.778 | 0.338 |
| Word LR | word | 0.835 | 0.796 | 0.779 | 0.228 | 0.829 | 0.821 | 0.809 | 0.143 |
| Word SVM | word | 0.807 | 0.771 | 0.751 | 0.222 | 0.823 | 0.818 | 0.806 | 0.147 |
| Word BiGRU | word | 0.688 | 0.615 | 0.600 | 0.476 | 0.752 | 0.703 | 0.703 | 0.361 |
| DistilmBERT | subword | 0.709 | 0.699 | 0.694 | 0.038 | 0.744 | 0.736 | 0.734 | 0.035 |
| Char LR | char | 0.784 | 0.779 | 0.756 | 0.117 | 0.787 | 0.788 | 0.777 | 0.098 |
| Char SVM | char | 0.771 | 0.765 | 0.742 | 0.124 | 0.777 | 0.779 | 0.772 | 0.094 |
| Char CNN | char | 0.581 | 0.574 | 0.562 | 0.346 | 0.597 | 0.589 | 0.581 | 0.440 |

## Script-aware canonicalisation defence (NFKC, homoglyph and native look-alike folding, zero-width stripping, de-leet, native-script loanwords to English) vs adversarial training — macro-F1, targeted

| Model | L0 std | L0 +norm | L0 AT | L1 std | L1 +norm | L1 AT | L2 std | L2 +norm | L2 AT | L3 std | L3 +norm | L3 AT | L4 std | L4 +norm | L4 AT |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Word NB | 0.845 | 0.864 | 0.837 | 0.843 | 0.863 | 0.838 | 0.816 | 0.860 | 0.839 | 0.803 | 0.856 | 0.824 | 0.789 | 0.844 | 0.813 |
| Word RF | 0.731 | 0.713 | 0.801 | 0.716 | 0.700 | 0.796 | 0.666 | 0.695 | 0.809 | 0.683 | 0.691 | 0.788 | 0.688 | 0.689 | 0.778 |
| Word LR | 0.835 | 0.849 | 0.829 | 0.829 | 0.845 | 0.826 | 0.795 | 0.841 | 0.823 | 0.796 | 0.839 | 0.821 | 0.779 | 0.821 | 0.809 |
| Word SVM | 0.807 | 0.845 | 0.823 | 0.803 | 0.842 | 0.824 | 0.771 | 0.839 | 0.825 | 0.771 | 0.835 | 0.818 | 0.751 | 0.822 | 0.806 |
| Word BiGRU | 0.688 | 0.693 | 0.752 | 0.676 | 0.684 | 0.746 | 0.630 | 0.684 | 0.721 | 0.615 | 0.672 | 0.703 | 0.600 | 0.655 | 0.703 |
| Char LR | 0.784 | 0.794 | 0.787 | 0.784 | 0.794 | 0.787 | 0.780 | 0.794 | 0.788 | 0.779 | 0.794 | 0.788 | 0.756 | 0.780 | 0.777 |
| Char SVM | 0.771 | 0.787 | 0.777 | 0.771 | 0.787 | 0.778 | 0.767 | 0.786 | 0.779 | 0.765 | 0.787 | 0.779 | 0.742 | 0.770 | 0.772 |
| Char CNN | 0.581 | 0.624 | 0.597 | 0.582 | 0.623 | 0.596 | 0.579 | 0.620 | 0.586 | 0.574 | 0.618 | 0.589 | 0.562 | 0.615 | 0.581 |

## Per-language macro-F1, clean (L0) vs heavy targeted obfuscation (L3)

Languages: en = English, hi = Hindi–English, ta = Tamil–English

| Model | en L0 | en L3 | hi L0 | hi L3 | ta L0 | ta L3 |
|---|---|---|---|---|---|---|
| Word NB | 0.886 | 0.830 | 0.770 | 0.761 | 0.874 | 0.814 |
| Word RF | 0.777 | 0.711 | 0.712 | 0.655 | 0.701 | 0.680 |
| Word LR | 0.867 | 0.829 | 0.784 | 0.757 | 0.850 | 0.800 |
| Word SVM | 0.840 | 0.812 | 0.764 | 0.734 | 0.813 | 0.765 |
| Word BiGRU | 0.681 | 0.708 | 0.608 | 0.657 | 0.644 | 0.680 |
| DistilmBERT | 0.734 | 0.713 | 0.676 | 0.673 | 0.715 | 0.709 |
| Char LR | 0.807 | 0.804 | 0.773 | 0.765 | 0.769 | 0.765 |
| Char SVM | 0.778 | 0.777 | 0.780 | 0.765 | 0.751 | 0.748 |
| Char CNN | 0.702 | 0.699 | 0.588 | 0.586 | 0.611 | 0.608 |

## Cross-language transfer (train on one language only, test on every language; clean and L2 targeted)

| Model | Repr. | In-language F1 | Cross-language F1 | Transfer gap | In-language F1 @L2 | Cross-language F1 @L2 |
|---|---|---|---|---|---|---|
| Word LR | word | 0.831 | 0.716 | 0.115 | 0.797 | 0.672 |
| Word SVM | word | 0.800 | 0.688 | 0.112 | 0.767 | 0.641 |
| Word BiGRU | word | 0.637 | 0.337 | 0.301 | 0.511 | 0.290 |
| Char LR | char | 0.790 | 0.741 | 0.049 | 0.790 | 0.721 |
| Char SVM | char | 0.772 | 0.739 | 0.034 | 0.769 | 0.718 |
| Char CNN | char | 0.598 | 0.520 | 0.079 | 0.582 | 0.504 |

## Cue ablation — URLs, UPI IDs, phone numbers, amounts and numbers replaced by placeholders (train and test), targeted threat

Shows how much each model relies on non-linguistic cues rather than the code-mixed text itself.

| Model | Repr. | F1 L0 (full) | F1 L0 (cues masked) | Δ L0 | F1 L3 (full) | F1 L3 (masked) | FNR L3 (masked) |
|---|---|---|---|---|---|---|---|
| Word NB | word | 0.845 | 0.836 | -0.009 | 0.803 | 0.767 | 0.233 |
| Word RF | word | 0.731 | 0.728 | -0.003 | 0.683 | 0.652 | 0.406 |
| Word LR | word | 0.835 | 0.822 | -0.012 | 0.796 | 0.772 | 0.227 |
| Word SVM | word | 0.807 | 0.789 | -0.017 | 0.771 | 0.743 | 0.233 |
| Word BiGRU | word | 0.688 | 0.781 | +0.093 | 0.615 | 0.699 | 0.323 |
| Char LR | char | 0.784 | 0.790 | +0.006 | 0.779 | 0.765 | 0.165 |
| Char SVM | char | 0.771 | 0.762 | -0.008 | 0.765 | 0.746 | 0.145 |
| Char CNN | char | 0.581 | 0.602 | +0.021 | 0.574 | 0.562 | 0.337 |

## Inference latency (CPU, 2 cores, batch size 1 unless stated)

| Model | Repr. | p50 ms | p95 ms | Batch throughput (msg/s) | Size |
|---|---|---|---|---|---|
| Word NB | word | 0.64 | 0.77 | 29237 | 8.9k features |
| Word RF | word | 98.12 | 122.16 | 1878 | 8.9k features |
| Word LR | word | 1.35 | 1.64 | 16320 | 8.9k features |
| Word SVM | word | 4.39 | 7.39 | 10650 | 8.9k features |
| Word BiGRU | word | 2.71 | 3.84 | 1898 | 0.5M params |
| Char LR | char | 1.46 | 2.20 | 3117 | 45.9k features |
| Char SVM | char | 4.99 | 7.59 | 3074 | 45.9k features |
| Char CNN | char | 2.33 | 4.89 | 699 | 0.4M params |
