import asyncio, nest_asyncio, os, concurrent.futures, logging, pandas as pd, numpy as np, dotenv, random
from asyncio.events import AbstractEventLoop
from asyncio.tasks import Task
from typing import Dict, List, Union, Tuple
from datetime import datetime
from ib_insync import IB, util, ticker
from ibapi.contract import Contract
from threading import Thread

from koi.models import ContractData, KoiState
from koi.market_data.root import ApplyConfig, Market, apply_strategies, apply_without_strategies, extract_contracts

pd.options.mode.chained_assignment = None  # default='warn'
logging.getLogger('asyncio').setLevel(logging.CRITICAL)
env = dotenv.dotenv_values('.env')

# Helpers
def historical_bars(ib: IB, contract: Contract, bar_size: str = '5 mins', duration: str = '4 D', end_date: Union[str, datetime] = '', loop: AbstractEventLoop = None) -> Tuple[str, pd.DataFrame]:
    """
    Gets data for specified timespan & frequency
    See: https://interactivebrokers.github.io/tws-api/historical_bars.html
    """
    if loop is not None: asyncio.set_event_loop(loop)

    whatToShow = 'MIDPOINT' if contract.exchange == 'IDEALPRO' else 'TRADES'
    try:
        if not ib.isConnected():
            print('Not connected!!\n')
            ib.connect('127.0.0.1', int(env['IB_PORT']), clientId=random.randint(1, 100))

        bars = ib.reqHistoricalData(
            contract,
            endDateTime=end_date,
            durationStr=duration,
            barSizeSetting=bar_size,
            whatToShow=whatToShow,
            useRTH=True,
            # useRTH=False,
            formatDate=1,
            keepUpToDate=False,
            timeout=180
        )

    except Exception as e: raise 'IB_Client: reqHistoricalData error: {}'.format(e)

    barsList = list(bars)
    df = util.df(barsList)
    return (contract.symbol, df)


EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=5)
class IB_Client(Market):
    ib = IB()
    event_loop = asyncio.new_event_loop()
    stream_contracts: List[ContractData] = []
    tickers: List[ticker.Ticker] = []
    latest: Dict[str, ticker.Ticker] = {}
    stream_task: Task = None

    def __init__(self, state: KoiState):
        try:
            asyncio.set_event_loop(self.event_loop)
            nest_asyncio.apply(self.event_loop)

            # Connect to IB
            print("Connecting to TWS...")
            self.ib.connect('127.0.0.1', int(env['IB_PORT']), clientId=random.randint(1, 100))

            # Extract list of all strategy instruments to stream
            if state is not None:
                self.stream_contracts = extract_contracts(state.strategies).stocks

        except Exception as e:
            print('IB_Client Error: ', e)
            # if self.ib.isConnected(): self.ib.disconnect()



    def get_historical_data(self, contracts: List[Contract], size: str = '5 mins', duration: str = '7 D', end_date: Union[datetime, str] = '', use_cached_if_available: bool = False, apply_config: ApplyConfig = None) -> List[Tuple[str, pd.DataFrame]]:
        """Given a list of contracts, executes and waits for historical bar requests in parallel"""        
        asyncio.set_event_loop(self.event_loop)
        print(f'get_historical_data: {duration} @ {size} steps  |  Strategies: {apply_config is not None}')

        # Temp
        # TSLA_2021_04_01_5 mins_15 D
        # inprecise_date_string = '2021_04_01'
        # use_cached_if_available = True
        # End temp

        precise_date_string = datetime.now().strftime('%Y_%m_%d %H_%M_%S') if isinstance(end_date, str) else end_date.strftime('%Y_%m_%d %H_%M_%S')
        inprecise_date_string = datetime.now().strftime('%Y_%m_%d') if isinstance(end_date, str) else end_date.strftime('%Y_%m_%d')
        filepaths = {}
        for c in contracts:
            if int(duration[:2]) > 9 and use_cached_if_available:  filepaths[c.symbol] = f'config/data/{c.symbol}/{c.symbol}_{inprecise_date_string}_{size}_{duration}.csv'
            else: filepaths[c.symbol] = f'config/data/{c.symbol}/{c.symbol}_{precise_date_string}_{size}_{duration}.csv'

        # If allowing use of cache, ensure all contracts are saved, otherwise redownload all
        used_cache = False
        data: List[Tuple[str, pd.DataFrame]] = []
        if use_cached_if_available and all([os.path.isfile(filepaths[c.symbol]) for c in contracts]):
            data = [(c.symbol, pd.read_csv(filepaths[c.symbol])) for c in contracts]
            used_cache = True
            print('get_historical_data:used cache')
        else:
            for c in contracts:
                res = self.event_loop.run_in_executor(EXECUTOR, historical_bars, self.ib, c, size, duration, end_date, self.event_loop)
                data.append(list(self.event_loop.run_until_complete(asyncio.gather(*[res])))[0])


        if not isinstance(data, list): raise Exception('Error retrieving bar data')

        # Save data if it's new
        if use_cached_if_available and not used_cache:
            print('get_historical_data:saving new data to cache')
            for sym, df in data:
                if data is None: continue
                if not os.path.exists(f'config/data/{sym}'): os.mkdir(f'config/data/{sym}')
                if df is not None: df.to_csv(filepaths[sym])

        data = list(filter(lambda d: not isinstance(d, ConnectionError), data))
        if apply_config is not None: data = [(sym, apply_strategies(sym, df, size, specific_fields=(apply_config.specific_strategies[sym] if apply_config.specific_strategies is not None else None), lookback=apply_config.lookbacks[sym], labels=apply_config.labels)) for sym, df in data if df is not None and df.shape[0] > 0]
        else: data = [(sym, apply_without_strategies(df)) for sym, df in data if df is not None and df.shape[0] > 0]

        return data



    
    # Tick Data Streaming / Fetching
    async def begin_tick_monitoring(self, contract_list: List[ContractData]):
        with await self.ib.connectAsync():
            contracts = [c.to_contract() for c in contract_list]
            for contract in contracts: self.ib.reqMktData(contract)

            try:
                async for tickers in self.ib.pendingTickersEvent:
                    if not self.tick_streaming_enabled: raise Exception('disabled')
                    for ticker in tickers:
                        self.latest[str(ticker.contract.symbol)] = ticker
            except Exception as e:
                if str(e) != 'disabled': print('Stream Error:', str(e))
                return


    async def fetch_latest_ticks(self):
        contracts = [c.to_contract() for c in self.stream_contracts]

        for contract in contracts: self.ib.reqMktData(contract)

        while self.tick_streaming_enabled:
            try:
                async for tickers in self.ib.pendingTickersEvent:
                    if not self.tick_streaming_enabled: raise Exception('disabled')
                    for ticker in tickers:
                        self.latest[str(ticker.contract.symbol)] = ticker
            except Exception as e:
                if str(e) != 'disabled': print('Stream Error:', str(e))
                return

            asyncio.sleep(1)

        return True
            
    


    def stream_forever(self, loop: AbstractEventLoop):
        # asyncio.set_event_loop(loop)
        asyncio.set_event_loop(self.event_loop)

        while self.tick_streaming_enabled:
            try:
                task = loop.create_task(self.begin_tick_monitoring(self.stream_contracts))
                self.stream_task = task
                loop.run_until_complete(task)

            except Exception as e: print('Error with tick monitoring:', e)

    def stream_tickers(self):
        """Asynchronously monitors tick streams for all given contracts"""
        self.tick_streaming_enabled = True
        
        Thread(target=self.stream_forever, args=[self.event_loop]).start()

    def toggle_tick_streaming(self):
        if self.tick_streaming_enabled: self.tick_streaming_enabled = False
        else: self.stream_tickers()



    def get_latest_ticks(self) -> Dict[str, dict]:
        data = {}
        for (symbol, ticker) in self.latest.items():
            data[symbol] = {
                'ask': ticker.ask,
                'prevAsk': ticker.prevAsk if not np.isnan(ticker.prevAsk) else ticker.ask,
                'open': ticker.open  if not np.isnan(ticker.open) else ticker.ask,
                'askSize': ticker.askSize,
                'prevAskSize': ticker.prevAskSize if not np.isnan(ticker.prevAskSize) else ticker.askSize,
                'bid': ticker.bid,
                'bidSize': ticker.bidSize,
                'prevBidSize': ticker.prevBidSize if not np.isnan(ticker.prevBidSize) else ticker.bidSize,
                'high': ticker.high if not np.isnan(ticker.high) else ticker.ask,
                'low': ticker.low if not np.isnan(ticker.low) else ticker.ask,
                'close': ticker.close if not np.isnan(ticker.close) else ticker.ask,
                'time': ticker.time.strftime('%Y-%m-%d %H:%M:%S')
            }

        return data