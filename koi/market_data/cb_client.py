import asyncio, os, nest_asyncio, cbpro, pandas as pd, robin_stocks.robinhood as rh
from threading import Thread
from datetime import datetime, timedelta
from time import sleep
from math import ceil
from typing import List, Dict, NamedTuple, Optional, Tuple, Union
from cbpro.authenticated_client import AuthenticatedClient
from cbpro.public_client import PublicClient
from dotenv import dotenv_values

from koi.market_data import apply_strategies, apply_without_strategies, ApplyConfig, Market
from koi.market_data.root import extract_contracts, CryptoOrder
from koi.models import CB_Account, CB_Order, CryptoContract, KoiState
from koi.market_data.helpers.kraken import Client as Kraken
from koi.market_data.helpers.market_models import CryptoOrderStatus, CryptoTick


env = dotenv_values('.env')

class cb_socket(cbpro.WebsocketClient):

    prev_buy_state: Dict[str, CryptoTick] = {}
    latest_buy_state: Dict[str, CryptoTick] = {}
    prev_sell_state: Dict[str, CryptoTick] = {}
    latest_sell_state: Dict[str, CryptoTick] = {}
    
    def on_open(self):
        self.url = "wss://ws-feed.pro.coinbase.com/"
        self.message_count = 0

    def on_message(self, msg):
        self.message_count += 1

        if 'type' in msg and msg['type'] == 'ticker' and 'product_id' in msg:
            product = msg['product_id']
            msg_data = CryptoTick.from_json(msg)
            if msg['side'] == 'buy':
                # update prev & latest buy state
                if product in self.latest_buy_state: self.prev_buy_state[product] = self.latest_buy_state[product]
                else: self.prev_buy_state[product] = msg_data
                self.latest_buy_state[product] = msg_data

            elif msg['side'] == 'sell':
                # update prev & latest sell state
                if product in self.latest_sell_state: self.prev_sell_state[product] = self.latest_sell_state[product]
                else: self.prev_sell_state[product] = msg_data
                self.latest_sell_state[product] = msg_data


    def on_close(self):
        print('CB Socket Closed')




class CB_Client(Market):
    event_loop = asyncio.new_event_loop()
    stream_products: List[str] = []
    exchange: str
    available_balance: Dict
    capital: float
    latest_tick: Dict[str, CryptoTick]

    # Kraken params
    kraken: Kraken = None

    # Coinbase params
    public_client: PublicClient = None
    authed_client: AuthenticatedClient = None
    socket: cb_socket = None
    accounts: List[CB_Account] = []
    sb_api_url = 'https://api-public.sandbox.pro.coinbase.com'
    api_url = 'https://api.pro.coinbase.com'
    # Sandbox credentials
    sb_key = env['COINBASE_KEY_SB']
    sb_passphrase = env['COINBASE_PASSPHRASE_SB']
    sb_secret = env['COINBASE_SECRET_SB']
    # Primary credentials
    key = env['COINBASE_KEY']
    passphrase = env['COINBASE_PASSPHRASE']
    secret = env['COINBASE_SECRET']

    
    def __init__(self, state: KoiState, exchange: str = 'robinhood'):
        try:
            asyncio.set_event_loop(self.event_loop)
            nest_asyncio.apply(self.event_loop)
            self.exchange = exchange
            self.available_balance = {}
            self.public_client = cbpro.PublicClient()
            SANDBOX_MODE = env['CRYPTO_SANDBOX'] == 'True'
            self.latest_tick = {}

            if self.exchange == 'kraken':
                self.kraken = Kraken(SANDBOX_MODE)

            elif self.exchange == 'coinbase':
                if SANDBOX_MODE: self.authed_client = cbpro.AuthenticatedClient(self.sb_key, self.sb_secret, self.sb_passphrase, self.sb_api_url) # sandbox client
                else: self.authed_client = cbpro.AuthenticatedClient(self.key, self.secret, self.passphrase, self.api_url)
                
                api_accounts = self.authed_client.get_accounts()
                if isinstance(api_accounts, list):
                    self.accounts = [CB_Account.from_json(account) for account in api_accounts]
                    print(f'Available CoinBase account balances:', [f'{account.currency}:{account.available}' for account in self.accounts if float(account.available) > 0])
                    for account in self.accounts: self.available_balance[account.currency] = account.available
                else:
                    print('Error fetching coinbase accounts:', api_accounts)

            elif self.exchange == 'robinhood':
                self.authed_client = cbpro.AuthenticatedClient(self.key, self.secret, self.passphrase, self.api_url)
                rh.login(env['RH_LOGIN'], env['RH_PASS'])
                self.capital = rh.load_account_profile()['portfolio_cash']

            # Extract list of all strategy instruments to stream
            if state is not None:
                contracts = extract_contracts(state.strategies).cryptos
                self.stream_products = [c.symbol for c in contracts]

            if self.exchange == 'coinbase':
                print('starting crypto socket: coinbase')
                # Channel options: ['ticker', 'user', 'matches', 'level2', 'full']
                self.socket = cb_socket(channels=['ticker'], products=self.stream_products, auth=False, api_key=self.key, api_secret=self.secret, api_passphrase=self.passphrase)

        except Exception as e:
            print('CB_Client Error: ', e)




    ########
    # DATA 
    ########
    def handle_socket_error(self, e): pass

    def toggle_tick_streaming(self):
        self.socket.on_error = self.handle_socket_error
        if self.exchange == 'kraken':
            if self.tick_streaming_enabled:
                self.kraken.stream_ticks = False
            else:
                Thread(
                    target=self.kraken.start_tick_streaming,
                    args=[self.stream_products]
                ).start()
        elif self.exchange == 'coinbase':
            if self.tick_streaming_enabled:
                try: self.socket.close()
                except Exception as e: pass
            else: self.socket.start()

        self.tick_streaming_enabled = not self.tick_streaming_enabled

    def get_latest_ticks(self) -> Dict[str, dict]:
        data = {}

        if self.exchange == 'kraken':
            for product in self.stream_products:
                # Ensure data for product is present
                if not self.kraken.has_symbol_tick_data(product): continue

                # extract states
                prev_state, latest_state = self.kraken.get_symbol_tick_data(product)

                data[product] = {
                    'ask': latest_state.ask,
                    'prevAsk': prev_state.ask,
                    'askSize': latest_state.ask_size,
                    'prevAskSize': prev_state.ask_size,
                    'open': latest_state.open,
                    'bid': latest_state.bid,
                    'bidSize': latest_state.bid_size,
                    'prevBidSize': prev_state.bid_size,
                    'high': latest_state.high,
                    'low': latest_state.low,
                    'close': latest_state.close,
                    'time': latest_state.time # 2021-01-31T18:04:12.616460Z
                    # 'time': buy_state.time.strftime('%Y-%m-%dT%H:%M:%S.%fZ') # 2021-01-31T18:04:12.616460Z
                }

            return data
        
        elif self.exchange == 'robinhood':
            return {}
        
        else:
            # ticker format: {'type': 'ticker', 'sequence': 13438836927, 'product_id': 'ETH-USD', 'price': '1293.37', 'open_24h': '1377.19', 'volume_24h': '201254.23533537', 'low_24h': '1283', 'high_24h': '1392.23', 'volume_30d': '17943944.12693805', 'best_bid': '1293.25', 'best_ask': '1293.37', 'side': 'buy', 'time': '2021-01-31T18:04:12.616460Z', 'trade_id': 81168541, 'last_size': '0.05770902'}
            
            for product in self.stream_products:
                # Ensure data for product is present
                has_data = product in self.socket.latest_buy_state and product in self.socket.latest_sell_state
                if not has_data: continue

                # extract states
                prev_buy_state, buy_state = self.socket.prev_buy_state[product], self.socket.latest_buy_state[product]
                prev_sell_state, sell_state = self.socket.prev_sell_state[product], self.socket.latest_sell_state[product]

                data[product] = {
                    'ask': sell_state.best_ask,
                    'prevAsk': prev_sell_state.best_ask,
                    'open': buy_state.price,
                    'askSize': sell_state.last_size,
                    'prevAskSize': prev_sell_state.last_size,
                    'bid': buy_state.best_bid,
                    'bidSize': buy_state.last_size,
                    'prevBidSize': prev_buy_state.last_size,
                    'high': sell_state.high_24h,
                    'low': sell_state.low_24h,
                    'close': buy_state.price,
                    'time': buy_state.time # 2021-01-31T18:04:12.616460Z
                    # 'time': buy_state.time.strftime('%Y-%m-%dT%H:%M:%S.%fZ') # 2021-01-31T18:04:12.616460Z
                }

            return data

    def latest_symbol_price(self, symbol: str) -> Tuple[float, float]:
        if self.exchange == 'robinhood':
            print('rh: getting latest price')
            tick = CryptoTick.from_rh_data(rh.get_crypto_quote(symbol.split('-')[0]), symbol)
            self.latest_tick[symbol] = tick
            return float(tick.best_ask), float(tick.best_bid)

        else:
            bid = self.socket.latest_buy_state[symbol].best_bid
            ask = self.socket.latest_buy_state[symbol].best_ask
            return float(ask), float(bid)


    async def get_n_candle_groups(self, contract: CryptoContract, granularity: int, end_date: datetime, duration_seconds: int,  n: int = 6) -> Tuple[str, pd.DataFrame]:
        def fetch_data(iteration: int = 1, df: pd.DataFrame = None) -> pd.DataFrame:
            fut = asyncio.Future()
            offset_per_iter = duration_seconds / n

            if iteration < n + 1:
                iter_end_date = (end_date - timedelta(seconds=(offset_per_iter * (iteration - 1)) ))
                iter_start_date = iter_end_date - timedelta(seconds=offset_per_iter)

                candles = self.public_client.get_product_historic_rates(contract.symbol, start=iter_start_date, end=iter_end_date.isoformat(), granularity=granularity)
                sleep(.25)

                if df is None:
                    df = pd.DataFrame(candles, columns=['unix', 'low', 'high', 'open', 'close', 'volume'])
                    df['unix'].apply(int)
                    df.set_index(['unix'], inplace=True)

                else:
                    new_df = pd.DataFrame(candles, columns=['unix', 'low', 'high', 'open', 'close', 'volume'])
                    new_df['unix'].apply(int)
                    new_df.set_index(['unix'], inplace=True)
                    df = pd.concat([df, new_df])
                    df.sort_index(inplace=True)

                # recursively call fetch_data for the next fetches
                merged: pd.DataFrame = asyncio.get_event_loop().run_until_complete(fetch_data(iteration + 1, df))

                fut.set_result(merged)
                return fut
            else:
                fut.set_result(df)
                return fut


        df: pd.DataFrame = asyncio.get_event_loop().run_until_complete(fetch_data())
        # return (contract.symbol, df.iloc[::-1])
        return (contract.symbol, df)

    def get_historical_data(self, contracts: List[CryptoContract], size: int = 60, duration: str = '7 D', end_date: Union[datetime, str] = '', use_cached_if_available: bool = False, apply_config: ApplyConfig = None) -> List[Tuple[str, pd.DataFrame]]:
        """
        Given a list of contracts, executes and waits for historical bar requests in parallel.
        Coinbase api limits to 300 candles at a time (5 hours worth @ 1 min candles so multiple fetches may be needed
        """
        
        asyncio.set_event_loop(self.event_loop)
        data: List[Tuple[str, pd.DataFrame]] = []

        def duration_in_seconds(timeframe: str):
            # duration_quantity = int(duration[:2])
            duration_quantity = int(duration.split(' ')[0])
            if timeframe == 'D': return duration_quantity * 86400
            elif timeframe == 'H': return duration_quantity * 3600
            elif timeframe == 'M': return duration_quantity * 60
            elif timeframe == 'Y': return duration_quantity * 31556952
            else: return duration_quantity


        # Determine required candles
        duration_seconds = duration_in_seconds(duration[-1:])
        candles = ceil(duration_seconds / size)
        
        # Format cache strings
        precise_date_string = datetime.now().strftime('%Y_%m_%d %H_%M_%S') if isinstance(end_date, str) else end_date.strftime('%Y_%m_%d %H_%M_%S')
        inprecise_date_string = datetime.now().strftime('%Y_%m_%d') if isinstance(end_date, str) else end_date.strftime('%Y_%m_%d')
        filepaths = {}
        for c in contracts:
            if duration_seconds > 1_000_000 and use_cached_if_available:  filepaths[c.symbol] = f'config/data/{c.symbol}/{c.symbol}_{inprecise_date_string}_{size}S_{duration}.csv'
            else: filepaths[c.symbol] = f'config/data/{c.symbol}/{c.symbol}_{precise_date_string}_{size}S_{duration}.csv'
        
        
        # If allowing use of cache, ensure all contracts are saved, otherwise redownload all
        used_cache = False
        if use_cached_if_available and all([os.path.isfile(filepaths[c.symbol]) for c in contracts]):
            print('CB_Client:get_historical_data:used cache')
            data = [(c.symbol, pd.read_csv(filepaths[c.symbol])) for c in contracts]
            used_cache = True
        else:

            end = datetime.now() if isinstance(end_date, str) else end_date
            end_iso = end.isoformat()
            print('CB_Client:Requested end date:', end.strftime('%Y_%m_%d %H_%M_%S'))
    
            if candles <= 300: # Can be fetched in single request
                for contract in contracts:
                    candles = self.public_client.get_product_historic_rates(contract.symbol, end=end_iso, granularity=size)
                    if len(candles) > 1:
                        df = pd.DataFrame(candles, columns=['unix', 'low', 'high', 'open', 'close', 'volume']).iloc[::-1]
                        data.append((contract.symbol, df))
                    else: print(f'No candles available for: {contract.symbol}')
            
            else: # multiple fetches required
                group = asyncio.gather(*[self.get_n_candle_groups(c, size, end, duration_seconds, ceil(candles / 300)) for c in contracts])
                data = list(self.event_loop.run_until_complete(group))

        
        if use_cached_if_available and not used_cache:
            print('CB_Client:get_historical_data:saving new data to cache')
            for sym, df in data:
                if not os.path.exists(f'config/data/{sym}'): os.mkdir(f'config/data/{sym}')
                if df is not None: df.to_csv(filepaths[sym])

        if apply_config is not None: data = [(sym, apply_strategies(sym, df, size, specific_fields=(apply_config.specific_strategies[sym] if apply_config.specific_strategies is not None else None), lookback=apply_config.lookbacks[sym], labels=apply_config.labels)) for sym, df in data if df.shape[0] > 0]
        else: data = [(sym, apply_without_strategies(df)) for sym, df in data if df.shape[0] > 0]

        return data





    ##########
    # ORDERS 
    ##########
    def add_order(self, order: CryptoOrder) -> CryptoOrderStatus:
        if self.exchange == 'kraken':
            info = self.kraken.add_order(order)

        elif self.exchange == 'robinhood':
            print('adding rh order:', order)
            if order.side == 'buy':
                info = rh.order_buy_crypto_limit(order.symbol.split('-')[0], round(order.quantity, 7), round(order.price, 7))  # debug
                # info = rh.order_buy_crypto_limit(order.symbol, order.quantity, order.price)
            elif order.side == 'sell':
                info = rh.order_sell_crypto_limit(order.symbol.split('-')[0], round(order.quantity, 7), round(order.price, 7))

            print('rh order info:', info)
        else:
            if order.price is not None:
                info = self.authed_client.place_limit_order(order.symbol, order.side, price=order.price, size=round(order.quantity, 8))
            else:
                info = self.authed_client.place_market_order(order.symbol, order.side, size=round(order.quantity, 8))

        return CryptoOrderStatus(info, self.exchange)

    def update_order_status(self, status: CryptoOrderStatus):
        if self.exchange == 'kraken':
            return status
        elif self.exchange == 'coinbase':
            latest_status = self.authed_client.get_order(status.id)
        elif self.exchange == 'robinhood':
            latest_status = rh.get_crypto_order_info(status.id)

        print('latest status info:', latest_status)
        return CryptoOrderStatus(latest_status, self.exchange)








    ##########
    # HELPERS 
    ##########
