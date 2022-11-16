from abc import ABC, abstractmethod
from typing import List, Union, Optional

import pandas as pd
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.base import TransformerMixin, BaseEstimator
from sklearn.preprocessing import StandardScaler, OneHotEncoder

from sklearn.linear_model import LinearRegression
from sklearn.ensemble import ExtraTreesRegressor, GradientBoostingRegressor

# from sklearn.linear_model import Lasso, Ridge, LinearRegression
# from sklearn.feature_extraction import DictVectorizer
# import xgboost as xgb
# from sklearn.svm import LinearSVR


class ToDictTransformer(TransformerMixin, BaseEstimator):
    def __init__(self):
        self.columns = None

    def fit(self, df, y=None):
        return self

    def transform(self, df):
        return df.to_dict(orient='records')

    def get_feature_names_out(self, *args, **kwargs):
        return self.columns


class _Model(ABC):
    @abstractmethod
    def fit(self, X_train: Union[List[dict], pd.DataFrame], y_train: pd.Series) -> None:
        pass

    @abstractmethod
    def predict(self, X: Union[List[dict], pd.DataFrame]) -> np.ndarray:
        pass


class LinReg(_Model):
    def __init__(self, categorical=List[str], numerical=List[str], **kwargs) -> None:

        """
        Linear Regression
        Parameters:
        categorical: List[str]
            List of categorical columns
        numerical: List[str]
            List of numerical columns
        **kwargs:
            Parameters to pass to sklearn's LogisticRegression class
        """

        self.callbacks = []
        self.__model = LinearRegression(**kwargs)
        self.__scaler = StandardScaler()
        self.__ohe = OneHotEncoder()

        self.__transformer = ColumnTransformer(
            [
                ('cat_cols', self.__ohe, categorical),
                ('num_cols', self.__scaler, numerical),
            ],
            remainder='drop',
        )
        self.__pipeline = Pipeline(
            [('preprocessor', self.__transformer), ('regressor', self.__model)]
        )

    def fit(self, X_train: Union[List[dict], pd.DataFrame], y_train: pd.Series) -> None:
        """
        Fits the model pipeline
        Parameters
        X_train: List[dicts] | DataFrame
            List of dictionaries with the X_train examples
        y_train: pd.Series
            Series of y true values
        """
        if isinstance(X_train, List):
            self.__pipeline.fit(pd.DataFrame(X_train), y_train)
        else:
            self.__pipeline.fit(X_train, y_train)
        """
        print(self.__pipeline.named_steps)
        print(
            self.__pipeline.named_steps['preprocessor']
            .named_transformers_['cat_cols']
            .categories_
        )
        """

        return self

    def predict(self, X: Union[List[dict], pd.DataFrame]) -> np.ndarray:
        """
        Makes predictions. Calls to predict method of Pipeline class
        Parameters:
        X: List[dicts] | DataFrame
            List of dicts for wich to make predictions
        Returns:
            ndarray
        """
        if isinstance(X, List):
            pred = self.__pipeline.predict(pd.DataFrame(X))
        else:
            pred = self.__pipeline.predict(X)

        if self.callbacks is not None:
            for callback in self.callbacks:
                callback(pred)
        return pred


class GBRegressor(_Model):
    def __init__(self, categorical=List[str], numerical=List[str], **kwargs) -> None:

        """
        GradientBoostingRegressor
        Parameters:
        categorical: List[str]
            List of categorical columns
        numerical: List[str]
            List of numerical columns
        **kwargs:
            Parameters to pass to sklearn's GradientBoostingRegressor class
        """

        self.callbacks = []
        self.__model = GradientBoostingRegressor(**kwargs)
        self.__scaler = StandardScaler()
        self.__ohe = OneHotEncoder()

        self.__transformer = ColumnTransformer(
            [
                ('cat_cols', self.__ohe, categorical),
                ('num_cols', self.__scaler, numerical),
            ],
            remainder='drop',
        )
        self.__pipeline = Pipeline(
            [('preprocessor', self.__transformer), ('regressor', self.__model)]
        )

    def fit(self, X_train: Union[List[dict], pd.DataFrame], y_train: pd.Series) -> None:
        """
        Fits the model pipeline
        Parameters
        X_train: List[dicts] | DataFrame
            List of dictionaries with the X_train examples
        y_train: pd.Series
            Series of y true values
        """
        if isinstance(X_train, List):
            self.__pipeline.fit(pd.DataFrame(X_train), y_train)
        else:
            self.__pipeline.fit(X_train, y_train)
        """
        print(self.__pipeline.named_steps)
        print(
            self.__pipeline.named_steps['preprocessor']
            .named_transformers_['cat_cols']
            .categories_
        )
        """

        return self

    def predict(self, X: Union[List[dict], pd.DataFrame]) -> np.ndarray:
        """
        Makes predictions. Calls to predict method of Pipeline class
        Parameters:
        X: List[dicts] | DataFrame
            List of dicts for wich to make predictions
        Returns:
            ndarray
        """
        if isinstance(X, List):
            pred = self.__pipeline.predict(pd.DataFrame(X))
        else:
            pred = self.__pipeline.predict(X)

        if self.callbacks is not None:
            for callback in self.callbacks:
                callback(pred)
        return pred
