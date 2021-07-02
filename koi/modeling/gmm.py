import pandas as pd
import numpy as np
from sklearn import mixture
from sklearn.preprocessing import scale
from random import randint

from koi.models import Direction, Prediction


class GMM(object):
    RANDOM_STATE = 17
    MAX_ITER = 500
    N_INIT = 50
    N_COMPS = 6
    N_SAMPLES = 1000

    modle: mixture.GaussianMixture

    def __init__(self, max_iter: int, n_init: int, n_comps: int, n_samples: int):
        self.MAX_ITER = max_iter
        self.N_INIT = n_init
        self.N_COMPS = n_comps
        self.N_SAMPLES = n_samples


    def train(self, df: pd.DataFrame, symbol: str):
        """Takes random sets of sequential rows in the train dataset for predictions"""
        # print('training gmm for {}'.format(symbol))
        quotes = []
        # for row_set in range(0, 5000):
        for row_set in range(0, 50):
            if row_set % 1000 == 0: print(f'\tGMM:train {symbol} - {row_set}')
            row_quant = randint(10, 30)
            row_start = randint(0, len(df) - row_quant)
            subset = df.iloc[row_start:row_start+row_quant]

            volume_gap = subset['vol_pct_change']
            daily_change = (subset['close'] - subset['open']) / subset['open']
            fract_high = (subset['high'] - subset['open']) / subset['open']
            fract_low = (subset['open'] - subset['low']) / subset['open']
            forecast_variable = (subset['open'].shift(-1) - subset['open'])
            quotes.append(pd.DataFrame({
                'Sequence_ID': [row_set] * len(subset),
                'volume_gap': volume_gap,
                'daily_change': daily_change,
                'fract_high': fract_high,
                'fract_low': fract_low,
                'forecast_variable': forecast_variable
            }))

        # Create df
        quotes_df = pd.concat(quotes)
        quotes_df['volume_gap'].fillna(quotes_df['volume_gap'].mean(), inplace=True)
        quotes_df['daily_change'].fillna(quotes_df['daily_change'].mean(), inplace=True)
        quotes_df['fract_high'].fillna(quotes_df['fract_high'].mean(), inplace=True)
        quotes_df['fract_low'].fillna(quotes_df['fract_low'].mean(), inplace=True)
        quotes_df['forecast_variable'].fillna(quotes_df['forecast_variable'].mean(), inplace=True)

        # Sanitize data
        quotes_df = quotes_df.replace([np.inf, -np.inf], np.nan)
        quotes_df = quotes_df.dropna(how='any')

        # convert cols np arrays
        daily_change = np.array(quotes_df['daily_change'].values)
        fract_high = np.array(quotes_df['fract_high'].values)
        fract_low = np.array(quotes_df['fract_low'].values)
        volume_gap = np.array(quotes_df['volume_gap'].values)
        forecast = np.array(quotes_df['forecast_variable'].values)

        # Scale vals down for better predictions
        X = np.column_stack([
            scale(daily_change),
            scale(volume_gap),
            scale(fract_high),
            scale(fract_low),
            scale(forecast)
        ])

        # print(X)

        # Fit our new model with the created sequences
        self.model = mixture.GaussianMixture(n_components=self.N_COMPS, max_iter=self.MAX_ITER, n_init=self.N_INIT, init_params='random', random_state=self.RANDOM_STATE)
        self.model.fit(X)

        # print('completed gmm training for {}'.format(symbol))
        return True

    def predict(self, df: pd.DataFrame) -> Prediction:
        subset = df[-40:].copy()
        # subset.replace([np.inf, -np.inf], np.nan).dropna(how='all')
        # subset.dropna(how='any')
        subset = subset.replace([np.inf, -np.inf], np.nan).dropna(how='all')
        daily_change = (subset['close'] - subset['open']) / subset['open']
        fract_high = (subset['high'] - subset['open']) / subset['open']
        fract_low = (subset['open'] - subset['low']) / subset['open']
        forecast = (subset['open'].shift(-1) - subset['open'])
        volume_gap = subset['vol_pct_change']

        # convert to np arrays
        daily_change = np.array(daily_change.values)
        fract_high = np.array(fract_high.values)
        fract_low = np.array(fract_low.values)
        volume_gap = np.array(volume_gap.values)
        forecast = np.array(forecast.values)

        # Scale vals down
        X = np.column_stack(np.nan_to_num([
            scale(daily_change),
            scale(volume_gap),
            scale(fract_high),
            scale(fract_low),
            scale(forecast)
        ]))

        hidden_states_prob = self.model.predict_proba(X)
        hidden_states = self.model.predict(X)
        last_state = hidden_states[-1]

        most_likely_next_state = np.argmax(hidden_states_prob[last_state], axis=0)
        state_prediction_confidence = hidden_states_prob[last_state][most_likely_next_state]

        diff_pred = self.model.means_[last_state][0]
        variance = np.diag(self.model.covariances_[last_state])[0]
        confidence = state_prediction_confidence

        # TODO: make prediction direction unsure if low confidence
        return Prediction('gmm', Direction.Up if diff_pred > 0 else Direction.Down, confidence, 'gmm prediction')

