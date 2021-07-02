import asyncio, time
from asyncio.events import AbstractEventLoop
from datetime import datetime, timedelta
from threading import Thread
from typing import Optional, Union, Dict, List
import eel
from ib_insync.contract import Contract, Stock
import pandas as pd
from multiprocessing.pool import ThreadPool
from timeit import default_timer as timer

from koi.broker import Broker
from koi.strategies.root import StrategyInterface
from koi.models import CryptoContract, Decision, Move, TransactionReport
from koi.portfolio import Portfolio
from koi.utils import save_strategy_data, save_transaction, to_bar_size, save_strategy_config
from koi.market_data import Market, apply_strategies, IB_Client, ApplyConfig
from koi.notifier import NotificationService


class Trader:
    """
        The trader is a central piece for backtests & active trading of strategies.
        Event Flow:
            * Fetch initial data to be used for training (if needed) & analysis (if req'd)
            * Trigger training & analysis of each portfolio dataframe in parallel
            * 'Step' is called each strategy-specified time period apart to trigger a buy/sell decision
            * Stategy state is saved upon execution of buy/sell decisions and portfolio updates 
    """
    strategy: StrategyInterface
    broker: Broker
    md: Market
    ns: NotificationService
    dfs: Dict[str, pd.DataFrame] = {}

    active: bool = False
    stage: str = ''

    analysis_dfs: Dict[str, pd.DataFrame] = {}
    train_dfs: Dict[str, pd.DataFrame] = {}

    def __init__(self, strategy: StrategyInterface, marketData: Market, broker: Broker, notifier: NotificationService):
        self.broker = broker
        self.strategy = strategy
        self.md = marketData
        self.ns = notifier




    # Strategy Preparation Methods

    def setup(self, loop: AbstractEventLoop, data_end_date: datetime, start_once_complete: bool = False, dfs: Dict[str, pd.DataFrame] = None):
        """
        Kicks off and controls trader event flow pre-trading
            * Data Fetching (by default, previous 7 days of data)
            * Analysis + Model Training
        """
        asyncio.set_event_loop(loop)

        # Data Fetching (one at a time to allow for cache usage if analysis config & strategy duration match)
        if dfs is not None:
            self.train_dfs = dfs
            self.analysis_dfs = dfs
        elif self.strategy.analysis_config is not None or self.strategy.training_required([c.symbol for c in self.strategy.contracts]):
            th = Thread(target=self.fetch_setup_data, args=[loop, self.strategy.contracts, data_end_date])
            _, _ = th.start(), th.join()

        # Trigger strategy training/analyses
        for sym, df in self.train_dfs.items():
            start_date, end_date = df.iloc[0]['date'], df.iloc[-1]['date']
            print(f'{self.strategy.name}:Trader:{sym} Train Range: ({start_date} -> {end_date})')
        for sym, df in self.analysis_dfs.items():
            start_date, end_date = df.iloc[0]['date'], df.iloc[-1]['date']
            print(f'{self.strategy.name}:Trader:{sym} Analysis Range: ({start_date} -> {end_date})')

        loop.run_until_complete(self.strategy.prepare(self.train_dfs, self.analysis_dfs))

        if start_once_complete:
            th = Thread(target=lambda:loop.run_until_complete(self.start(loop)))
            th.start()

        return True


    def fetch_setup_data(self, loop: AbstractEventLoop, contracts: Union[List[Contract], List[CryptoContract]], end_date: datetime):
        """Obtains & stores analysis & training data required for the trader's strategy"""
        asyncio.set_event_loop(loop)
        bar_size = to_bar_size(self.strategy.trade_config.trade_frequency, self.strategy.crypto)

        pool = ThreadPool(processes=1)
        if self.strategy.analyzer is not None: # Obtain data for analysis if required
            
            # Determine which symbols have not yet been analyzed
            # Only apply strategies if there are unanalyzed symbols
            unanalyzed_contracts = [c for c in contracts if (c.symbol if isinstance(c, CryptoContract) else c.symbol) not in self.strategy.analyzer.analysis.analyzed_symbols]
            fetch_contracts = [c for c in contracts]

            if len(fetch_contracts) > 0:                
                async_result = pool.apply_async(self.md.get_historical_data, (fetch_contracts, bar_size, self.strategy.analysis_config.duration, end_date, True, ApplyConfig(len(unanalyzed_contracts) > 0, True, self.strategy.cnn_manager.lookbacks([c.symbol for c in fetch_contracts]))))
                analysis_data = async_result.get()
            else: analysis_data = {}
    
            for sym, df in analysis_data: self.analysis_dfs[sym] = df
            print(f'{self.strategy.name}:Setup:Analysis Data Fetched')

        if self.strategy.training_required([c.symbol for c in contracts]): # Obtain training data, use analysis_config data if exists and same duration
            # Only fetch data for symbols that don't yet have a model
            # Only apply strategies if there are unanalyzed symbols
            untrained_contracts = [c for c in contracts if (c.symbol if isinstance(c, CryptoContract) else c.symbol) not in self.strategy.cnn_manager.models.keys()]

            fetched_analysis_data = self.strategy.analysis_config and self.strategy.analysis_config.duration == self.strategy.trade_config.train_duration
            if fetched_analysis_data and all([(c.symbol if isinstance(c, CryptoContract) else c.symbol) in self.analysis_dfs for c in untrained_contracts]):
                self.train_dfs = self.analysis_dfs
                print(f'{self.strategy.name}:Setup:Train Data Fetched - Used cached analysis data')
            else:
                async_result = pool.apply_async(self.md.get_historical_data, (untrained_contracts, bar_size, self.strategy.trade_config.train_duration, end_date, True, ApplyConfig(True, True, self.strategy.cnn_manager.lookbacks([c.symbol for c in untrained_contracts]))))
                train_data = async_result.get()
                print(f'{self.strategy.name}:Setup:Train Data Fetched')
                for sym, df in train_data: self.train_dfs[sym] = df

        return True




    # Active Trading Methods

    def start(self, main_loop: AbstractEventLoop):
        """
        Begins trading flow
            * Fetches recent data if required (e.g. arima requires recent data)
            * Sets up portfolios if needed
            * Kicks off step timer
        """
        self.active = True
        self.strategy.active = True
        asyncio.set_event_loop(main_loop)
        fut = asyncio.Future()

        # Prepare strategy if needed
        if not self.strategy.prepared:
            recent_duration = self.strategy.trade_config.recent_data_duration
            if recent_duration is None: train_end_date = datetime.now()
            else: train_end_date = datetime.now() - timedelta(days=int(recent_duration[0]))

            # start setup thread
            th = Thread(target=self.setup, args=[main_loop, train_end_date, False])
            _, _ = th.start(), th.join()


        # Obtain recent data for trading recency models
        if self.strategy.trade_config.recent_data_duration is not None:
            contracts = self.strategy.contracts
            bar_size = to_bar_size(self.strategy.trade_config.trade_frequency, self.strategy.crypto)

            print(f'{self.strategy.name}:Start:Fetching initial data')

            pool = ThreadPool(processes=1)
            async_result = pool.apply_async(self.md.get_historical_data, (contracts, bar_size, self.strategy.trade_config.recent_data_duration, '', False, ApplyConfig(True, False, self.strategy.cnn_manager.lookbacks([c.symbol for c in contracts]), self.strategy.cnn_manager.cols(contracts))))
            initial_data = async_result.get()
            
            print(f'{self.strategy.name}:Start:Initial Data Fetched:')
            self.dfs = { sym: df for sym, df in initial_data }

        # Create portfolio for each df if is not already created
        for sym in self.dfs.keys():
            hold_start = self.dfs[sym].iloc[-1]['close']
            self.strategy.portfolios[sym] = Portfolio(hold_start, stop_loss_pct=self.strategy.trade_config.stop_loss_pct, symbol=sym)

        # Start refresh cycle + wait for good time to start (i.e. cur_minute % frequency = 0 to avoid lag)
        freq = self.strategy.trade_config.trade_frequency
        cur_minute = datetime.now().minute
        if freq > 60:
            freq_mins = freq / 60
            if freq_mins < 60 and cur_minute % freq_mins != 0:  # wait for start of frequency period
                print(f'Waiting {freq_mins - (cur_minute % freq_mins)} minutes for start of frequency period')
                eel.sleep((freq_mins - (cur_minute % freq_mins)) * 60)
            elif freq_mins >= 60 and freq_mins < 1440 and cur_minute != 0:      # wait till top of the hour
                print(f'Waiting {60 - cur_minute} minutes till start of top of the next hour')
                eel.sleep((60 - cur_minute) * 60)
        
        Thread(target=self.start_refresh_cycle, args=(main_loop, fut)).start()


    def start_refresh_cycle(self, loop: AbstractEventLoop, future: asyncio.Future):
        """
        Continously executes move analysis according to
        trader's move frequency until program exit
        """
        while self.active:
            Thread(target=self.step, args=[loop]).start()
            eel.sleep(self.strategy.trade_config.trade_frequency)

        print('\n\n\n\nCOMPLETE\n\n\n')
        future.set_result(True) # tell main thread to close this thread
        return True



    def update_dfs(self, sym: str, df: pd.DataFrame):
        if sym not in self.dfs.keys():
            print(f'WARNING: {sym} not in self.dfs')
            return

        if 'unix' not in self.dfs[sym].columns.tolist():
            self.dfs[sym]['unix'] = self.dfs[sym]['date'].apply(lambda d: d.timestamp())

        latest_row = df.iloc[[-1]]
        existing_timestamps = self.dfs[sym]['unix'].tolist()
        if latest_row.iloc[-1]['unix'] in existing_timestamps:
            print('latest data already in dataframe - skipping update')
            print(df.tail(2))
            return

        # check if we need to merge more than one row (max = 2 for now)
        if df.shape[0] > 1 and df.iloc[-2]['unix'] not in existing_timestamps:
            print('merging multiple')
            df = pd.concat([self.dfs[sym], df.iloc[-2:]], ignore_index=True)
        else:
            df = pd.concat([self.dfs[sym], latest_row], ignore_index=True)

        if len(df) > 200:
            df.drop(df.index[:(len(df) - 200)], inplace=True)

        date = df.iloc[-1]['date']
        print(f'\nUpdated {sym} data for step ending @ {date} | {df.shape[0]} rows')
        if self.strategy.analyzer is not None:
            self.dfs[sym] = apply_strategies(sym, df, self.strategy.trade_config.trade_frequency, list(self.strategy.analyzer.analysis.data[sym].indicators.keys()), lookback=3)
        elif self.strategy.cnn_manager is not None:
            self.dfs[sym] = apply_strategies(sym, df, self.strategy.trade_config.trade_frequency, self.strategy.cnn_manager.cols_for(sym), lookback=self.strategy.cnn_manager.lookbacks([sym])[sym])
        else:
            self.dfs[sym] = apply_strategies(sym, df, self.strategy.trade_config.trade_frequency)
        self.dfs[sym].to_csv(f'config/visited/{self.strategy.name}_{sym}.csv')

        return

    def step(self, loop: AbstractEventLoop):
        """Combine the latest bar with existing data + makes/executes moves + state updates"""
        print(f'\n\n{self.strategy.name}:Step')
        asyncio.set_event_loop(loop)
        start = timer()
        pool = ThreadPool(processes=1)
        async_result = pool.apply_async(self.md.get_historical_data, (self.strategy.contracts, to_bar_size(self.strategy.trade_config.trade_frequency, self.strategy.crypto), f'{self.strategy.trade_config.trade_frequency} S', '', False))
        latest_bars = async_result.get()

        # Update the dfs with latest data in parallel
        ths = [Thread(target=self.update_dfs, args=[sym, df]) for sym, df in latest_bars]
        for th in ths: th.start()
        for th in ths: th.join()

        # Fit the new data and make buy/sell/hold decision
        next_moves, _ = self.strategy.determine_next_move(self.dfs)

        if len(next_moves) > 0: print('Moves:', [f'{m.move} | {m.symbol}, {m.quantity}' for m in next_moves])
        else: print('No Moves.')
        transactions = self.execute_moves(next_moves, self.dfs)
        for transaction in transactions: self.ns.notify_transaction(transaction)

        last_states = { sym: df.iloc[-1] for (sym, df) in latest_bars }
        # self.strategy.evaluate_funds(transactions, last_states)
        self.strategy.performance.update(self.strategy.portfolios, transactions, last_states)
        
        print(f'{self.strategy.name}:Step:complete ({timer() - start}s)')
        return True # indicate end of step thread


    def execute_moves(self, moves: List[Decision], dfs: Dict[str, pd.DataFrame], is_backtest: bool = False) -> List[TransactionReport]:
        """
        Given a list of moves, communicates with broker to execute buys/sells and
        updates symbol portfolios appropriately.
        """
        reports = []

        # First perform all sell decisions to free up capital
        for decision in [m for m in moves if m.move == Move.Sell]:
            state_at_move = dfs[decision.symbol].iloc[-1]
            transaction = self.broker.attempt_market_sell(decision, state_at_move, is_backtest, self.strategy.crypto)
            if transaction.succeeded:
                pl = transaction.strike - self.strategy.portfolios[decision.symbol].purchase_price
                print(f'SOLD {transaction.symbol:<20} @ ', transaction.strike, f', p/l: {pl:.2f}')
                # Update the portfolio with the sell info
                self.strategy.portfolios[decision.symbol].sold(transaction.strike, transaction.quantity)

                # Keep a record of the transaction
                report = save_transaction(self.strategy, transaction, state_at_move, is_backtest)
                reports.append(report)
                self.strategy.evaluate_funds([report], {report.symbol: state_at_move})

        # Now, perform buy decisions
        for decision in [m for m in moves if m.move == Move.Buy]:
            state_at_move = dfs[decision.symbol].iloc[-1]
            transaction = self.broker.attempt_market_buy(decision, self.strategy.available_capital, state_at_move, is_backtest, self.strategy.crypto)
            if transaction.succeeded:
                print(f'BOUGHT {transaction.symbol:<20} @ ', transaction.strike)
                # Create portfolio for given symbol if it doesn't yet exist
                if decision.symbol not in self.strategy.portfolios.keys():
                    self.strategy.portfolios[decision.symbol] = Portfolio()

                # Update the portfolio with the purchase info
                self.strategy.portfolios[decision.symbol].purchased(transaction.strike, transaction.quantity, transaction.date, transaction.confidence)

                # Keep a record of the transaction
                report = save_transaction(self.strategy, transaction, state_at_move, is_backtest)
                reports.append(report)
                self.strategy.evaluate_funds([report], {report.symbol: state_at_move})

        return reports





    # Active Monitoring Methods

    def check_trending_symbols(self):
        # TODO: check source (e.g. WSB) for trending symbols and modify strategy's existing contracts
        # preview
        self.active = False
        trending = ['GME', 'SPCE', 'AMC', 'BBBY', 'SPWR']
        keep = [c for c in self.strategy.contracts if self.strategy.portfolios[c.symbol].has_stock]
        new_contracts: List[Contract] = [Stock(sym, 'SMART') for sym in trending if sym not in list(map(lambda c: c.symbol, keep))] + keep
        self.strategy.contracts = new_contracts
        self.setup(asyncio.get_event_loop(), True)
        

    def check_latest_news(self):
        # TODO: check rss feeds for trending symbols and modify strategy's existing contracts
        pass


