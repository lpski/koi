import datetime as dt
from typing import Union

class CryptoTick(object):
    product_id: str
    price: str
    open_24h: str
    volume_24h: str
    low_24h: str
    high_24h: str
    volume_30d: str
    best_bid: str
    best_ask: str
    side: str
    time: str
    last_size: str

    def __init__(self, type: str, sequence: str, trade_id: str, product_id: str, price: str, open_24h: str, volume_24h: str, low_24h: str, high_24h: str, volume_30d: str, best_bid: str, best_ask: str, side: str, time: str, last_size: str):
        self.product_id = product_id
        self.price = price
        self.open_24h = open_24h
        self.volume_24h = volume_24h
        self.low_24h = low_24h
        self.high_24h = high_24h
        self.volume_30d = volume_30d
        self.best_bid = best_bid
        self.best_ask = best_ask
        self.side = side
        self.time = time
        self.last_size = last_size

    @classmethod
    def from_json(cls, data: dict):
        return cls(**data)

    @classmethod
    def from_rh_data(cls, data: dict, symbol: str):
        return cls(
            type='', sequence='', trade_id=data["id"], product_id=symbol,
            price=data['mark_price'], open_24h=data['open_price'], volume_24h=data["volume"], low_24h=data["low_price"], high_24h=data["high_price"], volume_30d="",
            best_bid=data["bid_price"], best_ask=data["ask_price"], side='buy', time='', last_size=''
        )



class TickData(object):
    def __init__(self, data: dict, format: str = 'rh'):
        if format == 'rh':
            self.ask = float(data['ask_price'])
            self.bid = float(data['bid_price'])
            self.mark = float(data['mark_price'])
            self.high = float(data['high_price'])
            self.low = float(data['low_price'])
            self.open = float(data['open_price'])
            self.symbol = data['symbol']
            self.id = data['id']
            self.volume = data['volume']
        else:
            self.ask = float(data['ask'])
            self.bid = float(data['bid'])

        self.spread_pct = (self.ask - self.bid) / self.ask * 100



"""

# [548,
    {'a': ['1692.88000', 17, '17.14695000'],
    'b': ['1692.87000', 137, '137.43150142'],
    'c': ['1692.88000', '0.25000000'],
    'v': ['14317.92380552', '31294.58260897'],
    'p': ['1710.28692', '1710.48644'],
    't': [12483, 20971],
    'l': ['1683.06000', '1670.61000'],
    'h': ['1724.63000', '1731.70000'],
    'o': ['1715.00000', '1676.82000']},
'ticker', 'ETH/USD']

"""
class KrakenTick(object):
    product: str
    ask: float
    ask_size: int
    bid: float
    bid_size: int
    high: float
    low: float
    close: float
    open: float
    time: str

    def __init__(self, data: dict, product: str):
        self.product = product

        self.ask = float(data['a'][0])
        self.ask_size = int(data['a'][1])
        self.bid = float(data['b'][0])
        self.bid_size = int(data['b'][1])
        self.high = float(data['h'][1])
        self.low = float(data['l'][1])
        self.close = float(data['c'][0])
        self.open = float(data['o'][1])
        self.time = dt.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%fZ')





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





class CryptoOrderStatus(object):
    id: str
    state: str # One of [queued, unconfirmed, confirmed, partially_filled, filled, rejected, canceled, failed]
    settled: bool = False
    failed: bool = False
    price: float # Average fill price
    fill_quantity: float
    fees: float = 0
    executed_value: float # Total trade value

    def __init__(self, data: dict, exchange: str):
        if exchange == 'robinhood':
            if 'id' not in data: raise Exception(f'No id provided in ', data)
            self.id = data['id']
            self.fees = self.validate_numeric_field(data, 'fees')
            self.price = self.validate_numeric_field(data, 'average_price')
            self.fill_quantity = self.validate_numeric_field(data, 'cumulative_quantity')
            self.executed_value = self.price * self.fill_quantity
            self.state = data['state']
            self.settled = (data['state'] == 'filled')
            self.failed = (data['state'] in ['rejected', 'canceled', 'failed'])

    def validate_numeric_field(self, data: dict, field: str, default: Union[float, int] = 0) -> Union[float, int]:
        if field in data:
            if isinstance(data[field], int) or isinstance(data[field], float): return data[field]
            if isinstance(data[field], str):
                try: return float(data[field]) 
                except: return default
        return default
    