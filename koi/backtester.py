import asyncio, datetime, math, traceback, os, shutil
from asyncio.events import AbstractEventLoop
from threading import Thread
from uuid import uuid4
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from multiprocessing.pool import ThreadPool

from koi.market_data import IB_Client, CB_Client, Market, apply_strategies, ApplyConfig
from koi.market_data.root import apply_labels
from koi.models import BacktestConfig, CryptoContract, Direction, Move, TransactionReport, TransactionType
from koi.trader import Trader
from koi.portfolio import Portfolio
from koi.utils import to_bar_size


class Backtester:
    id: str
    name: str
    stage: str # One of 'setup' | 'testing' | 'complete'
    trader: Trader
    config: BacktestConfig
    completed: asyncio.Future
    bt_data: Dict[str, pd.DataFrame] = {}
    bt_trades: List[TransactionReport] = []

    def __init__(self, trader: Trader, marketData: Market, config: BacktestConfig):
        self.id = str(uuid4())
        self.trader = trader
        self.md = marketData
        self.name = trader.strategy.name
        self.config = config
        self.stage = 'inactive'


    def start(self, main_loop: AbstractEventLoop = None, target_csvs: Dict[str, str] = None):
        """
        Kicks off and controls backtest event flow
            * Triggers training/analysis data fetch (by default 14 -> 7 days ago)
            * Triggers backtest data fetch (by default 7 -> 0 days ago)
        """

        print(f'\n{self.name}:Backtest:Start')
        asyncio.set_event_loop(main_loop)
        self.completed = asyncio.Future()
        self.stage = 'setup'

        # Strategy Setup + Load backtest data in parallel
        # Train end date goes up until the recent_data_duration begins + the test size
        recent_duration = self.trader.strategy.trade_config.recent_data_duration
        if recent_duration is None: train_end_date = datetime.datetime.now()
        else: train_end_date = datetime.datetime.now() - datetime.timedelta(days=int(recent_duration[0]))
        bt_size = 10     # days to backtest on
        train_end_date = train_end_date - datetime.timedelta(days=bt_size)

        # Start data fetch threads
        st = Thread(target=self.trader.setup, args=[main_loop, train_end_date, False])
        st.start()
        st.join()

        tt = Thread(target=self.fetch_test_data, args=[f'{bt_size} D', main_loop])
        tt.start()
        tt.join()

        print('\nSetup Threads complete\n')

        self.perform_testing()
        


    def fetch_test_data(self, test_size: str, loop: AbstractEventLoop):
        print(f'{self.name}:Backtest:fetch_test_data')
        asyncio.set_event_loop(loop)
        bar_size = to_bar_size(self.trader.strategy.trade_config.trade_frequency, self.trader.strategy.crypto)

        pool = ThreadPool(processes=1)
        lookbacks = self.trader.strategy.cnn_manager.lookbacks([c.symbol for c in self.trader.strategy.contracts])
        if self.trader.strategy.cnn_config is not None:
            async_result = pool.apply_async(self.md.get_historical_data, (self.trader.strategy.contracts, bar_size, test_size, '', True, ApplyConfig(True, True, lookbacks)))
        else:
            async_result = pool.apply_async(self.md.get_historical_data, (self.trader.strategy.contracts, bar_size, test_size, '', True, ApplyConfig(True, False, lookbacks)))
        bt_data = async_result.get()

        # Set up portfolios for tracking
        for sym, df in bt_data:
            self.bt_data[sym] = df
            start_date, end_date = df.iloc[0]['date'], df.iloc[-1]['date']
            print(f'{self.name}:Backtest:{sym} Test Range: ({start_date} -> {end_date})')
            
            if sym not in self.trader.strategy.portfolios:
                hold_start = df.iloc[-1]['close']
                self.trader.strategy.portfolios[sym] = Portfolio(hold_start, stop_loss_pct=self.trader.strategy.trade_config.stop_loss_pct, symbol=sym)
            
            # save for reference
            if not os.path.exists(f'config/bt_bars/{self.name}'): os.mkdir(f'config/bt_bars/{self.name}')
            df.to_csv(f'config/bt_bars/{self.name}/{sym}.csv')

        print(f'{self.name}:Backtest:fetch_test_data complete')
        return True



    test_index = 0
    test_size = 0
    def perform_testing(self):
        self.stage = 'testing'
        print(f'{self.name}:Backtest:perform_testing')

        # Ensure test is valid
        if len(self.trader.strategy.contracts) == 0: raise 'No Contracts available to test'

        # Clean out old reports if exist
        if os.path.exists(f'config/transactions/{self.trader.strategy.name}_transactions_bt.csv'):
            os.remove(f'config/transactions/{self.trader.strategy.name}_transactions_bt.csv')
        if os.path.exists(f'config/bt_bars/{self.trader.strategy.name}'):
            shutil.rmtree(f'config/bt_bars/{self.trader.strategy.name}')

        for sym, df in self.bt_data.items():
            # df['labels'] = apply_labels(df, 'close', self.trader.strategy.cnn_config.lookback)
            df['price_diff'] = df['close'].diff()
            self.trader.strategy.cnn_manager.evaluate(df, sym)

        # Create offset to allow for there to be recent data for recency models in strategy 
        if self.trader.strategy.cnn_config is not None: observe_size = self.trader.strategy.cnn_config.batch_size
        else: observe_size = math.floor(min([len(d.index) for d in self.bt_data.values()]) * 0.1)
        self.test_size = len(list(self.bt_data.values())[0].index) - observe_size

        test_quantity = len(self.bt_data[list(self.bt_data.keys())[0]]) - self.trader.strategy.cnn_config.lookback
        for i in range(0, test_quantity):
            self.test_index = i
        
            try:
                if i < observe_size: # update hold start price if not yet testing
                    for sym, df in self.bt_data.items():
                        self.trader.strategy.portfolios[sym].set_hold_start(df.iloc[i]['close'], self.trader.strategy.available_capital / len(self.bt_data.keys()))
                    continue
    
                dfs_at_time = { sym: df.iloc[0:i+1] for (sym, df) in self.bt_data.items() }
                next_moves, predictions = self.trader.strategy.determine_next_move(dfs_at_time)
                transactions = self.trader.execute_moves(next_moves, dfs_at_time, True)
                self.trader.strategy.evaluate_funds(transactions, { sym: df.iloc[-1] for sym, df in dfs_at_time.items()})
 
                # Log actuality for any buy transactions
                lookbacks = self.trader.strategy.cnn_manager.lookbacks(list(self.bt_data.keys()))
                buys = [(t.symbol, self.bt_data[t.symbol].iloc[i+lookbacks[t.symbol]]) for t in transactions if t.transaction_type == TransactionType.MarketBuy]
                for (sym, state) in buys: print(f'{sym} price in {lookbacks[sym]} iterations: {state["close"]} (+/- {state["close"] - dfs_at_time[sym].iloc[-1]["close"]})')

                # Update dataframes with prediction values for later analysis
                for sym, preds in predictions.items():
                    for pred in preds:
                        # Add column for prediction category if it doesn't yet exist
                        col_name = pred.source + ' prediction'
                        if col_name not in self.bt_data[sym].columns: self.bt_data[sym][col_name] = np.nan
                        self.bt_data[sym][col_name][i] = 1 if pred.direction == Direction.Up else -1 if pred.direction == Direction.Down else 0

                # State updates
                last_states = { sym: df.iloc[i] for (sym, df) in self.bt_data.items() }
                self.trader.strategy.performance.update(self.trader.strategy.portfolios, transactions, last_states)
                self.bt_trades = self.bt_trades + transactions

                # Sell all holdings on last index
                if i == test_quantity - 1:
                    for sym, p in self.trader.strategy.portfolios.items():
                        if p.has_stock:
                            last_price = dfs_at_time[sym].iloc[-1]['close']
                            p.sold(last_price, p.quantity)
                    self.trader.strategy.performance.update(self.trader.strategy.portfolios, transactions, last_states)

            except Exception as e:
                print('Exception during backtesting:', traceback.format_exc())
                break


        self.completed.set_result(True)
        self.stage = 'complete'
        print(f'{self.name}:Backtest:perform_testing complete')
        for ps, p in self.trader.strategy.portfolios.items():
            print(f'\t{ps}:\t\tStrategy: ${p.gross_profit:.2f}, Hold: ${p.hold_profit(self.bt_data[ps].iloc[-1]["close"], self.trader.strategy.initial_capital)}  |  {len([t for t in self.trader.strategy.performance.good_buys if t.symbol == ps])} good, {len([t for t in self.trader.strategy.performance.bad_buys if t.symbol == ps])} bad')

        av_gb_conf, n_gb = np.mean([t.confidence for t in self.trader.strategy.performance.good_buys]), len(self.trader.strategy.performance.good_buys)
        av_bb_conf, n_bb = np.mean([t.confidence for t in self.trader.strategy.performance.bad_buys]), len(self.trader.strategy.performance.bad_buys)
        print(f'Strategy Profit:{self.trader.strategy.performance.strategy_profit}, Hold Profit:{self.trader.strategy.performance.hold_profit}  |  Av Buy Conf: good - {av_gb_conf} ({n_gb}), bad - {av_bb_conf}({n_bb})')

        # save dfs for analysis
        for sym, df in self.bt_data.items():
            df.to_csv(f'config/bt_bars/{self.name}_tested_{sym}.csv')


