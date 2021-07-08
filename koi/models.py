from datetime import datetime
from enum import Enum
import json
from math import isnan
import numpy as np
from typing import Any, NamedTuple, Union, Dict, List
from ib_insync.contract import Forex, Stock, Index
from ibapi.contract import Contract

from koi.portfolio import Portfolio
from koi.modeling.modeling_models import ModelParams




# BUY SELL
class Direction(Enum):
    Down = 'down'
    Unsure = 'unsure'
    Up = 'up'

class Prediction(NamedTuple):
    source: str
    direction: Direction
    confidence: float
    description: str = ''
    meta: Dict[str, Any] = None

class Indicator(object):
    # If field value is below/above target (decided by direction), follow signal
    signal: str
    direction: str
    field: str
    target: float
    description: str = ''
    accuracy: float = 0

    @classmethod
    def from_json(cls, data: dict):
        return cls(**data)

    def __init__(self, signal: str, direction: str, field: str, target: float, description: str, accuracy: float = 0):
        self.signal = signal
        self.direction = direction
        self.field = field
        self.target = target
        self.description = description
        self.accuracy = accuracy

class CryptoContract(object):
    market: str
    currency: str
    symbol: str

    def __init__(self, market: str, currency: str):
        self.market = market
        self.currency = currency
        self.symbol = f'{self.market}-{self.currency}'

    # def symbol(self) -> str:
    #     return f'{self.market}-{self.currency}'

    @classmethod
    def from_json(cls, data: dict):
        if 'symbol' in data: del data['symbol']
        return cls(**data)



class Move(Enum):
    Sell = -1
    Hold = 0
    Buy = 1

class TransactionType(Enum):
    MarketSell = -1
    MarketBuy = 1



class BuyQuantity(Enum):
    Half = 0
    Max = 1

class Opportunity(object):
    contract: Union[Contract, CryptoContract]
    confidence: float
    description: str

    def __init__(self, contract: Union[Contract, CryptoContract], confidence: float, description: str = ''):
        self.contract = contract
        self.confidence = confidence
        self.description = description

class Decision(object):
    move: Move
    contract: Union[Contract, CryptoContract]
    quantity: Union[float, BuyQuantity]
    confidence: float
    reason: str
    symbol: str

    def __init__(self, move: Move, contract: Union[Contract, CryptoContract], quantity: Union[float, BuyQuantity], confidence: float, reason: str = ''):
        self.move = move
        self.contract = contract
        self.quantity = quantity
        self.confidence = confidence
        self.reason = reason
        self.symbol = contract.symbol


class Transaction(object):
    succeeded: bool
    transaction_type: TransactionType
    strike: float
    quantity: float
    symbol: str
    confidence: float
    date: str
    reason: str # decision factor that led to transaction
    
    def __init__(self, success: bool, type: TransactionType, strike: float, quantity: float, decision: Decision, date: str):
        self.succeeded = success
        self.transaction_type = type
        self.strike = strike
        self.quantity = quantity
        self.symbol = decision.symbol
        self.confidence = decision.confidence
        self.reason = decision.reason
        self.date = date


class TransactionReport(object):
    date: str
    symbol: str
    transaction_type: TransactionType
    strike: float
    quantity: float
    confidence: float
    hold_length: int # for sells only
    tradePL: float # for sells only
    portfolioPL: float
    totalPL: float
    reason: str

    def __init__(self, date: str, transaction: Transaction, tradePL: float, portfolioPL: float, totalPL: float, hold_length: int):
        self.date = date
        self.symbol = transaction.symbol
        self.transaction_type = transaction.transaction_type
        self.strike = transaction.strike
        self.quantity = transaction.quantity
        self.confidence = transaction.confidence
        self.reason = transaction.reason
        self.tradePL = tradePL
        self.portfolioPL = portfolioPL
        self.totalPL = totalPL
        self.hold_length = hold_length

    def to_safe_dict(self) -> dict:
        data = self.__dict__.copy()
        if isnan(self.hold_length): data['hold_length'] = 0
        if isnan(self.tradePL): data['tradePL'] = 0

        # convert date if needed
        if isinstance(self.date, datetime):
            data['date'] = datetime.strftime(self.date, '%Y/%m/%d %H:%M:%S')

        # convert transaction type to string format
        data['transaction_type'] = 'Sell' if self.transaction_type == TransactionType.MarketSell else 'Buy'

        return data







# Trading
class TradeConfig(object):
    """
    trade_frequency: frequency of trading interval in seconds
    stop_loss_pct: percentage of loss to trigger stop loss
    recent_data_duration: amt of data fetched immediately prior to beginning trading, after training & analysis
    train_duration: size of data to train on (e.g. '5d', '1y')
    train_pct: percentage of data to train on vs test on
    """
    trade_frequency: int = 300
    stop_loss_pct: float = 0.03
    recent_data_duration: Union[str, None] = None
    train_duration: Union[str, None] = None
    train_pct: float = 0.7

    def __init__(self, trade_frequency: int = 300, stop_loss_pct: float = 0.03, recent_data_duration: Union[str, None] = None, train_duration: Union[str, None] = None, train_pct: float = 0.7) -> None:
        self.trade_frequency = trade_frequency
        self.stop_loss_pct = stop_loss_pct
        self.recent_data_duration = recent_data_duration
        self.train_duration = train_duration
        self.train_pct = train_pct

    @classmethod
    def from_json(cls, data: dict):
        return cls(**data)



class CB_Order(object):
    id: str = ''
    price: str = ''
    size: str= ''
    product_id: str= ''
    side: str= ''
    stp: str= ''
    type: str= ''
    time_in_force: str= ''
    post_only: bool = False
    created_at: str = ''
    fill_fees: str = ''
    filled_size: str = ''
    executed_value: str = ''
    status: str = ''
    settled: bool = False
    funds: str = ''
    message: str = ''
    profile_id: str = ''
    done_at: str = ''

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

 

    @classmethod
    def from_json(cls, data: dict):
        return cls(**data)


class CB_Account(NamedTuple):
    id: str
    currency: str
    balance: str
    available: str
    hold: str
    profile_id: str
    trading_enabled: bool

    # Example
    # {
    #     "id": "e316cb9a-0808-4fd7-8914-97829c1925de",
    #     "currency": "USD",
    #     "balance": "80.2301373066930000",
    #     "available": "79.2266348066930000",
    #     "hold": "1.0035025000000000",
    #     "profile_id": "75da88c5-05bf-4f54-bc85-5c775bd68254",
    #     "trading_enabled": true
    # }

    @classmethod
    def from_json(cls, data: dict):
        return cls(**data)





# ANALYSIS
class Sequence(object):
    size: int
    start_index: int
    cumulative_diff: float

    def __init__(self, size: int, start: int, diff: float):
        self.size = size
        self.start_index = start
        self.cumulative_diff = diff


class ExtremesData(object):
    sum: float
    average: float
    field_averages: Dict[str, float]
    
    def __init__(self, averages: Dict[str, float], sequences: List[Sequence]):
        self.field_averages = averages

        # analyze sequences
        seq_diffs = [seq.cumulative_diff for seq in sequences]
        self.sum = np.sum(seq_diffs)
        self.average = np.mean(seq_diffs)


class WindowData(object):
    positive_extremes_averages: Dict[str, ExtremesData]
    negative_extremes_averages: Dict[str, ExtremesData]
    overall_field_averages: Dict[str, float]
    overall_field_std: Dict[str, float]
    
    def __init__(self):
        self.positive_extremes_averages = {}
        self.negative_extremes_averages = {}
        self.overall_field_averages = {}
        self.overall_field_std = {}

    def to_dict(self):
        data = self.__dict__.copy()
        data['positive_extremes_averages'] = {size: d.__dict__ for size, d in self.positive_extremes_averages.items()}
        data['negative_extremes_averages'] = {size: d.__dict__ for size, d in self.negative_extremes_averages.items()}
        return data


class AnalysisData(object):
    sequences: List[Sequence]
    window_size_data: Dict[str, WindowData]
    
    def __init__(self):
        self.sequences = []
        self.window_size_data = {}


    def to_dict(self):
        data = self.__dict__.copy()
        data['sequences'] = list(map(lambda s: s.__dict__, self.sequences))
        data['window_size_data'] = { size: d.to_dict() for size, d in self.window_size_data.items() }
        return data


class AnalysisConfig(NamedTuple):
    duration: str = '7 D'
    end_date: str = ''
    correlation_threshold: float = 0.035
    accuracy_threshold: float = .65
    extremes_pct: float = 0.37
    use_cached: bool = True

    @classmethod
    def from_json(cls, data: dict):
        return cls(**data)


class SymbolData(object):
    indicators: Dict[str, List[Indicator]]
    low_vol_marker: float
    high_vol_marker: float
    very_high_vol_marker: float
    timestamp: int
    
    def __init__(self, indicators: Dict[str, List[Indicator]] = None, low_vol_marker: float = None, high_vol_marker: float = None, very_high_vol_marker = None, timestamp: float = None):
        if indicators is not None: self.indicators = indicators
        else: self.indicators = {}

        if low_vol_marker is not None: self.low_vol_marker = low_vol_marker
        else: self.low_vol_marker = 0

        if high_vol_marker is not None: self.high_vol_marker = high_vol_marker
        else: self.high_vol_marker = 0

        if very_high_vol_marker is not None: self.very_high_vol_marker = very_high_vol_marker
        else: self.very_high_vol_marker = 0

        if timestamp is not None: self.timestamp = timestamp
        else: self.timestamp = datetime.now().timestamp()

    def to_dict(self):
        raw = self.__dict__.copy()
        raw['indicators'] = { field: [indc.__dict__ for indc in field_indcs] for field, field_indcs in self.indicators.items() }
        return raw

    @classmethod
    def from_json(cls, raw: dict):
        indicators = { field: [Indicator.from_json(indc) for indc in field_indcs] for field, field_indcs in raw['indicators'].items() }
        del raw['indicators']
        return cls(**raw, indicators=indicators)

class Analysis(object):
    analyzed_symbols: List[str]
    fields: List[str]
    data: Dict[str, SymbolData]
    
    def __init__(self, fields: List[str] = None, data: Dict = None, analyzed_symbols: List[str] = None):
        if fields is not None: self.fields = fields
        else: self.fields = []

        if data is not None: self.data = data
        else: self.data = {}

        if analyzed_symbols is not None: self.analyzed_symbols = analyzed_symbols
        else: self.analyzed_symbols = []

    def to_dict(self):
        raw = self.__dict__.copy()
        raw['data'] = { sym: sym_data.to_dict() for sym, sym_data in self.data.items() }
        return raw

    @classmethod
    def from_json(cls, raw: dict):
        data = { sym: SymbolData.from_json(sym_data) for sym, sym_data in raw['data'].items() }
        del raw['data']
        return cls(**raw, data=data)





# BACKTESTS
class BacktestConfig(object):
    analysisConfig: Union[AnalysisConfig, None] = None

    @classmethod
    def from_json(cls, data: dict):
        return cls(**data)









# STATE MANAGEMENT
class ContractType(Enum):
    FOREX = 0
    STOCK = 1

class ContractData(object):
    symbol: str
    exchange: str
    whatToShow: str
    contract_type: str
    pair: str
    primaryExchange: str
    currency: str

    def __init__(self, symbol: str, exchange: str, whatToShow: str, contract_type: str, pair: str = None, primaryExchange: str = None, currency: str = 'USD'):
        self.symbol = symbol
        self.exchange = exchange
        self.whatToShow = whatToShow
        self.contract_type = contract_type
        self.pair = pair
        self.primaryExchange = primaryExchange
        self.currency = currency

    def to_contract(self) -> Contract:
        if self.contract_type == 'FOREX':
            return Forex(self.pair, self.exchange)
        elif self.contract_type == 'STOCK':
            return Stock(self.symbol, self.exchange, self.currency, primaryExchange=self.primaryExchange)
        elif self.contract_type == 'INDEX':
            return Index(self.symbol, self.exchange, self.currency)



    @classmethod
    def from_contract(cls, contract: Contract):
        to_show, c_type = '', ''
        pair, primaryExchange = '', ''
        if isinstance(contract, Forex):
            to_show = 'MIDPOINT'
            c_type = 'FOREX'
            pair = contract.pair()
        elif isinstance(contract, Stock):
            to_show = 'TRADES'
            c_type = 'STOCK'
            primaryExchange = 'ISLAND'
        elif isinstance(contract, Index):
            to_show = 'TRADES'
            c_type = 'INDEX'
        
        return cls(symbol=contract.symbol, exchange=contract.exchange, whatToShow=to_show, contract_type=c_type, pair=pair, primaryExchange=primaryExchange, currency=contract.currency)
    
    @classmethod
    def from_json(cls, data: dict):
        return cls(**data)



class StrategyInfo(object):
    name: str
    equity: float # Total value of owned stocks
    available_capital: float # Liquid Cash
    initial_capital: float # Strategy starting capital
    active: bool = False
    start_date: str
    crypto: bool
    contracts: Union[List[ContractData], List[CryptoContract]]
    portfolios: Dict[str, Portfolio] # Mappings of contract symbols to portfolio states
    indicators: Dict[str, Dict[str, List[Indicator]]]

    # strategy configs
    analysis_config: Union[AnalysisConfig, None]
    cnn_config: Union[ModelParams, None]
    trade_config: TradeConfig

    @classmethod
    def from_json(cls, name: str, data: dict):
        # Format contract data
        contracts = []
        if 'contracts' in data:
            if data['crypto']: contracts = list(map(lambda c: CryptoContract.from_json(c), data['contracts']))
            else: contracts = list(map(lambda c: ContractData.from_json(c), data['contracts']))
            del data['contracts']

        # Format configs
        trade_config = TradeConfig.from_json(data['trade_config'])
        del data['trade_config']

        analysis_config = None
        if 'analysis_config' in data:
            analysis_config = AnalysisConfig.from_json(data['analysis_config'])
            del data['analysis_config']

        
        cnn_config = None
        if 'cnn_config' in data:
            cnn_config = ModelParams.from_json(data['cnn_config'])
            del data['cnn_config']

        # Extract indicators
        if 'indicators' in data:
            indicators = { sym: { field: [Indicator.from_json(indc) for indc in field_indcs] for field, field_indcs in field_data.items() } for sym, field_data in data['indicators'].items() }
            del data['indicators']
        else: indicators = {}

        return cls(name, **data, contracts=contracts, trade_config=trade_config, analysis_config=analysis_config, indicators=indicators, cnn_config=cnn_config)


    def __init__(self, name: str, equity: float = 0, available_capital: float = 0, initial_capital: float = 0, contracts: List[ContractData] = [], portfolios: Dict[str, Portfolio] = {}, start_date: str = '', trade_config: TradeConfig = TradeConfig(), analysis_config: AnalysisConfig = None, crypto: bool = False, indicators: Dict[str, Dict[str, List[Indicator]]] = {}, cnn_config: ModelParams = None):
        self.name = name
        self.equity = equity
        self.available_capital = available_capital
        self.initial_capital = initial_capital
        self.contracts = contracts
        self.portfolios = portfolios
        self.start_date = start_date
        self.analysis_config = analysis_config
        self.trade_config = trade_config
        self.crypto = crypto
        self.indicators = indicators
        self.cnn_config = cnn_config





class KoiState(object):
    strategies: List[StrategyInfo]
    ib_connected: bool
    market_ticks_streaming: bool
    crypto_ticks_streaming: bool

    def __init__(self, strategies: Dict[str, StrategyInfo]):
        self.strategies = strategies

    
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

    @classmethod
    def from_json(cls, data: dict):
        strategies = [StrategyInfo.from_json(name, info) for name,info in data['strategies'].items()]
        return cls(strategies)




class Sentiment(NamedTuple):
    symbol: str
    source: str
    timestamp: int
    rating: float

class SentimentInfo(dict):
    # lt = long term, mt = mid term, st = short term
    impressions: List[Sentiment]

