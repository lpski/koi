import pandas as pd, dotenv, asyncio, sys
from copy import deepcopy
from threading import Thread
from typing import List

from koi.backtester import Backtester
from koi.analyzer import Analyzer
from koi.utils import AppConfig, initialize_app, load_state
from koi.trader import Trader
from koi.models import BacktestConfig, KoiState, StrategyInfo
from koi.strategies import get_defined_strategies
from koi.broker import Broker
from koi.portfolio import Portfolio
from koi.market_data import IB_Client, CB_Client
from koi.notifier import NotificationService

pd.options.mode.chained_assignment = None  # default='warn'
env = dotenv.dotenv_values('.env')
AvailableStrategies = get_defined_strategies()

class Platform:
    state: KoiState = None
    ib_client: IB_Client
    cb_client: CB_Client
    traders: List[Trader] = []
    analyzers: List[Analyzer] = []
    backtesters: List[Backtester] = []
    config: AppConfig
    bt_data: pd.DataFrame
    broker: Broker
    notifier: NotificationService

    def __init__(self):
        try:
            print('\nStarting koi platform\n_________________________\n')

            # First we set initialize and extract cli arguments
            self.appConfig = initialize_app()
            self.state = load_state()

            self.ib_client = IB_Client(self.state)
            self.cb_client = CB_Client(self.state, exchange=env['CRYPTO_EXCHANGE'])
            self.broker = Broker(self.ib_client, self.cb_client)
            self.notifier = NotificationService()

            # We create (and track) one trader for each strategy with its last state
            strategies = { s.name: s for s in AvailableStrategies }

            # Filter out unknown strategies from state.json
            self.state.strategies = [s for s in self.state.strategies if s.name in strategies]
            strategy_info = { s.name: s for s in self.state.strategies }
    
            for s_name, s_class in strategies.items():
                use_crypto = strategy_info[s_name].crypto
                self.traders.append(Trader(s_class(strategy_info[s_name]), self.cb_client if use_crypto else self.ib_client, self.broker, self.notifier))


        except KeyboardInterrupt:
            if self.ib_client.ib.isConnected(): self.ib_client.ib.disconnect()
            sys.exit(0)



    def toggle_strategy(self, strategy_name: str):
        """Starts or stops a given strategy's trading activity"""
        for t in self.traders:
            if t.strategy.name == strategy_name:
                if not t.active:
                    try:
                        loop = asyncio.get_event_loop()
                        Thread(target=t.start, args=[loop]).start()
                    except Exception as e:
                        print('Trader Strategy ERROR', e)
                else:
                    t.active = False
                break
        

        for s in self.state.strategies:
            if s.name == strategy_name:
                s.active = not s.active
                break



    def backtest_requested(self, strategy_name: str):
        """
        Called when the web app requests a strategy to be backtested
        """
        strategy_info = { s.name: s for s in self.state.strategies }
        strategies = { s.name: s for s in AvailableStrategies }
        if strategy_name not in strategies: return

        # Create the requested strategy interface and it's associated trader
        info = deepcopy(strategy_info[strategy_name])
        if info.crypto: test_portfolios = { (f'{c.market}-{c.currency}'): Portfolio(-1, symbol=(f'{c.market}-{c.currency}')) for c in info.contracts }
        else: test_portfolios = { c.symbol: Portfolio(-1, symbol=c.symbol) for c in info.contracts }
        
        del info.portfolios, info.available_capital, info.equity, info.start_date
        test_info = StrategyInfo(portfolios=test_portfolios, equity=info.initial_capital, available_capital=info.initial_capital, start_date='', **(info.__dict__))
        strategy = strategies[strategy_name](test_info, True)
        trader = Trader(strategy, self.cb_client if test_info.crypto else self.ib_client, self.broker, self.notifier)
        backtester = Backtester(trader, self.cb_client if test_info.crypto else self.ib_client, BacktestConfig())

        # remove existing backtester if exists, then append new one to backest list
        self.backtesters = [bt for bt in self.backtesters if bt.name != strategy_name]
        self.backtesters.append(backtester)

        # Start up the the backtest in a seperate thread to avoid blocking main thread
        loop = asyncio.get_event_loop()
        try: Thread(target=backtester.start, args=[loop]).start()
        except Exception as e: print('Backtest Strategy ERROR', e)


    def analysis_requested(self, strategy_name: str):
        """
        Called when the web app requests a strategy's portfolios to be analyzed for optimum buy/sell points
        """
        strategy_info = { s.name: s for s in self.state.strategies }
        strategies = { s.name: s for s in AvailableStrategies }
        if strategy_name not in strategies: return
        
        # Create the requested strategy interface and it's associated trader
        info = deepcopy(strategy_info[strategy_name])
        test_portfolios = { c.symbol: Portfolio(-1, symbol=c.symbol) for c in info.contracts }
        del info.portfolios, info.available_capital, info.equity, info.active, info.start_date
        test_info = StrategyInfo(portfolios=test_portfolios, equity=info.initial_capital, available_capital=info.initial_capital, active=True, start_date='', **(info.__dict__))
        strategy = strategies[strategy_name](test_info)
        analyzer = Analyzer(strategy)

        # remove existing analyzer if exists, then append new one to analyzers list
        if (len([a for a in self.analyzers if a.name == strategy_name]) > 0):
            self.analyzers = list([a for a in self.analyzers if a.name != strategy_name])
        self.analyzers.append(analyzer)

        # Start up the the backtest in a seperate thread to avoid blocking main thread
        loop = asyncio.get_event_loop()
        th = Thread(target=lambda:loop.run_until_complete(analyzer.start(loop, md=self.md)))
        th.start()



