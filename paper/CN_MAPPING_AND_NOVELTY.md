# How ScamShield maps to the Computer Networks syllabus, and what is new

## Is this a Computer Networks project?

Yes, though the scam classifier on its own would not make it one. A scam classifier is a machine-learning
component, so the project wraps it in a complete networked system. The system has its own
application-layer protocol, transport-layer reliability built on UDP, error detection, DNS and IP-addressing
analysis, and measured experiments for each of these. Every networking piece is implemented from first
principles (no networking libraries beyond raw sockets) and is exercised by the web app, the Android app and the
experiments.

### Theory course — BCSE308L

| Module | Topic in the syllabus | Where it is in ScamShield |
|---|---|---|
| 1 | Layered architecture, protocols and standards | The stack: SMS text → SSP (application) → TCP or ARQ-over-UDP (transport) → IP. `src/scamshield/net/protocol.py` documents the SSP frame layout byte by byte |
| 2 | Packet switching, transmission impairments, performance | `net/channel.py` emulates loss (Bernoulli and Gilbert-Elliott bursts), bit errors, propagation delay, jitter and a bottleneck link; experiments N2–N5 measure goodput, latency and efficiency |
| 3 | Error detection and correction: Hamming code, CRC, checksum | `net/errorcodes.py`: parity, Internet checksum (RFC 1071), CRC-16-CCITT, CRC-32 (IEEE 802.3), Hamming(7,4). Every SSP frame carries a CRC-32. Experiment N1 measures which errors each check misses |
| 3 | Flow control: sliding window, Go-Back-N, Selective Repeat | `net/arq.py`: Stop-and-Wait, Go-Back-N and Selective Repeat with advertised receive windows. Experiments N2 (loss) and N3 (window size) |
| 4 | IPv4/IPv6 addressing, classful and classless addressing | `net/cidr.py`: IPv4/IPv6 parsing, classful class, CIDR prefix matching, subnetting, the special-purpose address registry. Used to judge where an SMS link really points |
| 6 | TCP and UDP, congestion control, QoS | The detector is served over both TCP (byte stream, frame reassembly) and UDP (datagrams). `arq.py` adds AIMD congestion control (slow start, congestion avoidance, multiplicative decrease) and Jacobson/Karels RTO estimation with Karn's rule. Experiments N4 and N5 |
| 7 | Application layer, DNS | `net/dns.py`: a DNS client and an authoritative DNS server written on raw UDP sockets (RFC 1035 wire format, name compression, A/AAAA/CNAME/PTR/TXT, TC bit with TCP fallback, TTL caching). Experiment N6 |
| 8 | Contemporary issues | Phishing and smishing over SMS; the security mechanisms of the course objectives (integrity through CRC, DNS-based link reputation) |

### Lab course — BCSE308P

| Lab experiment | ScamShield component |
|---|---|
| 2. Error detection and correction mechanisms | `errorcodes.py`, experiment N1, the "Flip a random bit" demo on the web app's Network tab |
| 3. Flow control mechanisms | Stop-and-Wait / Go-Back-N / Selective Repeat in `arq.py`, experiments N2 and N3 |
| 4. IP addressing, classless addressing | `cidr.py`, the subnet calculator in the web app, CIDR checks on every link |
| 6. Socket programming (TCP and UDP) | `service.py` (TCP and UDP servers), `client.py`, and the Android app's TCP client (`Ssp.kt`) |
| 8. Transport-layer protocols and congestion control | AIMD congestion window through an emulated bottleneck queue, experiment N4 (figure 10) |
| 9. DNS client and server resolving a host name or an IP address | `dns.py` client + server, forward (A/AAAA) and reverse (PTR) lookups, the "Resolve a link" tool |

## Novelty

1. **A multilingual, script-true benchmark.** UPI-MixSMS covers English and code-mixed SMS in which the second
   language is written in its own script and banking terms stay in English. The current release has two
   code-mixed settings in two scripts: Hindi–English in Devanagari (आपका SBI account आज block कर दिया जाएगा) and
   Tamil–English in Tamil script (உங்கள் SBI account இன்று block செய்யப்படும், link-ஐ click செய்யவும்). That is how
   people actually type payment messages. Earlier code-mixed scam work uses romanised text only. Every
   language-specific piece (templates, script tables, cue words) sits behind one registry, so adding a language
   is a data change, not a code change. The test split is template-disjoint, so scores measure generalisation to
   new phrasings and not memorisation of templates.
2. **A graded attack scheme that is aware of the script.** Levels L1–L4 go from typos to script-specific attacks
   (confusable letters such as ல/ள/ழ and श/ष/स, vowel-length swaps, a dropped virama, look-alike characters from
   other blocks such as Tamil digits and Gujarati letters, ZWJ/ZWNJ) and, at L4, **transliteration in both
   directions** (English words written in the native script, native words written in Latin letters). This turns
   the "transliteration" problem from the abstract into a measurable attack.
3. **Script-aware canonicalisation** as a defence that needs no retraining. It folds homoglyphs, native look-alike
   characters, separators, leetspeak and native-script loanwords back to a canonical form before classification,
   for every registered script.
4. **Fusing text and network evidence.** The text verdict is combined with link intelligence gathered at the
   network level: DNS resolution, TTL, CNAME chains, and CIDR classification of the resolved addresses. This
   catches a link that resolves into a private or reserved block, which no text model can see.
5. **One model on phone and server, verified to match.** The same model runs on the phone (exact parity with
   Python on 300 test messages) and behind a custom CRC-protected protocol. The protocol is measured under loss,
   congestion and corruption.
