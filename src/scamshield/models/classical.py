"""Classical baselines: word-level vs character-level TF-IDF with LR / SVM / NB / RF."""
import joblib
import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

WORD_TOKEN = r"(?u)[\w\u0B80-\u0BFF]+"  # \\w alone splits Tamil words at vowel signs


def _word_vec(binary=False, counts=False):
    if counts:
        return CountVectorizer(lowercase=True, token_pattern=WORD_TOKEN, ngram_range=(1, 2), min_df=2)
    return TfidfVectorizer(lowercase=True, token_pattern=WORD_TOKEN, ngram_range=(1, 2), min_df=2,
                           sublinear_tf=True)


def _char_vec():
    return TfidfVectorizer(lowercase=True, analyzer="char_wb", ngram_range=(2, 5), min_df=2,
                           sublinear_tf=True, max_features=200_000)


class SklearnModel:
    family = "classical"

    def __init__(self, name, granularity, pipeline):
        self.name, self.granularity, self.pipe = name, granularity, pipeline

    def fit(self, X, y, Xv=None, yv=None, seed=0):
        self.pipe.fit(list(X), np.asarray(y))
        return self

    def predict_proba(self, X, batch_size=None):
        return self.pipe.predict_proba(list(X))

    def save(self, path):
        joblib.dump(self.pipe, path)

    def load(self, path):
        self.pipe = joblib.load(path)
        return self

    def n_params(self):
        """Feature-space size (vocabulary of the vectoriser) -- the comparable size measure for linear/tree models."""
        vec = self.pipe.steps[0][1]
        return int(len(getattr(vec, "vocabulary_", {})))


def make(name, seed=0):
    lr = lambda: LogisticRegression(C=10.0, max_iter=3000, class_weight="balanced")
    svm = lambda: CalibratedClassifierCV(LinearSVC(C=0.5, class_weight="balanced"), cv=3, method="sigmoid")
    specs = {
        "word_lr": ("word", lambda: Pipeline([("vec", _word_vec()), ("clf", lr())])),
        "char_lr": ("char", lambda: Pipeline([("vec", _char_vec()), ("clf", lr())])),
        "word_svm": ("word", lambda: Pipeline([("vec", _word_vec()), ("clf", svm())])),
        "char_svm": ("char", lambda: Pipeline([("vec", _char_vec()), ("clf", svm())])),
        "word_nb": ("word", lambda: Pipeline([("vec", _word_vec(counts=True)), ("clf", MultinomialNB(alpha=0.3))])),
        "word_rf": ("word", lambda: Pipeline([("vec", _word_vec()),
                                               ("clf", RandomForestClassifier(n_estimators=300, n_jobs=-1,
                                                                              class_weight="balanced",
                                                                              random_state=seed))])),
    }
    gran, factory = specs[name]
    return SklearnModel(name, gran, factory())


NAMES = ["word_nb", "word_rf", "word_lr", "word_svm", "char_lr", "char_svm"]
