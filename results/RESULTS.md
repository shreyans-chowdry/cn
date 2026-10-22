# Results

All numbers on the template-disjoint test set (n = 3971). Obfuscated conditions are averaged over obfuscation seeds; from-scratch neural models are additionally averaged over training seeds (mean ± std).

## Obfuscation scheme statistics

| Level | Word perturb prob. | Words changed | Char edit rate | Char edit rate after canonicalisation | Top ops |
|---|---|---|---|---|---|
| L1 (light) | 0.15 | 0.124 | 0.033 | 0.019 | case, phonetic, vowel_drop, swap |
| L2 (moderate) | 0.3 | 0.346 | 0.083 | 0.028 | leet, separator, case, repeat |
| L3 (heavy) | 0.45 | 0.433 | 0.110 | 0.045 | zero_width, insert, delete, homoglyph |
| L4 (cross-script) | 0.6 | 0.548 | 0.201 | 0.080 | script_mix, zero_width, swap, delete |

## Table 1 — Clean test performance (no obfuscation)

| Model | Repr. | Macro-F1 | 95% CI (seed 0) | Scam FNR | Scam FPR | ECE | Latency ms (p50) | Size |
|---|---|---|---|---|---|---|---|---|
| Word NB | word | 0.763 | [0.748, 0.777] | 0.041 | 0.229 | 0.204 | 0.50 | 10.5k features |
| Word RF | word | 0.694 | [0.675, 0.709] | 0.302 | 0.209 | 0.142 | 78.51 | 10.5k features |
| Word LR | word | 0.775 | [0.760, 0.788] | 0.084 | 0.263 | 0.073 | 0.71 | 10.5k features |
| Word SVM | word | 0.788 | [0.773, 0.801] | 0.078 | 0.270 | 0.098 | 3.07 | 10.5k features |
| Word BiGRU | word | 0.668 ± 0.026 | [0.630, 0.664] | 0.191 | 0.247 | 0.192 | 2.82 | 0.5M params |
| DistilmBERT | subword | 0.779 | [0.767, 0.792] | 0.068 | 0.253 | 0.184 | 37.07 | 135.3M params |
| XLM-R | subword | 0.838 | [0.826, 0.851] | 0.052 | 0.141 | 0.119 | 73.19 | 278.0M params |
| MuRIL | subword | 0.759 | [0.746, 0.772] | 0.117 | 0.308 | 0.316 | 73.26 | 237.6M params |
| Char LR | char | 0.812 | [0.800, 0.825] | 0.126 | 0.210 | 0.035 | 1.01 | 45.1k features |
| Char SVM | char | 0.807 | [0.795, 0.819] | 0.138 | 0.214 | 0.070 | 4.30 | 45.1k features |
| Char CNN | char | 0.673 ± 0.029 | [0.650, 0.679] | 0.170 | 0.258 | 0.189 | 1.31 | 0.4M params |
| CANINE-S | char | 0.726 | [0.711, 0.741] | 0.093 | 0.303 | 0.216 | 99.88 | 132.1M params |

## Macro-F1 vs. obfuscation level — targeted threat model (clean training)

| Model | Repr. | L0 | L1 | L2 | L3 | L4 | Mean L0-L4 | Drop L0→L3 | Drop L0→L4 |
|---|---|---|---|---|---|---|---|---|---|
| Word NB | word | 0.763 | 0.751 ± 0.001 | 0.708 ± 0.007 | 0.690 ± 0.003 | 0.685 ± 0.004 | 0.719 | 0.073 | 0.078 |
| Word RF | word | 0.694 | 0.677 ± 0.003 | 0.614 ± 0.002 | 0.597 ± 0.005 | 0.592 ± 0.004 | 0.635 | 0.097 | 0.102 |
| Word LR | word | 0.775 | 0.767 ± 0.001 | 0.720 ± 0.001 | 0.709 ± 0.003 | 0.703 ± 0.004 | 0.735 | 0.066 | 0.071 |
| Word SVM | word | 0.788 | 0.780 ± 0.001 | 0.734 ± 0.002 | 0.723 ± 0.004 | 0.718 ± 0.003 | 0.749 | 0.064 | 0.070 |
| Word BiGRU | word | 0.668 | 0.644 ± 0.020 | 0.558 ± 0.011 | 0.531 ± 0.044 | 0.513 ± 0.045 | 0.583 | 0.138 | 0.155 |
| DistilmBERT | subword | 0.779 | 0.780 | 0.774 | 0.780 | 0.773 | 0.777 | -0.001 | 0.006 |
| XLM-R | subword | 0.838 | 0.831 | 0.758 | 0.766 | 0.717 | 0.782 | 0.072 | 0.121 |
| MuRIL | subword | 0.759 | 0.739 | 0.668 | 0.698 | 0.705 | 0.714 | 0.061 | 0.053 |
| Char LR | char | 0.812 | 0.805 ± 0.000 | 0.781 ± 0.003 | 0.774 ± 0.001 | 0.749 ± 0.001 | 0.784 | 0.038 | 0.064 |
| Char SVM | char | 0.807 | 0.797 ± 0.001 | 0.773 ± 0.003 | 0.764 ± 0.004 | 0.735 ± 0.002 | 0.775 | 0.044 | 0.073 |
| Char CNN | char | 0.673 | 0.668 ± 0.025 | 0.645 ± 0.026 | 0.638 ± 0.023 | 0.600 ± 0.022 | 0.645 | 0.035 | 0.074 |
| CANINE-S | char | 0.726 | 0.722 | 0.652 | 0.683 | 0.659 | 0.688 | 0.043 | 0.067 |

## Macro-F1 vs. obfuscation level — uniform threat model (clean training)

| Model | Repr. | L0 | L1 | L2 | L3 | L4 | Mean L0-L4 | Drop L0→L3 | Drop L0→L4 |
|---|---|---|---|---|---|---|---|---|---|
| Word NB | word | 0.763 | 0.756 ± 0.002 | 0.715 ± 0.007 | 0.685 ± 0.003 | 0.658 ± 0.001 | 0.715 | 0.078 | 0.105 |
| Word RF | word | 0.694 | 0.667 ± 0.003 | 0.569 ± 0.008 | 0.532 ± 0.005 | 0.488 ± 0.004 | 0.590 | 0.162 | 0.206 |
| Word LR | word | 0.775 | 0.760 ± 0.003 | 0.708 ± 0.006 | 0.670 ± 0.001 | 0.643 ± 0.004 | 0.711 | 0.105 | 0.132 |
| Word SVM | word | 0.788 | 0.768 ± 0.004 | 0.713 ± 0.005 | 0.676 ± 0.002 | 0.646 ± 0.003 | 0.718 | 0.112 | 0.142 |
| Word BiGRU | word | 0.668 | 0.622 ± 0.018 | 0.515 ± 0.027 | 0.468 ± 0.043 | 0.433 ± 0.044 | 0.541 | 0.201 | 0.235 |
| DistilmBERT | subword | 0.779 | 0.754 | 0.687 | 0.701 | 0.633 | 0.711 | 0.078 | 0.146 |
| XLM-R | subword | 0.838 | 0.813 | 0.725 | 0.708 | 0.640 | 0.745 | 0.130 | 0.198 |
| MuRIL | subword | 0.759 | 0.733 | 0.651 | 0.681 | 0.651 | 0.695 | 0.078 | 0.108 |
| Char LR | char | 0.812 | 0.802 ± 0.001 | 0.768 ± 0.003 | 0.754 ± 0.003 | 0.714 ± 0.003 | 0.770 | 0.058 | 0.098 |
| Char SVM | char | 0.807 | 0.795 ± 0.001 | 0.767 ± 0.003 | 0.754 ± 0.005 | 0.710 ± 0.006 | 0.767 | 0.054 | 0.097 |
| Char CNN | char | 0.673 | 0.664 ± 0.026 | 0.637 ± 0.022 | 0.628 ± 0.020 | 0.585 ± 0.010 | 0.638 | 0.045 | 0.088 |
| CANINE-S | char | 0.726 | 0.730 | 0.719 | 0.716 | 0.686 | 0.715 | 0.010 | 0.040 |

## Scam false-negative rate vs. obfuscation level — targeted threat model (clean training)

| Model | Repr. | L0 | L1 | L2 | L3 | L4 |
|---|---|---|---|---|---|---|
| Word NB | word | 0.041 | 0.081 ± 0.004 | 0.208 ± 0.020 | 0.263 ± 0.007 | 0.273 ± 0.011 |
| Word RF | word | 0.302 | 0.356 ± 0.008 | 0.544 ± 0.004 | 0.591 ± 0.013 | 0.605 ± 0.010 |
| Word LR | word | 0.084 | 0.108 ± 0.003 | 0.254 ± 0.003 | 0.282 ± 0.010 | 0.296 ± 0.011 |
| Word SVM | word | 0.078 | 0.103 ± 0.004 | 0.251 ± 0.004 | 0.281 ± 0.011 | 0.298 ± 0.008 |
| Word BiGRU | word | 0.191 | 0.272 ± 0.128 | 0.576 ± 0.111 | 0.637 ± 0.166 | 0.692 ± 0.159 |
| DistilmBERT | subword | 0.068 | 0.064 | 0.089 | 0.068 | 0.091 |
| XLM-R | subword | 0.052 | 0.077 | 0.317 | 0.293 | 0.443 |
| MuRIL | subword | 0.117 | 0.182 | 0.423 | 0.313 | 0.291 |
| Char LR | char | 0.126 | 0.151 ± 0.001 | 0.229 ± 0.009 | 0.251 ± 0.004 | 0.331 ± 0.004 |
| Char SVM | char | 0.138 | 0.172 ± 0.004 | 0.250 ± 0.010 | 0.280 ± 0.013 | 0.369 ± 0.006 |
| Char CNN | char | 0.170 | 0.189 ± 0.021 | 0.266 ± 0.030 | 0.288 ± 0.036 | 0.411 ± 0.044 |
| CANINE-S | char | 0.093 | 0.106 | 0.332 | 0.240 | 0.315 |

## Scam false-positive rate (genuine/promo flagged as scam) vs. obfuscation level — uniform threat model (clean training)

| Model | Repr. | L0 | L1 | L2 | L3 | L4 |
|---|---|---|---|---|---|---|
| Word NB | word | 0.229 | 0.214 ± 0.004 | 0.166 ± 0.002 | 0.154 ± 0.006 | 0.179 ± 0.010 |
| Word RF | word | 0.209 | 0.186 ± 0.001 | 0.131 ± 0.002 | 0.118 ± 0.001 | 0.116 ± 0.008 |
| Word LR | word | 0.263 | 0.234 ± 0.002 | 0.162 ± 0.005 | 0.175 ± 0.004 | 0.206 ± 0.000 |
| Word SVM | word | 0.270 | 0.244 ± 0.005 | 0.169 ± 0.001 | 0.176 ± 0.003 | 0.208 ± 0.004 |
| Word BiGRU | word | 0.247 | 0.238 ± 0.095 | 0.125 ± 0.065 | 0.144 ± 0.094 | 0.132 ± 0.089 |
| DistilmBERT | subword | 0.253 | 0.286 | 0.364 | 0.343 | 0.410 |
| XLM-R | subword | 0.141 | 0.137 | 0.089 | 0.108 | 0.101 |
| MuRIL | subword | 0.308 | 0.283 | 0.228 | 0.234 | 0.265 |
| Char LR | char | 0.210 | 0.208 ± 0.001 | 0.183 ± 0.003 | 0.165 ± 0.003 | 0.135 ± 0.005 |
| Char SVM | char | 0.214 | 0.209 ± 0.003 | 0.180 ± 0.000 | 0.162 ± 0.003 | 0.125 ± 0.004 |
| Char CNN | char | 0.258 | 0.252 ± 0.056 | 0.230 ± 0.061 | 0.211 ± 0.064 | 0.169 ± 0.058 |
| CANINE-S | char | 0.303 | 0.287 | 0.142 | 0.192 | 0.180 |

## Expected calibration error vs. obfuscation level — targeted threat model (clean training)

| Model | Repr. | L0 | L1 | L2 | L3 | L4 |
|---|---|---|---|---|---|---|
| Word NB | word | 0.204 | 0.216 ± 0.002 | 0.256 ± 0.006 | 0.270 ± 0.002 | 0.271 ± 0.003 |
| Word RF | word | 0.142 | 0.134 ± 0.002 | 0.091 ± 0.003 | 0.083 ± 0.001 | 0.079 ± 0.004 |
| Word LR | word | 0.073 | 0.064 ± 0.001 | 0.056 ± 0.004 | 0.052 ± 0.006 | 0.062 ± 0.002 |
| Word SVM | word | 0.098 | 0.100 ± 0.001 | 0.136 ± 0.002 | 0.139 ± 0.005 | 0.140 ± 0.004 |
| Word BiGRU | word | 0.192 | 0.215 ± 0.018 | 0.294 ± 0.020 | 0.312 ± 0.051 | 0.330 ± 0.050 |
| DistilmBERT | subword | 0.184 | 0.182 | 0.188 | 0.183 | 0.190 |
| XLM-R | subword | 0.119 | 0.125 | 0.201 | 0.192 | 0.242 |
| MuRIL | subword | 0.316 | 0.292 | 0.199 | 0.244 | 0.251 |
| Char LR | char | 0.035 | 0.033 ± 0.002 | 0.024 ± 0.005 | 0.024 ± 0.004 | 0.029 ± 0.001 |
| Char SVM | char | 0.070 | 0.079 ± 0.001 | 0.103 ± 0.002 | 0.109 ± 0.003 | 0.133 ± 0.001 |
| Char CNN | char | 0.189 | 0.193 ± 0.031 | 0.216 ± 0.030 | 0.220 ± 0.023 | 0.261 ± 0.019 |
| CANINE-S | char | 0.216 | 0.220 | 0.292 | 0.260 | 0.283 |

## Expected calibration error vs. obfuscation level — uniform threat model (clean training)

| Model | Repr. | L0 | L1 | L2 | L3 | L4 |
|---|---|---|---|---|---|---|
| Word NB | word | 0.204 | 0.213 ± 0.003 | 0.247 ± 0.007 | 0.268 ± 0.004 | 0.283 ± 0.001 |
| Word RF | word | 0.142 | 0.112 ± 0.000 | 0.049 ± 0.003 | 0.034 ± 0.004 | 0.024 ± 0.002 |
| Word LR | word | 0.073 | 0.043 ± 0.006 | 0.020 ± 0.004 | 0.018 ± 0.004 | 0.013 ± 0.004 |
| Word SVM | word | 0.098 | 0.092 ± 0.003 | 0.112 ± 0.002 | 0.133 ± 0.002 | 0.140 ± 0.003 |
| Word BiGRU | word | 0.192 | 0.229 ± 0.018 | 0.323 ± 0.037 | 0.340 ± 0.062 | 0.365 ± 0.063 |
| DistilmBERT | subword | 0.184 | 0.206 | 0.261 | 0.249 | 0.297 |
| XLM-R | subword | 0.119 | 0.137 | 0.217 | 0.224 | 0.284 |
| MuRIL | subword | 0.316 | 0.294 | 0.218 | 0.258 | 0.244 |
| Char LR | char | 0.035 | 0.035 ± 0.001 | 0.037 ± 0.003 | 0.040 ± 0.002 | 0.029 ± 0.004 |
| Char SVM | char | 0.070 | 0.075 ± 0.002 | 0.085 ± 0.003 | 0.081 ± 0.003 | 0.109 ± 0.006 |
| Char CNN | char | 0.189 | 0.192 ± 0.030 | 0.208 ± 0.023 | 0.206 ± 0.017 | 0.249 ± 0.011 |
| CANINE-S | char | 0.216 | 0.211 | 0.229 | 0.220 | 0.244 |

## Hypothesis test — do character-level models degrade less than word/subword models?

Paired bootstrap (1000 resamples) over test messages on the *drop* in macro-F1 from L0 to the attacked condition. Negative Δdrop means the character model loses less. One-sided p-value for H1: A degrades less than B.

| A (char) | B (word/subword) | threat | level | drop A | drop B | Δdrop (A−B) | 95% CI | p (A degrades less) | McNemar p (attacked) |
|---|---|---|---|---|---|---|---|---|---|
| Char LR | Word LR | targeted | L3 | 0.0391 | 0.0688 | -0.0296 | [-0.038, -0.021] | 0.0 | 6.22e-25 |
| Char LR | Word LR | targeted | L4 | 0.0647 | 0.0679 | -0.0034 | [-0.012, 0.006] | 0.213 | 3.86e-07 |
| Char LR | Word LR | uniform | L3 | 0.0603 | 0.1063 | -0.0456 | [-0.061, -0.031] | 0.0 | 1.79e-28 |
| Char LR | Word LR | uniform | L4 | 0.1008 | 0.1351 | -0.0343 | [-0.049, -0.018] | 0.0 | 4.47e-22 |
| Char SVM | Word SVM | targeted | L3 | 0.0483 | 0.0682 | -0.0196 | [-0.027, -0.012] | 0.0 | 2.53e-12 |
| Char SVM | Word SVM | targeted | L4 | 0.0746 | 0.0663 | 0.0083 | [-0.000, 0.017] | 0.97 | 1.63e-01 |
| Char SVM | Word SVM | uniform | L3 | 0.0588 | 0.1132 | -0.0544 | [-0.069, -0.040] | 0.0 | 3.25e-23 |
| Char SVM | Word SVM | uniform | L4 | 0.1033 | 0.1385 | -0.0352 | [-0.050, -0.019] | 0.0 | 4.76e-14 |
| Char CNN | Word BiGRU | targeted | L3 | 0.0464 | 0.1703 | -0.1237 | [-0.136, -0.111] | 0.0 | 1.25e-17 |
| Char CNN | Word BiGRU | targeted | L4 | 0.0871 | 0.1921 | -0.105 | [-0.120, -0.091] | 0.0 | 8.46e-10 |
| Char CNN | Word BiGRU | uniform | L3 | 0.0363 | 0.2291 | -0.1932 | [-0.213, -0.173] | 0.0 | 3.70e-38 |
| Char CNN | Word BiGRU | uniform | L4 | 0.0788 | 0.255 | -0.1765 | [-0.199, -0.154] | 0.0 | 3.55e-32 |
| CANINE-S | DistilmBERT | targeted | L3 | 0.0434 | -0.0007 | 0.0441 | [0.037, 0.052] | 1.0 | 4.49e-21 |
| CANINE-S | DistilmBERT | targeted | L4 | 0.0667 | 0.0057 | 0.061 | [0.052, 0.070] | 1.0 | 3.65e-30 |
| CANINE-S | DistilmBERT | uniform | L3 | 0.0106 | 0.0779 | -0.067 | [-0.085, -0.050] | 0.0 | 3.52e-02 |
| CANINE-S | DistilmBERT | uniform | L4 | 0.0401 | 0.1457 | -0.1058 | [-0.127, -0.086] | 0.0 | 1.13e-07 |
| CANINE-S | XLM-R | targeted | L3 | 0.0434 | 0.0721 | -0.0286 | [-0.038, -0.019] | 0.0 | 8.36e-14 |
| CANINE-S | XLM-R | targeted | L4 | 0.0667 | 0.1215 | -0.0551 | [-0.067, -0.045] | 0.0 | 1.12e-05 |
| CANINE-S | XLM-R | uniform | L3 | 0.0106 | 0.1298 | -0.1189 | [-0.138, -0.098] | 0.0 | 5.27e-01 |
| CANINE-S | XLM-R | uniform | L4 | 0.0401 | 0.1984 | -0.1586 | [-0.182, -0.139] | 0.0 | 1.50e-04 |
| Char LR | XLM-R | targeted | L3 | 0.0391 | 0.0721 | -0.033 | [-0.042, -0.025] | 0.0 | 1.06e-01 |
| Char LR | XLM-R | targeted | L4 | 0.0647 | 0.1215 | -0.0572 | [-0.067, -0.047] | 0.0 | 1.53e-05 |
| Char LR | XLM-R | uniform | L3 | 0.0603 | 0.1298 | -0.0693 | [-0.086, -0.051] | 0.0 | 2.04e-03 |
| Char LR | XLM-R | uniform | L4 | 0.1008 | 0.1984 | -0.0979 | [-0.117, -0.078] | 0.0 | 4.49e-10 |

## Adversarial training (train on 50% L1–L3 obfuscated copies; L4 script-mixing never seen) — targeted threat

| Model | Repr. | F1 L0 (std) | F1 L3 (std) | F1 L4 (std) | FNR L3 (std) | F1 L0 (AT) | F1 L3 (AT) | F1 L4 (AT) | FNR L3 (AT) |
|---|---|---|---|---|---|---|---|---|---|
| Word NB | word | 0.763 | 0.690 | 0.685 | 0.263 | 0.765 | 0.724 | 0.724 | 0.177 |
| Word RF | word | 0.694 | 0.597 | 0.592 | 0.591 | 0.723 | 0.677 | 0.673 | 0.359 |
| Word LR | word | 0.775 | 0.709 | 0.703 | 0.282 | 0.756 | 0.734 | 0.735 | 0.167 |
| Word SVM | word | 0.788 | 0.723 | 0.718 | 0.281 | 0.751 | 0.729 | 0.727 | 0.165 |
| Word BiGRU | word | 0.668 | 0.531 | 0.513 | 0.637 | 0.705 | 0.672 | 0.673 | 0.221 |
| DistilmBERT | subword | 0.779 | 0.780 | 0.773 | 0.068 | 0.729 | 0.729 | 0.739 | 0.145 |
| Char LR | char | 0.812 | 0.774 | 0.749 | 0.251 | 0.806 | 0.785 | 0.774 | 0.197 |
| Char SVM | char | 0.807 | 0.764 | 0.735 | 0.280 | 0.783 | 0.769 | 0.758 | 0.169 |
| Char CNN | char | 0.673 | 0.638 | 0.600 | 0.288 | 0.663 | 0.649 | 0.628 | 0.194 |

## Canonicalisation defence (NFKC + homoglyph folding + zero-width stripping + de-leet) vs adversarial training — macro-F1, targeted

| Model | L0 std | L0 +norm | L0 AT | L1 std | L1 +norm | L1 AT | L2 std | L2 +norm | L2 AT | L3 std | L3 +norm | L3 AT | L4 std | L4 +norm | L4 AT |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Word NB | 0.763 | 0.759 | 0.765 | 0.751 | 0.748 | 0.755 | 0.708 | 0.744 | 0.743 | 0.690 | 0.736 | 0.724 | 0.685 | 0.734 | 0.724 |
| Word RF | 0.694 | 0.679 | 0.723 | 0.677 | 0.660 | 0.713 | 0.614 | 0.647 | 0.708 | 0.597 | 0.626 | 0.677 | 0.592 | 0.608 | 0.673 |
| Word LR | 0.775 | 0.781 | 0.756 | 0.767 | 0.774 | 0.751 | 0.720 | 0.771 | 0.748 | 0.709 | 0.761 | 0.734 | 0.703 | 0.759 | 0.735 |
| Word SVM | 0.788 | 0.787 | 0.751 | 0.780 | 0.781 | 0.746 | 0.734 | 0.778 | 0.743 | 0.723 | 0.766 | 0.729 | 0.718 | 0.764 | 0.727 |
| Word BiGRU | 0.668 | 0.665 | 0.705 | 0.644 | 0.641 | 0.696 | 0.558 | 0.627 | 0.675 | 0.531 | 0.600 | 0.672 | 0.513 | 0.601 | 0.673 |
| Char LR | 0.812 | 0.824 | 0.806 | 0.805 | 0.815 | 0.800 | 0.781 | 0.809 | 0.791 | 0.774 | 0.805 | 0.785 | 0.749 | 0.784 | 0.774 |
| Char SVM | 0.807 | 0.806 | 0.783 | 0.797 | 0.797 | 0.779 | 0.773 | 0.790 | 0.775 | 0.764 | 0.785 | 0.769 | 0.735 | 0.764 | 0.758 |
| Char CNN | 0.673 | 0.656 | 0.663 | 0.668 | 0.652 | 0.661 | 0.645 | 0.650 | 0.651 | 0.638 | 0.646 | 0.649 | 0.600 | 0.624 | 0.628 |

## Per-language macro-F1, clean (L0) vs heavy targeted obfuscation (L3)

Languages: en = English, hi = Hindi-English, ta = Tamil-English, bn = Bengali-English, te = Telugu-English

| Model | en L0 | en L3 | hi L0 | hi L3 | ta L0 | ta L3 | bn L0 | bn L3 | te L0 | te L3 |
|---|---|---|---|---|---|---|---|---|---|---|
| Word NB | 0.784 | 0.717 | 0.735 | 0.655 | 0.747 | 0.695 | 0.829 | 0.746 | 0.716 | 0.633 |
| Word RF | 0.722 | 0.631 | 0.666 | 0.546 | 0.683 | 0.616 | 0.714 | 0.601 | 0.680 | 0.585 |
| Word LR | 0.756 | 0.714 | 0.735 | 0.643 | 0.839 | 0.794 | 0.750 | 0.680 | 0.797 | 0.717 |
| Word SVM | 0.748 | 0.706 | 0.747 | 0.652 | 0.850 | 0.812 | 0.786 | 0.719 | 0.806 | 0.728 |
| Word BiGRU | 0.606 | 0.465 | 0.626 | 0.451 | 0.701 | 0.543 | 0.649 | 0.465 | 0.643 | 0.450 |
| DistilmBERT | 0.780 | 0.788 | 0.756 | 0.748 | 0.758 | 0.762 | 0.817 | 0.821 | 0.779 | 0.775 |
| XLM-R | 0.898 | 0.872 | 0.803 | 0.725 | 0.789 | 0.711 | 0.868 | 0.797 | 0.830 | 0.721 |
| MuRIL | 0.830 | 0.780 | 0.783 | 0.712 | 0.707 | 0.644 | 0.721 | 0.678 | 0.739 | 0.666 |
| Char LR | 0.779 | 0.748 | 0.805 | 0.757 | 0.808 | 0.792 | 0.819 | 0.762 | 0.852 | 0.814 |
| Char SVM | 0.762 | 0.726 | 0.784 | 0.736 | 0.824 | 0.797 | 0.825 | 0.756 | 0.843 | 0.802 |
| Char CNN | 0.655 | 0.598 | 0.717 | 0.656 | 0.626 | 0.609 | 0.734 | 0.669 | 0.578 | 0.551 |
| CANINE-S | 0.662 | 0.627 | 0.786 | 0.732 | 0.689 | 0.654 | 0.762 | 0.721 | 0.711 | 0.663 |

## Cross-lingual transfer (train on one language pair, test on each; clean and L2 targeted)

| Model | Repr. | In-language F1 | Cross-language F1 | Transfer gap | In-language F1 @L2 | Cross-language F1 @L2 |
|---|---|---|---|---|---|---|
| Word LR | word | 0.730 | 0.768 | -0.038 | 0.692 | 0.710 |
| Word SVM | word | 0.745 | 0.762 | -0.017 | 0.704 | 0.704 |
| Word BiGRU | word | 0.608 | 0.475 | 0.133 | 0.538 | 0.415 |
| DistilmBERT | subword | 0.588 | 0.531 | 0.057 | 0.578 | 0.528 |
| Char LR | char | 0.789 | 0.809 | -0.019 | 0.772 | 0.783 |
| Char SVM | char | 0.782 | 0.805 | -0.023 | 0.762 | 0.777 |
| Char CNN | char | 0.603 | 0.586 | 0.017 | 0.577 | 0.563 |

## Cue ablation — URLs, UPI IDs, phone numbers, amounts and numbers replaced by placeholders (train and test), targeted threat

Shows how much each model relies on non-linguistic cues rather than the code-mixed text itself.

| Model | Repr. | F1 L0 (full) | F1 L0 (cues masked) | Δ L0 | F1 L3 (full) | F1 L3 (masked) | FNR L3 (masked) |
|---|---|---|---|---|---|---|---|
| Word NB | word | 0.763 | 0.770 | +0.007 | 0.690 | 0.680 | 0.294 |
| Word RF | word | 0.694 | 0.661 | -0.032 | 0.597 | 0.624 | 0.484 |
| Word LR | word | 0.775 | 0.764 | -0.011 | 0.709 | 0.683 | 0.311 |
| Word SVM | word | 0.788 | 0.763 | -0.025 | 0.723 | 0.690 | 0.297 |
| Word BiGRU | word | 0.668 | 0.674 | +0.006 | 0.531 | 0.650 | 0.044 |
| Char LR | char | 0.812 | 0.772 | -0.040 | 0.774 | 0.728 | 0.257 |
| Char SVM | char | 0.807 | 0.742 | -0.065 | 0.764 | 0.703 | 0.280 |
| Char CNN | char | 0.673 | 0.637 | -0.036 | 0.638 | 0.606 | 0.278 |

## Inference latency (CPU, 2 cores, batch size 1 unless stated)

| Model | Repr. | p50 ms | p95 ms | Batch throughput (msg/s) | Size |
|---|---|---|---|---|---|
| Word NB | word | 0.50 | 0.81 | 19874 | 10.5k features |
| Word RF | word | 78.51 | 110.29 | 2301 | 10.5k features |
| Word LR | word | 0.71 | 1.15 | 28469 | 10.5k features |
| Word SVM | word | 3.07 | 4.76 | 24695 | 10.5k features |
| Word BiGRU | word | 2.82 | 4.19 | 2071 | 0.5M params |
| DistilmBERT | subword | 37.07 | 51.10 | 39 | 135.3M params |
| XLM-R | subword | 73.19 | 98.62 | 23 | 278.0M params |
| MuRIL | subword | 73.26 | 97.25 | 21 | 237.6M params |
| Char LR | char | 1.01 | 1.51 | 5215 | 45.1k features |
| Char SVM | char | 4.30 | 5.87 | 2712 | 45.1k features |
| Char CNN | char | 1.31 | 2.78 | 933 | 0.4M params |
| CANINE-S | char | 99.88 | 134.12 | 17 | 132.1M params |
