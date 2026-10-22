"""Run with:  PYTHONPATH=src python -m pytest -q tests"""
import numpy as np

from scamshield.data.generator import generate
from scamshield.data.templates import TEMPLATES, LANGS
from scamshield.metrics import all_metrics, ece, scam_fnr
from scamshield.obfuscation import obfuscate, normalize, edit_rate


def test_templates_are_parallel_across_languages():
    for label, subs in TEMPLATES.items():
        for st, by_lang in subs.items():
            counts = {lg: len(by_lang[lg]) for lg in LANGS}
            assert len(set(counts.values())) == 1, (label, st, counts)


def test_generator_is_deterministic_and_template_disjoint():
    a, b = generate(200, seed=1), generate(200, seed=1)
    assert a.text.tolist() == b.text.tolist()
    train_t = set(a[a.split != "test"].template_id)
    test_t = set(a[a.split == "test"].template_id)
    assert not train_t & test_t


def test_obfuscation_levels():
    t = "Dear customer your SBI account will be blocked, update KYC now at sbi-kyc.xyz and enter PIN"
    assert obfuscate(t, 0, "en", seed=1) == t
    rates = [np.mean([edit_rate(t, obfuscate(t, lv, "en", seed=s)) for s in range(30)]) for lv in range(5)]
    assert rates == sorted(rates), rates           # monotone in level
    for s in range(30):                             # URLs are never touched
        assert "sbi-kyc.xyz" in obfuscate(t, 4, "en", seed=s)


def test_obfuscation_deterministic():
    t = "Aapka refund pending hai, PIN daalein"
    assert obfuscate(t, 3, "hi", seed=5) == obfuscate(t, 3, "hi", seed=5)


def test_normalize_undoes_homoglyphs_and_zero_width():
    assert normalize("K​YС рin") == "kyc pin"
    assert normalize("K.Y.C") == "kyc"


def test_metrics():
    y = np.array([0, 1, 2, 2])
    p = np.eye(3)[[0, 1, 2, 0]]
    m = all_metrics(p, y)
    assert abs(m["fnr_scam"] - 0.5) < 1e-9
    assert scam_fnr(y, np.array([0, 1, 2, 2])) == 0
    assert 0 <= ece(np.full((4, 3), 1 / 3), y) <= 1
