import asyncio, os, pandas as pd, random
from asyncio.events import AbstractEventLoop
from typing import Dict, List, Union
from pandas.io import json

from koi.market_data import Market
from koi.models import Analysis, AnalysisConfig, Direction, Prediction

class MoveData(object):
    avs: Dict[str, float]
    stds: Dict[str, float]

    def __init__(self, df: pd.DataFrame, std: bool = False):
        self.avs, self.stds = {}, {}


class Analyzer:
    name: str
    analysis_size: str
    dfs: Dict[str, pd.DataFrame] = {}
    stage: str = 'inactive' # One of 'inactive' | 'data' | 'sequencing' | 'analysis' | 'complete'
    active: bool = False
    completed: asyncio.Future
    analysis: Analysis = {}
    config: AnalysisConfig
    hour_profit_pct: Dict[str, Dict[int, int]] = {}
    trade_frequency: Union[str, int] = '5 mins'
    backtest: bool = False
    volume_restricted: bool = True

    def __init__(self, name: str, config: AnalysisConfig = AnalysisConfig(), trade_frequency: int = 300, is_backtest: bool = False):
        self.name = name
        self.config = config
        self.analysis_size = config.duration # Set up config
        self.trade_frequency = trade_frequency
        self.backtest = is_backtest

        # Load previous analysis if exists
        if os.path.isfile(f'config/analyses/{"bt_" if is_backtest else ""}{self.trade_frequency}s_{self.config.duration}_analysis_{self.name}.json'):
            try:
                with open(f'config/analyses/{"bt_" if is_backtest else ""}{self.trade_frequency}s_{self.config.duration}_analysis_{self.name}.json', 'r') as f:
                    data = json.loads(f.read())
                    self.analysis = Analysis.from_json(data)
                    print('loaded previous analysis data for:', self.name)
            except Exception as e:
                self.analysis = Analysis()
                print(f'Error Loading {self.name} Analysis: could not read json file')
                print(e)
        else:
            self.analysis = Analysis()



    async def start(self, dfs: Dict[str, pd.DataFrame] = None, md = None, loop: AbstractEventLoop = None, v2: bool = False):
        """Kicks off analysis event flow"""
        if loop is not None: asyncio.set_event_loop(loop)
        else: asyncio.set_event_loop(asyncio.new_event_loop())

        print(f'{self.name}:Analyzer:start:')

        self.active = True
        self.completed = asyncio.Future()

        # Fetch data if not provided
        if dfs is None:
            if md is None or loop is None: raise 'Analyzer Error: No data and no market data entity provided'
            self.dfs = loop.run_until_complete(self.fetch_data(loop, md))

        # Update analyzers stored data & determine which symbols need analyzed (ignore already analyzed)
        for sym, df in dfs.items(): self.dfs[sym] = df

        return True





    def predict(self, symbol: str, df: pd.DataFrame) -> Prediction:
        # Removed implementation
        if random.choice([True, False]):
            return Prediction('analysis', Direction.Up, .8, f'buy buy buy')
        else:
            Prediction('analysis', Direction.Down, .75, f'sell sell sell')


    # Utils
    def to_dict(self):
        data = self.__dict__.copy()
        data['name'] = self.name
        data['analysis'] = self.analysis.to_dict()
        data['config'] = self.config
        return data



