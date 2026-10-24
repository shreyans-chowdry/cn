# Results

All numbers on the template-disjoint test set (n = 3240). Obfuscated conditions are averaged over obfuscation seeds; from-scratch neural models are additionally averaged over training seeds (mean ± std).

## Obfuscation scheme statistics

| Level | Word perturb prob. | Words changed | Char edit rate | Char edit rate after canonicalisation | Top ops |
|---|---|---|---|---|---|
| L1 (light) | 0.15 | 0.133 | 0.028 | 0.019 | phonetic, repeat, case, vowel_drop |
| L2 (moderate) | 0.3 | 0.372 | 0.079 | 0.032 | separator, leet, swap, case |
| L3 (heavy) | 0.45 | 0.466 | 0.116 | 0.053 | zero_width, insert, homoglyph, delete |
| L4 (cross-script) | 0.6 | 0.583 | 0.256 | 0.134 | to_tamil, translit, zero_width, separator |

## Table 1 — Clean test performance (no obfuscation)

| Model | Repr. | Macro-F1 | 95% CI (seed 0) | Scam FNR | Scam FPR | ECE | Latency ms (p50) | Size |
|---|---|---|---|---|---|---|---|---|
| Word NB | word | 0.794 | [0.780, 0.809] | 0.139 | 0.137 | 0.184 | 0.42 | 7.2k features |
| Word RF | word | 0.707 | [0.689, 0.724] | 0.055 | 0.319 | 0.150 | 58.36 | 7.2k features |
| Word LR | word | 0.785 | [0.770, 0.798] | 0.129 | 0.199 | 0.059 | 0.62 | 7.2k features |
| Word SVM | word | 0.782 | [0.767, 0.797] | 0.080 | 0.206 | 0.097 | 2.84 | 7.2k features |
| Word BiGRU | word | 0.574 ± 0.093 | [0.657, 0.692] | 0.144 | 0.392 | 0.268 | 2.23 | 0.4M params |
| DistilmBERT | subword | 0.778 | [0.761, 0.794] | 0.045 | 0.191 | 0.161 | 58.57 | 135.3M params |
| XLM-R | subword | 0.851 | [0.839, 0.863] | 0.074 | 0.209 | 0.150 | 149.50 | 278.0M params |
| MuRIL | subword | 0.749 | [0.734, 0.763] | 0.077 | 0.375 | 0.118 | 114.97 | 237.6M params |
| Char LR | char | 0.777 | [0.761, 0.791] | 0.132 | 0.243 | 0.046 | 0.83 | 38.6k features |
| Char SVM | char | 0.772 | [0.756, 0.787] | 0.120 | 0.256 | 0.082 | 3.17 | 38.6k features |
| Char CNN | char | 0.660 ± 0.009 | [0.634, 0.666] | 0.437 | 0.126 | 0.195 | 0.97 | 0.4M params |
| CANINE-S | char | 0.778 | [0.762, 0.793] | 0.123 | 0.236 | 0.188 | 154.77 | 132.1M params |

## Macro-F1 vs. obfuscation level — targeted threat model (clean training)

| Model | Repr. | L0 | L1 | L2 | L3 | L4 | Mean L0-L4 | Drop L0→L3 | Drop L0→L4 |
|---|---|---|---|---|---|---|---|---|---|
| Word NB | word | 0.794 | 0.800 ± 0.004 | 0.784 ± 0.004 | 0.770 ± 0.005 | 0.752 ± 0.002 | 0.780 | 0.025 | 0.042 |
| Word RF | word | 0.707 | 0.704 ± 0.001 | 0.671 ± 0.004 | 0.679 ± 0.004 | 0.681 ± 0.003 | 0.689 | 0.028 | 0.026 |
| Word LR | word | 0.785 | 0.792 ± 0.001 | 0.767 ± 0.002 | 0.770 ± 0.004 | 0.758 ± 0.002 | 0.774 | 0.014 | 0.026 |
| Word SVM | word | 0.782 | 0.787 ± 0.004 | 0.763 ± 0.003 | 0.765 ± 0.005 | 0.744 ± 0.001 | 0.768 | 0.017 | 0.037 |
| Word BiGRU | word | 0.574 | 0.578 ± 0.083 | 0.539 ± 0.057 | 0.565 ± 0.078 | 0.546 ± 0.082 | 0.560 | 0.010 | 0.028 |
| DistilmBERT | subword | 0.778 | 0.778 | 0.791 | 0.783 | 0.782 | 0.782 | -0.005 | -0.004 |
| XLM-R | subword | 0.851 | 0.860 ± 0.000 | 0.847 ± 0.002 | 0.822 ± 0.007 | 0.788 ± 0.007 | 0.834 | 0.029 | 0.063 |
| MuRIL | subword | 0.749 | 0.749 | 0.733 | 0.726 | 0.699 | 0.731 | 0.022 | 0.050 |
| Char LR | char | 0.777 | 0.782 ± 0.000 | 0.793 ± 0.001 | 0.797 ± 0.002 | 0.787 ± 0.002 | 0.787 | -0.021 | -0.010 |
| Char SVM | char | 0.772 | 0.775 ± 0.001 | 0.784 ± 0.001 | 0.788 ± 0.001 | 0.775 ± 0.001 | 0.779 | -0.016 | -0.003 |
| Char CNN | char | 0.660 | 0.660 ± 0.007 | 0.652 ± 0.003 | 0.652 ± 0.003 | 0.645 ± 0.013 | 0.654 | 0.008 | 0.015 |
| CANINE-S | char | 0.778 | 0.780 | 0.780 | 0.788 | 0.771 | 0.780 | -0.010 | 0.007 |

## Macro-F1 vs. obfuscation level — uniform threat model (clean training)

| Model | Repr. | L0 | L1 | L2 | L3 | L4 | Mean L0-L4 | Drop L0→L3 | Drop L0→L4 |
|---|---|---|---|---|---|---|---|---|---|
| Word NB | word | 0.794 | 0.801 ± 0.005 | 0.788 ± 0.006 | 0.764 ± 0.010 | 0.744 ± 0.007 | 0.778 | 0.030 | 0.051 |
| Word RF | word | 0.707 | 0.662 ± 0.004 | 0.543 ± 0.003 | 0.466 ± 0.012 | 0.408 ± 0.006 | 0.557 | 0.241 | 0.299 |
| Word LR | word | 0.785 | 0.779 ± 0.003 | 0.735 ± 0.007 | 0.705 ± 0.004 | 0.666 ± 0.005 | 0.734 | 0.079 | 0.118 |
| Word SVM | word | 0.782 | 0.778 ± 0.004 | 0.740 ± 0.007 | 0.720 ± 0.005 | 0.681 ± 0.006 | 0.740 | 0.062 | 0.101 |
| Word BiGRU | word | 0.574 | 0.543 ± 0.091 | 0.470 ± 0.075 | 0.434 ± 0.045 | 0.422 ± 0.045 | 0.489 | 0.140 | 0.152 |
| DistilmBERT | subword | 0.778 | 0.778 | 0.692 | 0.721 | 0.688 | 0.731 | 0.057 | 0.090 |
| XLM-R | subword | 0.851 | 0.850 ± 0.003 | 0.796 ± 0.004 | 0.742 ± 0.016 | 0.677 ± 0.008 | 0.783 | 0.109 | 0.174 |
| MuRIL | subword | 0.749 | 0.782 | 0.778 | 0.784 | 0.746 | 0.768 | -0.035 | 0.003 |
| Char LR | char | 0.777 | 0.772 ± 0.002 | 0.762 ± 0.002 | 0.737 ± 0.006 | 0.713 ± 0.006 | 0.752 | 0.040 | 0.064 |
| Char SVM | char | 0.772 | 0.758 ± 0.001 | 0.749 ± 0.002 | 0.718 ± 0.005 | 0.711 ± 0.007 | 0.742 | 0.053 | 0.061 |
| Char CNN | char | 0.660 | 0.652 ± 0.006 | 0.630 ± 0.021 | 0.609 ± 0.021 | 0.580 ± 0.021 | 0.626 | 0.051 | 0.080 |
| CANINE-S | char | 0.778 | 0.740 | 0.676 | 0.651 | 0.615 | 0.692 | 0.127 | 0.163 |

## Scam false-negative rate vs. obfuscation level — targeted threat model (clean training)

| Model | Repr. | L0 | L1 | L2 | L3 | L4 |
|---|---|---|---|---|---|---|
| Word NB | word | 0.139 | 0.127 ± 0.010 | 0.174 ± 0.010 | 0.217 ± 0.014 | 0.267 ± 0.003 |
| Word RF | word | 0.055 | 0.068 ± 0.003 | 0.185 ± 0.012 | 0.158 ± 0.012 | 0.150 ± 0.012 |
| Word LR | word | 0.129 | 0.116 ± 0.003 | 0.199 ± 0.009 | 0.192 ± 0.010 | 0.234 ± 0.006 |
| Word SVM | word | 0.080 | 0.077 ± 0.009 | 0.164 ± 0.008 | 0.164 ± 0.015 | 0.232 ± 0.005 |
| Word BiGRU | word | 0.144 | 0.136 ± 0.035 | 0.347 ± 0.134 | 0.254 ± 0.184 | 0.323 ± 0.194 |
| DistilmBERT | subword | 0.045 | 0.047 | 0.015 | 0.041 | 0.049 |
| XLM-R | subword | 0.074 | 0.054 ± 0.000 | 0.109 ± 0.007 | 0.195 ± 0.019 | 0.307 ± 0.018 |
| MuRIL | subword | 0.077 | 0.081 | 0.149 | 0.176 | 0.276 |
| Char LR | char | 0.132 | 0.119 ± 0.001 | 0.094 ± 0.002 | 0.089 ± 0.006 | 0.129 ± 0.006 |
| Char SVM | char | 0.120 | 0.113 ± 0.002 | 0.096 ± 0.004 | 0.092 ± 0.004 | 0.138 ± 0.004 |
| Char CNN | char | 0.437 | 0.441 ± 0.042 | 0.475 ± 0.019 | 0.483 ± 0.029 | 0.508 ± 0.011 |
| CANINE-S | char | 0.123 | 0.127 | 0.134 | 0.113 | 0.177 |

## Scam false-positive rate (genuine/promo flagged as scam) vs. obfuscation level — uniform threat model (clean training)

| Model | Repr. | L0 | L1 | L2 | L3 | L4 |
|---|---|---|---|---|---|---|
| Word NB | word | 0.137 | 0.128 ± 0.007 | 0.103 ± 0.005 | 0.103 ± 0.005 | 0.115 ± 0.003 |
| Word RF | word | 0.319 | 0.361 ± 0.006 | 0.365 ± 0.009 | 0.478 ± 0.005 | 0.568 ± 0.011 |
| Word LR | word | 0.199 | 0.193 ± 0.006 | 0.165 ± 0.004 | 0.191 ± 0.003 | 0.217 ± 0.004 |
| Word SVM | word | 0.206 | 0.199 ± 0.004 | 0.176 ± 0.003 | 0.199 ± 0.003 | 0.216 ± 0.004 |
| Word BiGRU | word | 0.392 | 0.395 ± 0.070 | 0.280 ± 0.064 | 0.381 ± 0.134 | 0.353 ± 0.128 |
| DistilmBERT | subword | 0.191 | 0.187 | 0.368 | 0.249 | 0.265 |
| XLM-R | subword | 0.209 | 0.209 ± 0.002 | 0.215 ± 0.004 | 0.179 ± 0.009 | 0.169 ± 0.000 |
| MuRIL | subword | 0.375 | 0.309 | 0.225 | 0.195 | 0.154 |
| Char LR | char | 0.243 | 0.239 ± 0.006 | 0.232 ± 0.005 | 0.237 ± 0.001 | 0.219 ± 0.005 |
| Char SVM | char | 0.256 | 0.254 ± 0.001 | 0.234 ± 0.004 | 0.241 ± 0.002 | 0.210 ± 0.001 |
| Char CNN | char | 0.126 | 0.119 ± 0.012 | 0.092 ± 0.013 | 0.092 ± 0.018 | 0.100 ± 0.028 |
| CANINE-S | char | 0.236 | 0.277 | 0.320 | 0.367 | 0.362 |

## Expected calibration error vs. obfuscation level — targeted threat model (clean training)

| Model | Repr. | L0 | L1 | L2 | L3 | L4 |
|---|---|---|---|---|---|---|
| Word NB | word | 0.184 | 0.178 ± 0.004 | 0.188 ± 0.003 | 0.198 ± 0.006 | 0.213 ± 0.001 |
| Word RF | word | 0.150 | 0.145 ± 0.002 | 0.113 ± 0.005 | 0.116 ± 0.005 | 0.116 ± 0.004 |
| Word LR | word | 0.059 | 0.044 ± 0.004 | 0.026 ± 0.001 | 0.031 ± 0.006 | 0.031 ± 0.006 |
| Word SVM | word | 0.097 | 0.093 ± 0.003 | 0.105 ± 0.003 | 0.104 ± 0.005 | 0.118 ± 0.002 |
| Word BiGRU | word | 0.268 | 0.262 ± 0.052 | 0.304 ± 0.050 | 0.271 ± 0.060 | 0.289 ± 0.070 |
| DistilmBERT | subword | 0.161 | 0.162 | 0.151 | 0.159 | 0.160 |
| XLM-R | subword | 0.150 | 0.142 ± 0.001 | 0.161 ± 0.002 | 0.192 ± 0.006 | 0.231 ± 0.007 |
| MuRIL | subword | 0.118 | 0.118 | 0.092 | 0.079 | 0.079 |
| Char LR | char | 0.046 | 0.055 ± 0.001 | 0.072 ± 0.002 | 0.078 ± 0.002 | 0.082 ± 0.003 |
| Char SVM | char | 0.082 | 0.078 ± 0.002 | 0.065 ± 0.001 | 0.058 ± 0.000 | 0.057 ± 0.004 |
| Char CNN | char | 0.195 | 0.193 ± 0.033 | 0.204 ± 0.028 | 0.202 ± 0.030 | 0.207 ± 0.026 |
| CANINE-S | char | 0.188 | 0.188 | 0.192 | 0.183 | 0.204 |

## Expected calibration error vs. obfuscation level — uniform threat model (clean training)

| Model | Repr. | L0 | L1 | L2 | L3 | L4 |
|---|---|---|---|---|---|---|
| Word NB | word | 0.184 | 0.177 ± 0.005 | 0.177 ± 0.006 | 0.184 ± 0.009 | 0.196 ± 0.005 |
| Word RF | word | 0.150 | 0.114 ± 0.002 | 0.038 ± 0.004 | 0.058 ± 0.002 | 0.091 ± 0.009 |
| Word LR | word | 0.059 | 0.028 ± 0.003 | 0.023 ± 0.007 | 0.030 ± 0.005 | 0.030 ± 0.008 |
| Word SVM | word | 0.097 | 0.093 ± 0.005 | 0.099 ± 0.005 | 0.101 ± 0.004 | 0.110 ± 0.004 |
| Word BiGRU | word | 0.268 | 0.274 ± 0.052 | 0.318 ± 0.049 | 0.316 ± 0.025 | 0.320 ± 0.034 |
| DistilmBERT | subword | 0.161 | 0.166 | 0.249 | 0.209 | 0.223 |
| XLM-R | subword | 0.150 | 0.148 ± 0.003 | 0.195 ± 0.000 | 0.232 ± 0.014 | 0.283 ± 0.006 |
| MuRIL | subword | 0.118 | 0.141 | 0.141 | 0.145 | 0.120 |
| Char LR | char | 0.046 | 0.045 ± 0.004 | 0.042 ± 0.001 | 0.042 ± 0.005 | 0.062 ± 0.002 |
| Char SVM | char | 0.082 | 0.086 ± 0.000 | 0.078 ± 0.003 | 0.082 ± 0.003 | 0.058 ± 0.003 |
| Char CNN | char | 0.195 | 0.193 ± 0.024 | 0.203 ± 0.011 | 0.203 ± 0.010 | 0.215 ± 0.007 |
| CANINE-S | char | 0.188 | 0.214 | 0.255 | 0.273 | 0.300 |

## Hypothesis test — do character-level models degrade less than word/subword models?

Paired bootstrap (1000 resamples) over test messages on the *drop* in macro-F1 from L0 to the attacked condition. Negative Δdrop means the character model loses less. One-sided p-value for H1: A degrades less than B.

| A (char) | B (word/subword) | threat | level | drop A | drop B | Δdrop (A−B) | 95% CI | p (A degrades less) | McNemar p (attacked) |
|---|---|---|---|---|---|---|---|---|---|
| Char LR | Word LR | targeted | L3 | -0.0229 | 0.0105 | -0.0333 | [-0.041, -0.024] | 0.0 | 3.07e-07 |
| Char LR | Word LR | targeted | L4 | -0.0101 | 0.0264 | -0.0365 | [-0.045, -0.028] | 0.0 | 1.70e-07 |
| Char LR | Word LR | uniform | L3 | 0.0326 | 0.0755 | -0.0424 | [-0.059, -0.027] | 0.0 | 2.33e-10 |
| Char LR | Word LR | uniform | L4 | 0.0705 | 0.123 | -0.0524 | [-0.070, -0.033] | 0.0 | 6.95e-17 |
| Char SVM | Word SVM | targeted | L3 | -0.0174 | 0.0117 | -0.0291 | [-0.037, -0.021] | 0.0 | 4.27e-05 |
| Char SVM | Word SVM | targeted | L4 | -0.0033 | 0.0364 | -0.0398 | [-0.048, -0.031] | 0.0 | 2.57e-08 |
| Char SVM | Word SVM | uniform | L3 | 0.0475 | 0.06 | -0.0121 | [-0.028, 0.004] | 0.072 | 4.42e-04 |
| Char SVM | Word SVM | uniform | L4 | 0.0693 | 0.1032 | -0.0336 | [-0.053, -0.015] | 0.0 | 6.71e-12 |
| Char CNN | Word BiGRU | targeted | L3 | 0.0002 | 0.0139 | -0.0136 | [-0.031, 0.002] | 0.044 | 7.40e-02 |
| Char CNN | Word BiGRU | targeted | L4 | -0.0104 | 0.0276 | -0.0383 | [-0.056, -0.021] | 0.0 | 7.63e-01 |
| Char CNN | Word BiGRU | uniform | L3 | 0.0206 | 0.1727 | -0.1519 | [-0.176, -0.128] | 0.0 | 8.13e-12 |
| Char CNN | Word BiGRU | uniform | L4 | 0.0642 | 0.2029 | -0.139 | [-0.166, -0.112] | 0.0 | 1.19e-11 |
| CANINE-S | MuRIL | targeted | L3 | -0.0104 | 0.0225 | -0.0328 | [-0.042, -0.024] | 0.0 | 3.32e-28 |
| CANINE-S | MuRIL | targeted | L4 | 0.0073 | 0.0499 | -0.0428 | [-0.054, -0.033] | 0.0 | 1.42e-31 |
| CANINE-S | MuRIL | uniform | L3 | 0.1271 | -0.0349 | 0.1618 | [0.140, 0.185] | 1.0 | 3.57e-12 |
| CANINE-S | MuRIL | uniform | L4 | 0.1634 | 0.0028 | 0.1603 | [0.135, 0.186] | 1.0 | 1.30e-12 |
| CANINE-S | DistilmBERT | targeted | L3 | -0.0104 | -0.0051 | -0.0054 | [-0.014, 0.003] | 0.103 | 3.59e-01 |
| CANINE-S | DistilmBERT | targeted | L4 | 0.0073 | -0.0038 | 0.0112 | [0.002, 0.020] | 0.992 | 1.11e-03 |
| CANINE-S | DistilmBERT | uniform | L3 | 0.1271 | 0.0572 | 0.0699 | [0.050, 0.089] | 1.0 | 2.17e-10 |
| CANINE-S | DistilmBERT | uniform | L4 | 0.1634 | 0.0896 | 0.0739 | [0.052, 0.096] | 1.0 | 3.46e-14 |
| CANINE-S | XLM-R | targeted | L3 | -0.0104 | 0.0288 | -0.0391 | [-0.049, -0.030] | 0.0 | 2.15e-01 |
| CANINE-S | XLM-R | targeted | L4 | 0.0073 | 0.063 | -0.0556 | [-0.067, -0.044] | 0.0 | 4.84e-03 |
| CANINE-S | XLM-R | uniform | L3 | 0.1271 | 0.1095 | 0.0175 | [-0.004, 0.040] | 0.946 | 3.69e-05 |
| CANINE-S | XLM-R | uniform | L4 | 0.1634 | 0.1774 | -0.0138 | [-0.038, 0.011] | 0.123 | 4.79e-02 |
| Char LR | XLM-R | targeted | L3 | -0.0229 | 0.0288 | -0.0515 | [-0.061, -0.042] | 0.0 | 9.74e-01 |
| Char LR | XLM-R | targeted | L4 | -0.0101 | 0.063 | -0.0731 | [-0.083, -0.063] | 0.0 | 2.19e-02 |
| Char LR | XLM-R | uniform | L3 | 0.0326 | 0.1095 | -0.0764 | [-0.096, -0.055] | 0.0 | 2.00e-01 |
| Char LR | XLM-R | uniform | L4 | 0.0705 | 0.1774 | -0.1067 | [-0.130, -0.082] | 0.0 | 1.81e-06 |

## Adversarial training (train on 50% L1–L3 obfuscated copies; L4 cross-script transliteration never seen) — targeted threat

| Model | Repr. | F1 L0 (std) | F1 L3 (std) | F1 L4 (std) | FNR L3 (std) | F1 L0 (AT) | F1 L3 (AT) | F1 L4 (AT) | FNR L3 (AT) |
|---|---|---|---|---|---|---|---|---|---|
| Word NB | word | 0.794 | 0.770 | 0.752 | 0.217 | 0.792 | 0.791 | 0.775 | 0.151 |
| Word RF | word | 0.707 | 0.679 | 0.681 | 0.158 | 0.708 | 0.703 | 0.700 | 0.167 |
| Word LR | word | 0.785 | 0.770 | 0.758 | 0.192 | 0.787 | 0.781 | 0.768 | 0.103 |
| Word SVM | word | 0.782 | 0.765 | 0.744 | 0.164 | 0.782 | 0.776 | 0.761 | 0.110 |
| Word BiGRU | word | 0.574 | 0.565 | 0.546 | 0.254 | 0.675 | 0.674 | 0.661 | 0.193 |
| DistilmBERT | subword | 0.778 | 0.783 | 0.782 | 0.041 | 0.806 | 0.807 | 0.805 | 0.034 |
| Char LR | char | 0.777 | 0.797 | 0.787 | 0.089 | 0.762 | 0.779 | 0.778 | 0.078 |
| Char SVM | char | 0.772 | 0.788 | 0.775 | 0.092 | 0.743 | 0.760 | 0.759 | 0.077 |
| Char CNN | char | 0.660 | 0.652 | 0.645 | 0.483 | 0.642 | 0.644 | 0.651 | 0.333 |

## Script-aware canonicalisation defence (NFKC, homoglyph and Tamil-digit folding, zero-width stripping, de-leet, Tamil-script loanwords to English) vs adversarial training — macro-F1, targeted

| Model | L0 std | L0 +norm | L0 AT | L1 std | L1 +norm | L1 AT | L2 std | L2 +norm | L2 AT | L3 std | L3 +norm | L3 AT | L4 std | L4 +norm | L4 AT |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Word NB | 0.794 | 0.794 | 0.792 | 0.800 | 0.798 | 0.799 | 0.784 | 0.799 | 0.800 | 0.770 | 0.800 | 0.791 | 0.752 | 0.785 | 0.775 |
| Word RF | 0.707 | 0.636 | 0.708 | 0.704 | 0.630 | 0.710 | 0.671 | 0.631 | 0.716 | 0.679 | 0.629 | 0.703 | 0.681 | 0.626 | 0.700 |
| Word LR | 0.785 | 0.789 | 0.787 | 0.792 | 0.791 | 0.788 | 0.767 | 0.790 | 0.783 | 0.770 | 0.795 | 0.781 | 0.758 | 0.776 | 0.768 |
| Word SVM | 0.782 | 0.781 | 0.782 | 0.787 | 0.784 | 0.782 | 0.763 | 0.782 | 0.779 | 0.765 | 0.788 | 0.776 | 0.744 | 0.770 | 0.761 |
| Word BiGRU | 0.574 | 0.601 | 0.675 | 0.578 | 0.598 | 0.674 | 0.539 | 0.610 | 0.668 | 0.565 | 0.599 | 0.674 | 0.546 | 0.597 | 0.661 |
| Char LR | 0.777 | 0.780 | 0.762 | 0.782 | 0.785 | 0.765 | 0.793 | 0.785 | 0.771 | 0.797 | 0.793 | 0.779 | 0.787 | 0.784 | 0.778 |
| Char SVM | 0.772 | 0.774 | 0.743 | 0.775 | 0.779 | 0.746 | 0.784 | 0.777 | 0.752 | 0.788 | 0.785 | 0.760 | 0.775 | 0.777 | 0.759 |
| Char CNN | 0.660 | 0.646 | 0.642 | 0.660 | 0.649 | 0.641 | 0.652 | 0.647 | 0.637 | 0.652 | 0.651 | 0.644 | 0.645 | 0.653 | 0.651 |

## Per-language macro-F1, clean (L0) vs heavy targeted obfuscation (L3)

Languages: en = English, ta = Tamil–English

| Model | en L0 | en L3 | ta L0 | ta L3 |
|---|---|---|---|---|
| Word NB | 0.788 | 0.771 | 0.803 | 0.770 |
| Word RF | 0.769 | 0.722 | 0.635 | 0.624 |
| Word LR | 0.738 | 0.733 | 0.828 | 0.805 |
| Word SVM | 0.748 | 0.737 | 0.815 | 0.793 |
| Word BiGRU | 0.688 | 0.688 | 0.662 | 0.635 |
| DistilmBERT | 0.782 | 0.781 | 0.774 | 0.785 |
| XLM-R | 0.857 | 0.809 | 0.844 | 0.834 |
| MuRIL | 0.754 | 0.709 | 0.743 | 0.742 |
| Char LR | 0.758 | 0.783 | 0.793 | 0.810 |
| Char SVM | 0.752 | 0.766 | 0.788 | 0.807 |
| Char CNN | 0.692 | 0.701 | 0.606 | 0.607 |
| CANINE-S | 0.759 | 0.777 | 0.795 | 0.798 |

## Bilingual transfer (train on English or Tamil–English only, test on both; clean and L2 targeted)

| Model | Repr. | In-language F1 | Cross-language F1 | Transfer gap | In-language F1 @L2 | Cross-language F1 @L2 |
|---|---|---|---|---|---|---|
| Word LR | word | 0.792 | 0.731 | 0.061 | 0.776 | 0.703 |
| Word SVM | word | 0.797 | 0.729 | 0.068 | 0.784 | 0.703 |
| Word BiGRU | word | 0.640 | 0.371 | 0.269 | 0.515 | 0.329 |
| DistilmBERT | subword | 0.822 | 0.583 | 0.240 | 0.800 | 0.662 |
| MuRIL | subword | 0.775 | 0.770 | 0.005 | 0.676 | 0.671 |
| Char LR | char | 0.750 | 0.795 | -0.044 | 0.763 | 0.796 |
| Char SVM | char | 0.754 | 0.781 | -0.027 | 0.762 | 0.782 |
| Char CNN | char | 0.776 | 0.573 | 0.203 | 0.762 | 0.562 |

## Cue ablation — URLs, UPI IDs, phone numbers, amounts and numbers replaced by placeholders (train and test), targeted threat

Shows how much each model relies on non-linguistic cues rather than the code-mixed text itself.

| Model | Repr. | F1 L0 (full) | F1 L0 (cues masked) | Δ L0 | F1 L3 (full) | F1 L3 (masked) | FNR L3 (masked) |
|---|---|---|---|---|---|---|---|
| Word NB | word | 0.794 | 0.768 | -0.027 | 0.770 | 0.742 | 0.224 |
| Word RF | word | 0.707 | 0.718 | +0.011 | 0.679 | 0.648 | 0.313 |
| Word LR | word | 0.785 | 0.786 | +0.001 | 0.770 | 0.756 | 0.220 |
| Word SVM | word | 0.782 | 0.794 | +0.012 | 0.765 | 0.778 | 0.191 |
| Word BiGRU | word | 0.574 | 0.621 | +0.047 | 0.565 | 0.576 | 0.141 |
| Char LR | char | 0.777 | 0.725 | -0.052 | 0.797 | 0.710 | 0.168 |
| Char SVM | char | 0.772 | 0.715 | -0.056 | 0.788 | 0.719 | 0.120 |
| Char CNN | char | 0.660 | 0.690 | +0.030 | 0.652 | 0.646 | 0.537 |

## Inference latency (CPU, 2 cores, batch size 1 unless stated)

| Model | Repr. | p50 ms | p95 ms | Batch throughput (msg/s) | Size |
|---|---|---|---|---|---|
| Word NB | word | 0.42 | 0.70 | 41999 | 7.2k features |
| Word RF | word | 58.36 | 87.00 | 3219 | 7.2k features |
| Word LR | word | 0.62 | 0.95 | 36352 | 7.2k features |
| Word SVM | word | 2.84 | 6.63 | 11682 | 7.2k features |
| Word BiGRU | word | 2.23 | 415.82 | 2112 | 0.4M params |
| DistilmBERT | subword | 58.57 | 79.00 | 26 | 135.3M params |
| XLM-R | subword | 149.50 | 798.98 | 17 | 278.0M params |
| MuRIL | subword | 114.97 | 145.04 | 14 | 237.6M params |
| Char LR | char | 0.83 | 1.10 | 4300 | 38.6k features |
| Char SVM | char | 3.17 | 4.67 | 5382 | 38.6k features |
| Char CNN | char | 0.97 | 9.26 | 460 | 0.4M params |
| CANINE-S | char | 154.77 | 200.08 | 13 | 132.1M params |
