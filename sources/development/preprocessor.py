"""
Export a preprocessor class for processing datasets and generate train/val sets and
DictVectorizer

Classes:

    Preprocessor

"""

from typing import List
from datetime import datetime

import numpy as np
import pandas as pd
import seaborn as sns
import downloader
from sklearn.feature_extraction import DictVectorizer


class Preprocessor:
    def __init__(self, verbose: bool = False, analyse: bool = False):

        self.verbose = verbose
        self.analyse = analyse

    def read_dataframe_csv(self, file_path: str, parse_dates: List[str]):

        df = pd.read_csv(file_path, parse_dates=parse_dates)
        df.columns = df.columns.str.lower().str.replace(' ', '_')
        output_file_name = file_path.replace('csv', 'parquet')
        df.to_parquet(output_file_name, engine='pyarrow', index=None)

        return output_file_name

    def read_dataframe_parquet(self, file_path: str):

        return pd.read_parquet(file_path)

    def analyse_dataframe(self, df: pd.DataFrame, target: str = None):

        print('Analysing dataset...')
        print(f'shape: {df.shape}')
        print(f'types:\n{df.dtypes}')
        print(df.head().T)

        categorical_columns = list(df.dtypes[df.dtypes == 'object'].index)
        numerical_columns = list(df.dtypes[df.dtypes != 'object'].index)

        for column in df.columns:
            print('\n' + column)
            if column in categorical_columns:
                print('Suggested type: categorical')
            else:
                print('Suggested type: numerical')
            nuniques = df[column].nunique()
            if nuniques < 50:
                print(column, df[column].unique())
            else:
                print(f'Number of uniques values is {nuniques}')

            print(f'Number of nulls: {df[column].isnull().sum()}')

        sns.displot(df[target], kind='kde')
        print(f'\ndescription of {target}:')
        print(
            df[target].describe(
                percentiles=[0.01, 0.05, 0.1, 0.2, 0.75, 0.95, 0.98, 0.99]
            )
        )
        print(
            '% of trips within 1-60 min: '
            f'{((df[target] >= 60) & (df[target] <= 60*60)).mean()*100:.2f}'
        )

        return numerical_columns, categorical_columns

    def preprocess_data(
        self,
        df: pd.DataFrame,
        categorical_features: List[str],
        numerical_features: List[str],
        target: str = '',
    ):
        """
        drop records where, trip_start_timestamp, trip_seconds are NaNs
        drops records where trip_seconds < 60 or > 4000
        create duration in minutes as target

        categorical fillnans with -1
        categorical to str
        categorical value formatting

        keep only categorical and numerical features
        Return df and target
        """

        df = df[df.trip_seconds.notnull()]
        df = df[df.trip_start_timestamp.notnull()]
        df = df[(df.trip_seconds > 60) & (df.trip_seconds < 3600)]
        df['duration'] = df['trip_seconds'] / 60

        for column in categorical_features:
            if self.verbose:
                print(
                    f'\nFilling {round(df[column].isna().mean()*100,2)}% '
                    f'of nans with -1 in column: {column}'
                )
            df[column].fillna(-1, inplace=True)
            # This will not touch the None values, only the not None types are processed
            df[column] = df[column].astype('str')
            df[column] = df[column].str.lower().str.replace(' ', '_')

        if not target:
            target = ['duration']

        df.drop(
            df.columns.difference(categorical_features + numerical_features + target),
            axis=1,
            inplace=True,
        )

        if self.verbose:
            print(f'\nfinal shape: {df.shape}')
            print(f'\nfinal types:\n{df.dtypes}')
            print(f'\ncategorical_features: {categorical_features}')
            print(f'\nnumerical_features: {numerical_features}')
            print(f'\ntarget: {target}')

        return df[categorical_features + numerical_features], df[target]

    def prepare_dictionaries(
        self,
        df: pd.DataFrame,
        categorical_features: List[str],
        numerical_features: List[str],
    ):

        dicts = df[categorical_features + numerical_features].to_dict(orient='records')
        return dicts

    def prepare_features(
        self,
        dv: DictVectorizer,
        dict_vectorizer: DictVectorizer,
        y: np.ndarray,
        fit: bool = True,
    ):

        if not dv:
            dv = DictVectorizer()
            fit = True

        if fit:
            X = dv.fit_transform(dict_vectorizer)
        else:
            X = dv.transform(dict_vectorizer)

        return X, y.values, dv

    def process(
        self,
        csv_file_path: str,
        parse_dates: List[str],
        target: str,
        categorical_features: List[str],
        dv: DictVectorizer,
        dv_fit: bool = True,
    ):

        file_path = self.read_dataframe_csv(csv_file_path, parse_dates)
        df_raw = self.read_dataframe_parquet(file_path)

        if dv is None:
            dv = DictVectorizer()

        if self.analyse:
            self.analyse_dataframe(df_raw, target)

        df, y = self.preprocess_data(
            df_raw, categorical_features, numerical_features=[]
        )

        dicts = self.prepare_dictionaries(
            df, categorical_features, numerical_features=[]
        )

        X, y, dv = self.prepare_features(dv, dicts, y, dv_fit)

        return X, y, dv, dicts


if __name__ == "__main__":

    DATA_PATH = "../../data/"

    TRAIN_MONTH = 2
    VAL_MONTH = 3
    TEST_MONTH = 4
    TRAIN_SET_NAME = f"Taxi_Trips_2022_{TRAIN_MONTH:02d}.csv"
    VAL_SET_NAME = f"Taxi_Trips_2022_{VAL_MONTH:02d}.csv"
    TEST_SET_NAME = f"Taxi_Trips_2022_{TEST_MONTH:02d}.csv"
    TRAIN_PATHFILE = DATA_PATH + TRAIN_SET_NAME
    VAL_PATHFILE = DATA_PATH + VAL_SET_NAME
    TEST_PATHFILE = DATA_PATH + TEST_SET_NAME

    DATE_FIELDS = ['Trip Start Timestamp', 'Trip End Timestamp']
    CATEGORICAL_FEATURES = ['pickup_community_area', 'dropoff_community_area']
    TARGET = 'trip_seconds'

    print(f'Downloading train set: {TRAIN_SET_NAME}')
    downloader.download_dataset(
        datetime(2022, TRAIN_MONTH, 1), datetime(2022, TRAIN_MONTH, 2), TRAIN_PATHFILE
    )
    print(f'Downloading val set: {VAL_SET_NAME}')
    downloader.download_dataset(
        datetime(2022, VAL_MONTH, 1), datetime(2022, VAL_MONTH, 2), VAL_PATHFILE
    )
    print(f'Downloading test set: {TEST_SET_NAME}')
    downloader.download_dataset(
        datetime(2022, TEST_MONTH, 1), datetime(2022, TEST_MONTH, 2), TEST_PATHFILE
    )

    preprocessor = Preprocessor(verbose=True, analyse=False)
    dv = DictVectorizer()
    X, y, dv, dicts = preprocessor.process(
        TRAIN_PATHFILE, DATE_FIELDS, TARGET, CATEGORICAL_FEATURES, dv=dv, dv_fit=True
    )
