from asyncio.events import AbstractEventLoop
from enum import Enum
from typing import Dict, List, Tuple, Union
import pandas as pd, os
from ibapi.contract import Contract
from pandas.core.series import Series

from koi.analyzer import Analyzer
from koi.models import AnalysisConfig, CryptoContract, Decision, Indicator, StrategyInfo, TradeConfig, TransactionReport, TransactionType, Prediction
from koi.portfolio import Portfolio
from koi.performance import StrategyPerformance
from koi.modeling.cnn import CNN_Manager
from koi.modeling.modeling_models import ModelParams

class StrategyTarget(Enum):
    # non-modeled
    volume = 0  # mixed volume strategies
    mfi = 1     # money flow index
    ecr = 2

    # modeled
    arima = 3
    gmm = 4     # gaussian mixture model 
    rnn = 5     # recursive neural network
    cnn = 6     # convolutional neural network



class StrategyInterface:
    # attributes
    description: str
    name: str
    active: bool = False
    prepared: bool = False
    is_backtest: bool = False
    equity: float = 0
    available_capital: float = 0
    initial_capital: float = 0
    contracts: Union[List[Contract], List[CryptoContract]] = []
    portfolios: Dict[str, Portfolio] = {}
    start_date: str = ''
    performance: StrategyPerformance
    crypto: bool

    trade_config: TradeConfig
    analyzer: Analyzer = None
    analysis_config: Union[AnalysisConfig, None] = None
    cnn_manager: CNN_Manager = None
    cnn_config: Union[ModelParams, None] = None
    targets: List[StrategyTarget]


    # methods
    def __init__(self, info: StrategyInfo, is_backtest: bool = False):
        """Initializes instance of a strategy given a state config"""
        self.equity = info.equity
        self.available_capital = info.available_capital
        self.initial_capital = info.initial_capital
        self.portfolios = info.portfolios
        self.active = info.active
        self.performance = StrategyPerformance(info.initial_capital)
        self.contracts = [c if isinstance(c, CryptoContract) else c.to_contract() for c in info.contracts]
        self.trade_config = info.trade_config
        self.crypto = info.crypto
        self.is_backtest = is_backtest

        # Setup optionals
        if info.analysis_config is not None:
            self.analysis_config = info.analysis_config
            self.analyzer = Analyzer(info.name, info.analysis_config, info.trade_config.trade_frequency, is_backtest)

        if info.cnn_config is not None:
            self.cnn_config = info.cnn_config
            self.cnn_manager = CNN_Manager([c.symbol if isinstance(c, CryptoContract) else c.symbol for c in self.contracts], info.cnn_config)

        

    
    def training_required(self, symbols: List[str]) -> bool:
        """Returns whether the strategy uses targets that require training"""
        if self.targets == [StrategyTarget.cnn]:
            # CNN Training only required if not pre-trained
            return not all([os.path.exists(f'config/models/{symbol}') for symbol in symbols]) or self.cnn_config.flush_models
        else: return any([t in self.targets for t in [StrategyTarget.gmm, StrategyTarget.cnn]])

    def evaluate_funds(self, transactions: List[TransactionReport], latest_states: Dict[str, Series]):
        """Analyzes portfolio states to determine equity and available capital given a list of transactions"""
        for transaction in transactions:
            if transaction.transaction_type == TransactionType.MarketBuy:
                # On buys, we subtract the total transaction cost from the previous available capital
                self.available_capital -= (transaction.quantity * transaction.strike)
            else:
                # On sells, we add the total transaction revenue to the the previous available capital
                self.available_capital += (transaction.quantity * transaction.strike)

            # Equity is now the new available capital plus any portfolio holdings
            portfolio_holdings = sum([latest_states[x.symbol]['close'] * x.quantity for x in self.portfolios.values() if x.has_stock])
            self.equity = self.available_capital + portfolio_holdings


    

    # Delegated methods
    def should_buy(self, df: pd.DataFrame) -> Tuple[bool, float]:
        """Given last n frames, determines if shares should be purchased"""
        pass


    def should_sell(self, df: pd.DataFrame) -> bool:
        """Given last n frames, determines if shares should be sold"""
        pass

    def fit(self, dfs: Dict[str, pd.DataFrame]):
        """Updates calculations with latest movement data"""
        pass
    
    def determine_next_move(self, dfs: Dict[str, pd.DataFrame]) -> Tuple[List[Decision], Dict[str, List[Prediction]]]:
        """Returns the next buy/sell/hold decision based on strategy logic"""
        pass

    def train(self, dfs: Dict[str, pd.DataFrame]):
        """Optional model training method for strategies that require pre-estimation knowledge"""
        pass





    async def prepare(self, train_dfs: Dict[str, pd.DataFrame] = None, analyze_dfs: Dict[str, pd.DataFrame] = None, main_loop: AbstractEventLoop = None):
        """
        Optional method to allow for strategies to kick off pre-trading preparations (e.g. training/analysis)
        """
        pass

    # def modify_contracts(self):
    #     """
    #     Updates the stategy's contracts list and portfolios to reflect new contracts list.
    #         * Also kicks off training/analysis of any new contracts if the strategy requires it 
    #     """
    #     pass


    # def handle_managed_update(self):
    #     """Optional, for strategies which utilize managed portfolios"""
    #     pass

