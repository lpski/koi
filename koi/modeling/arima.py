import pandas as pd
import numpy as np
import warnings
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tools.sm_exceptions import ConvergenceWarning
from koi.models import Prediction, Direction

warnings.filterwarnings('ignore', 'Non-stationary starting autoregressive parameters', UserWarning)
warnings.filterwarnings('ignore', 'Maximum Likelihood optimization failed to ', ConvergenceWarning)


# Maximum Likelihood optimization failed to 
def predict(df: pd.DataFrame, order: tuple = (5,1,0)) -> Prediction:
    try:
        diffs = np.array(list(df['price_diff'][-100:]))
        diffs = np.nan_to_num(np.array(diffs))
        model = ARIMA(diffs, order=order)
        model_fit = model.fit()
        pred = model_fit.forecast()[0]

        # TODO: base confidence on trends in the dataframe
        return Prediction('arima', Direction.Up if pred > 0 else Direction.Down, .6, 'arima prediction')
        
    except Exception as e:
        # likely caused by maximum Likelihood optimization not converging
        return Prediction('arima', Direction.Unsure, 0)