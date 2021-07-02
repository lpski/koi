from ibapi.contract import Contract
import pandas as pd, datetime as dt, pandas_ta as ta, numpy as np, traceback, math
from datetime import datetime
from typing import Dict, List, NamedTuple, Optional, Tuple, Union

from koi.models import CryptoContract, KoiState, StrategyInfo, ContractData, Sentiment, SentimentInfo
from koi.es import fetch_impressions, available_sources

# Helper methods
def _rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    common_names = {
        "Datetime": "datetime",
        "Date": "date",
        "Time": "time",
        "Timestamp": "timestamp",
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Adj Close": "adj_close",
        "Volume": "volume",
        "Unix Timestamp": "unix",
        "Symbol": "symbol",
        "Volume USD": "volume",
        "Day": "day",
        "Local time": "local time"
    }
    df.rename(columns=common_names, errors="ignore", inplace=True)

    # Cleaning
    if 'symbol' in df.columns: df = df.drop(columns=['symbol'])
    return df

def _set_unix_index(df: pd.DataFrame, date_col: str = 'date') -> pd.DataFrame:

    if 'date' not in df.columns:
        if 'local time' in df.columns: # used for coinbase crypto data
            df['date'] = df['local time'].apply(lambda d: datetime.strptime(d, '%d.%m.%Y %H:%M:%S.%f %Z%z'))
        elif 'unix' in df.columns:
            df['date'] = df['unix'].apply(datetime.fromtimestamp)
    elif 'date' in df.columns and not isinstance(df['date'].iloc[-1], datetime):
        # Parse date strings to actual datetime objects
        df['date'] = df['date'].apply(lambda d: datetime.strptime(d, '%Y-%m-%d %H:%M:%S'))

    if 'unix' not in df.columns and 'date' not in df.columns:
        df['date'] = list(map(datetime.fromtimestamp, df.index.tolist()))
        df['unix'] = df.index.tolist()
    elif 'unix' not in df.columns and 'date' in df.columns:
        if isinstance(df[date_col].iloc[0], str):
            df['date'] = df[date_col].apply(lambda d: datetime.strptime(d, '%Y-%m-%d %H:%M:%S'))
        df['unix'] = list(map(lambda d: int(d.strftime('%s')), list(df[date_col])))


    # if 'date' not in df.columns: # set simplified date string if it doesn't exst
    #     df['date'] = list(map(lambda d: d.strftime('%Y-%m-%d %H:%M:%S'), list(df.index)))

    df['day_time'] = df['date'].apply(lambda d: int(d.hour))

    df.set_index('unix', inplace=True)
    df.reset_index(inplace=True)
    return df



def apply_without_strategies(df: pd.DataFrame):
    """Cleans given dataframe"""
    df = _rename_columns(df)
    df = _set_unix_index(df)
    return df






# Utils
def apply_labels(df: pd.DataFrame, label_source_col: str = 'close', lookback: int = 3, threshold: float = .001) -> np.ndarray:
    """
    Applies desired labels to df rows
    """

    labels = df[label_source_col].diff().shift(-lookback).rolling(lookback).sum().values
    sma = df['close'].shift(-lookback).rolling(lookback).mean().values
    for i in range(len(labels)):
        target_diff = sma[i] * threshold
        if labels[i] < -target_diff: labels[i] = 0
        elif labels[i] > target_diff: labels[i] = 2
        else: labels[i] = 1
    
    return labels


def apply_strategies(sym: str, df: pd.DataFrame, granularity: str, specific_fields: List[str] = None, indicator_periods: List[int] = [3, 8, 15, 30, 60], lookback: int = 1, labels: bool = False, sentiment: bool = False, log: bool = False) -> pd.DataFrame:
    """
    Apply any desired transformations to your dataframs
    """
    return df















class AppContracts(NamedTuple):
    stocks: List[ContractData]
    cryptos: List[CryptoContract]

def extract_contracts(strategies: List[StrategyInfo]) -> AppContracts:
    """Given a list of strategies, returns a list of all unique contracts"""
    symbols = set()
    stocks: List[ContractData] = []
    cryptos: List[CryptoContract] = []

    for s in strategies:
        for c in s.contracts:
            if s.crypto:
                if f'{c.market}-{c.currency}' in symbols: continue
                symbols.add(f'{c.market}-{c.currency}')
                cryptos.append(c)
            else:
                if c.symbol in symbols: continue
                symbols.add(c.symbol)
                stocks.append(c)
    
    return AppContracts(stocks, cryptos)



class BarData(NamedTuple):
    instrument_symbol: str
    data: pd.DataFrame
    used_cache: bool



class ApplyConfig(NamedTuple):
    strategies: bool = True
    labels: bool = False
    lookbacks: Dict[str, int] = None
    specific_strategies: Dict[str, List[str]] = None

class Market:
    tick_streaming_enabled: bool = False
    latest_ticks: Dict[str, any]
    latest_price: Dict[str, float]

    def __init__(self, state: KoiState):
        pass

    def get_historical_data(self, contracts: Union[List[Contract], List[CryptoContract]], size: Union[str, int] = '5 mins', duration: str = '7 D', end_date: Union[datetime, str] = '' , use_cached_if_available: bool = False, apply_config: ApplyConfig = None) -> List[Tuple[str, pd.DataFrame]]:
        pass

    def toggle_tick_streaming(self):
        pass

    def disconnect(self):
        pass

    def get_latest_ticks(self) -> Dict[str, dict]:
        pass


    def get_ticks_df(self) -> Dict[str, pd.DataFrame]:
        """
        Converts current symbol objects to a dictionary mapping a symbol to
        the last observed history for that symbol
        """
        relevant_cols = ['ask', 'askSize', 'prevAskSize', 'bid', 'bidSize', 'high', 'low', 'close', 'time']
        new_rows = {
            sym: pd.DataFrame([ticker.__dict__], columns=relevant_cols) for (sym, ticker) in self.latest_ticks.items()
        }
        return new_rows



class CryptoOrder(NamedTuple):
    symbol: str
    side: str
    quantity: float
    price: Optional[float] = None
