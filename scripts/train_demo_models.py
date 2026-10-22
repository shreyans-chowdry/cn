"""
Train the models the web demo serves and save them to artifacts/.

    python scripts/train_demo_models.py                 # classical + neural (about 5 minutes on a laptop)
    python scripts/train_demo_models.py --transformer   # also fine-tune DistilmBERT (uses Apple GPU / CUDA if present)

The experiment pipeline already writes these artifacts; use this script when you
only want the demo, or to add the transformer on a machine with a GPU.
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd  # noqa: E402

from scamshield.data.generator import generate  # noqa: E402
from scamshield.metrics import LABELS, all_metrics  # noqa: E402

LAB = {l: i for i, l in enumerate(LABELS)}
ART = ROOT / "artifacts"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--transformer", action="store_true")
    ap.add_argument("--force", action="store_true", help="retrain even if an artifact exists")
    a = ap.parse_args()
    data = ROOT / "data" / "upi_cmx.csv"
    if not data.exists():
        data.parent.mkdir(exist_ok=True)
        generate().to_csv(data, index=False)
    df = pd.read_csv(data)
    adv_p = ROOT / "data" / "train_adv.csv"
    if not adv_p.exists():
        from scamshield.experiments import prepare
        prepare()
    tr, va, te = (df[df.split == s] for s in ("train", "val", "test"))
    tr_adv = pd.read_csv(adv_p)
    ART.mkdir(exist_ok=True)

    from scamshield.models import classical, neural
    jobs = [(classical, n, ".joblib") for n in ("word_lr", "char_lr", "char_svm")] + \
           [(neural, n, ".pt") for n in ("word_bigru", "char_cnn")]
    for mod, name, ext in jobs:
        for regime, d in (("clean", tr), ("adv", tr_adv)):
            out = ART / f"{name}__{regime}{ext}"
            if out.exists() and not a.force:
                print("exists:", out.name)
                continue
            m = mod.make(name).fit(d.text.tolist(), d.label.map(LAB).values, va.text.tolist(), va.label.map(LAB).values)
            f1 = all_metrics(m.predict_proba(te.text.tolist()), te.label.map(LAB).values)["macro_f1"]
            m.save(str(out))
            print(f"saved {out.name}  test macro-F1={f1:.3f}")

    if a.transformer:
        from scamshield.models import transformer
        out = ART / "distil_mbert__clean"
        if not out.exists() or a.force:
            m = transformer.make("distil_mbert", epochs=1)
            m.fit(tr.text.tolist(), tr.label.map(LAB).values, va.text.tolist()[:600], va.label.map(LAB).values[:600])
            m.save(str(out))
            f1 = all_metrics(m.predict_proba(te.text.tolist()), te.label.map(LAB).values)["macro_f1"]
            print(f"saved {out.name}  test macro-F1={f1:.3f}")


if __name__ == "__main__":
    main()
