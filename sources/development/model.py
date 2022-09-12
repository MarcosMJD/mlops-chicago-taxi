from typing import List

import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction import DictVectorizer


class Model:
    def __init__(self, model: str, params, callbacks: List = []):

        if params:
            self.model = model(**params)
        else:
            self.model = model()

        self.dict = DictVectorizer()
        self.pipeline = make_pipeline(self.dict, self.model)

        self.params = params
        self.callbacks = callbacks

    def preprocess_features(self, data: pd.DataFrame):

        # The data in dataset already has 'id' unique.
        # If not the data is may be added with:
        # data['id'] = data.apply(lambda x: str(uuid.uuid4()), axis = 1)
        return data

    def fit(self, X_dicts, y):

        self.pipeline.fit(X_dicts, y)

    def predict(self, features_dicts):

        pred = self.pipeline.predict(features_dicts)
        for callback in self.callbacks:
            callback(pred)
        return pred
