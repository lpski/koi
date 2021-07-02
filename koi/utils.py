from datetime import datetime
from math import nan
from optparse import OptionParser
from typing import Dict, List
import os, pathlib, json, pandas as pd, math, traceback
from configparser import ConfigParser
from pandas.core.series import Series
from dotenv import dotenv_values

from koi.models import ContractData, CryptoContract, KoiState, StrategyInfo, Transaction, TransactionReport, TransactionType
from koi.strategies import StrategyInterface

class AppConfig():
    test_mode: bool
    test_strategies: List[str]
    test_capital: float
    force_download: bool
    data_offset: int

    def __init__(self, test: bool = False, test_strategies: List[str] = [], test_capital: float = 1000, force_download: bool = False, offset: int = 0):
        self.test_mode = test
        self.test_strategies = test_strategies
        self.test_capital = test_capital
        self.force_download = force_download
        self.data_offset = offset


def initialize_app() -> AppConfig:
    parser = OptionParser()
    parser.add_option("-z", "--test", dest="test", action = 'store_true', default=False, help="Test performance across tuple sizes")
    parser.add_option("-o", "--offset", dest="offset", type=int, default=0, help="Training/backtesting data offset")
    parser.add_option("-f", "--force", dest="force_download", action = 'store_true', default=False, help="Force download of new training data even if csv exists for givn strategy")
    parser.add_option("-s", "--strategies", dest="test_strategies", type=str, action="append", default=None, help="Specify which strategies to test, otherwise all active strategies are tested")
    parser.add_option("-c", "--capital", dest="test_capital", type=float, default=10000, help="Specify initial capital for backtesting")

    (options, _) = parser.parse_args()

    TEST_MODE = bool(options.test)
    TEST_STRATEGIES = list(set(options.test_strategies)) if options.test_strategies is not None else []
    TEST_CAPITAL = bool(options.test_capital)
    FORCE_DOWNLOAD = str(options.force_download)
    DATA_OFFSET = int(options.offset)

    return AppConfig(TEST_MODE, TEST_STRATEGIES, TEST_CAPITAL, FORCE_DOWNLOAD, DATA_OFFSET)





def set_config():
    env = dotenv_values('.env')
    config = ConfigParser()
    config.add_section('main')

    # Set the values for the `main` section.
    config.set('main', 'REGULAR_ACCOUNT', env['IB_ACCOUNT'])
    config.set('main', 'REGULAR_USERNAME', env['IB_USERNAME'])

    config.set('main', 'PAPER_ACCOUNT', env['IB_ACCOUNT'])
    config.set('main', 'PAPER_USERNAME', env['IB_USERNAME'])

    # Make the `config` folder for the user.
    new_directory = pathlib.Path("config/").mkdir(parents=True, exist_ok=True)

    # Write the contents of the `ConfigParser` object to the `config.ini` file.
    with open('config/config.ini', 'w+') as f:
        config.write(f)





# Strategy data saving

def save_transaction(strategy: StrategyInterface, transaction: Transaction, transaction_state: Series, is_backtest: bool = False) -> TransactionReport:
    df: pd.DataFrame
    file_path = 'config/transactions/{}_transactions{}.csv'.format(strategy.name, '_bt' if is_backtest else '')
    columns = ['date', 'symbol', 'type', 'price', 'quantity', 'confidence', 'hold_length', 'trade_pl', 'portfolio_pl', 'total_pl']

    # Get existing transactions if they exist, else create a new data frame
    if os.path.isfile(file_path):
        try: df = pd.read_csv(file_path)
        except: df = pd.DataFrame([], columns=columns)
    else: df = pd.DataFrame([], columns=columns)

    relevant_portfolio = strategy.portfolios[transaction.symbol]
    cross_portfolio_pl = sum(list(map(lambda p: p.gross_profit, strategy.portfolios.values())))
    report: TransactionReport
    if transaction.transaction_type == TransactionType.MarketBuy:
        report = TransactionReport(transaction.date, transaction, nan, relevant_portfolio.gross_profit, cross_portfolio_pl, nan)
    else:
        purchase_date: datetime = None
        if not isinstance(relevant_portfolio.purchase_date, datetime): purchase_date = datetime.strptime(relevant_portfolio.purchase_date, '%Y-%m-%d %H:%M:%S')
        else: purchase_date = relevant_portfolio.purchase_date
        
        sell_date: datetime = None
        if not isinstance(relevant_portfolio.purchase_date, datetime): sell_date = datetime.strptime(transaction.date, '%Y-%m-%d %H:%M:%S')
        else: sell_date = transaction.date

        hold_duration = math.floor((sell_date - purchase_date).seconds / strategy.trade_config.trade_frequency)
        report = TransactionReport(transaction.date, transaction, transaction.quantity * (transaction.strike - relevant_portfolio.purchase_price), relevant_portfolio.gross_profit, cross_portfolio_pl, hold_duration)


    # Append new data and save the updated csv
    df = df.append(pd.DataFrame([[
        report.date,
        report.symbol,
        report.transaction_type,
        report.strike,
        report.quantity,
        report.confidence,
        report.hold_length,
        report.tradePL,
        report.portfolioPL,
        report.totalPL
    ]], columns=df.columns))
    df.to_csv(file_path, index=False)

    return report


def save_strategy_data(dfs: Dict[str, pd.DataFrame], strategy_name: str):
    """
    Given a dictionary mapping instrument symbols to historical bar data, 
    writes to a new zip file in the format of [symbol]_[strategy_name]
    """
    pathlib.Path("config/data/").mkdir(parents=True, exist_ok=True)
    for (sym, df) in dfs.items():
        df_compression_opts = dict(method='zip', archive_name='{}_{}.csv'.format(sym, strategy_name))
        df.to_csv('config/data/{}_{}.zip'.format(sym, strategy_name), compression=df_compression_opts)




# State saving / loading
def load_state() -> KoiState:
    '''
    Loads the contents of the `state.json` file into a state object
    '''
    try:
        with open('config/state.json', 'r') as f:
            data = json.loads(f.read())
            return KoiState.from_json(data)
    except Exception as e:
        print('Error Loading State: could not read json file')
        print(traceback.print_exc())
        return None

def save_state(state: KoiState):
    '''
    Write the contents of the state object to the `state.json` file.
    '''
    pathlib.Path("config/").mkdir(parents=True, exist_ok=True)
    with open('config/state.json', 'w+', encoding='utf-8') as f:
        json.dump(state.__dict__, f, ensure_ascii=False, indent=4)

def save_strategy_config(strategy: StrategyInterface):
    '''
    Updates the state file with an updated strategy config.
    '''
    cur_state = load_state()
    if cur_state and cur_state.strategies:
        existing_config = [s for s in cur_state.strategies if s.name == strategy.name]

        # Convert interface to info
        contracts = [c if isinstance(c, CryptoContract) else ContractData.from_contract(c) for c in strategy.contracts]
        updated_info = StrategyInfo(strategy.name, strategy.equity, strategy.available_capital, strategy.initial_capital, contracts, strategy.portfolios, strategy.start_date, strategy.trade_config, strategy.analysis_config)

        if existing_config:
            cur_state.strategies = [s for s in cur_state.strategies if s.name != strategy.name] + [updated_info]
        else:
            cur_state.strategies.append(updated_info)
        save_state(cur_state)
    





# General Utility

def to_bar_size(seconds: int, crypto: bool = False):
    if crypto: return seconds

    if seconds < 60: return '{} secs'.format(seconds)
    if seconds < 3600: return '{} min{}'.format(math.floor(seconds / 60), 's' if seconds >= 120 else '')
    else: return '{} hour{}'.format(math.floor(seconds / 3600), 's' if seconds > 3600 else '')


