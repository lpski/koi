import asyncio, numpy as np, sys, eel
from datetime import datetime
from typing import Dict
from dotenv import load_dotenv
from koi.controller import Platform
from koi.models import KoiState
from koi.utils import save_strategy_config


platform: Platform

# Tick Data
@eel.expose
def fetch_market_tick_data() -> Dict[str, dict]:
    try: return platform.ib_client.get_latest_ticks()
    except Exception as e:
        print('fetch_market_tick_data error:', e)
        return {}

@eel.expose
def fetch_crypto_tick_data() -> Dict[str, dict]:
    try: return platform.cb_client.get_latest_ticks()
    except Exception as e:
        print('fetch_crypto_tick_data error: ', e)
        return {}

@eel.expose
def toggle_market_streaming():
    """Kicks off/pauses tick by tick streaming of available market contracts"""
    try: platform.ib_client.toggle_tick_streaming()
    except Exception as e: print('toggle_market_streaming error:', e)

@eel.expose
def toggle_crypto_streaming():
    """Kicks off/pauses tick by tick streaming of available crypto contracts"""
    try: platform.cb_client.toggle_tick_streaming()
    except Exception as e: print('toggle_crypto_streaming error:', e)





# State Fetching

@eel.expose
def fetch_state() -> KoiState:
    try:
        platform.state.ib_connected = platform.ib_client.ib.isConnected()
        platform.state.market_ticks_streaming = platform.ib_client.tick_streaming_enabled
        platform.state.crypto_ticks_streaming = platform.cb_client.tick_streaming_enabled
        return platform.state.toJSON()
    except Exception as e:
        print('fetch_state error:',e)
        return {}


@eel.expose
def fetch_trader_bars(strategy_name: str, size: int = 50):

    try:
        if len(platform.traders) == 0: return {}
        if strategy_name not in list(map(lambda t:t.strategy.name, platform.traders)): return {}
        asyncio.set_event_loop(asyncio.new_event_loop())

        formatted_bars = {}
        matching_traders = [t for t in platform.traders if t.strategy.name == strategy_name]
        if len(matching_traders) == 0: raise f'No matching trader for name {strategy_name}'

        trader = matching_traders[0]
        # print(f'fetch_trader_bars ok: {trader.dfs.keys()}')
        for sym, df in trader.dfs.items():
            new_df = df.iloc[-size:].copy()
            new_df.fillna('nan', inplace=True)

            # date needs to be a string rather than datetime to be sent to js app
            new_df['date'] = new_df['date'].apply(lambda d: d.strftime('%Y/%m/%d %H:%M:%S'))
            formatted_bars[sym] = new_df.to_dict('split')
        return formatted_bars
    except Exception as e:
        print('fetch_trader_bars error:', e)
        return {}



@eel.expose
def fetch_backtest_bars(strategy_name: str, size: int = 50):
    try:
        if len(platform.backtesters) == 0: return {}
        if strategy_name not in list(map(lambda bt:bt.trader.strategy.name, platform.backtesters)): return {}
        asyncio.set_event_loop(asyncio.new_event_loop())
    
        formatted_bars = {}
        matching_bts = [bt for bt in platform.backtesters if bt.trader.strategy.name == strategy_name]
        if len(matching_bts) == 0: raise f'No matching backtest for name {strategy_name}'

        bt = matching_bts[0]
        for sym, df in bt.bt_data.items():
            new_df = df.iloc[-size:].copy()
            # new_df.fillna('nan', inplace=True)
            new_df.replace({ np.nan: 0, np.inf: 0, -np.inf: 0 }, inplace=True)

            # only show bars up to active test place
            new_df = new_df.iloc[0:bt.test_index]

            # date needs to be a string rather than datetime to be sent to js app
            new_df['date'] = new_df['date'].apply(lambda d: d.strftime('%Y/%m/%d %H:%M:%S'))
            new_df = new_df.iloc[-size:]
            formatted_bars[sym] = new_df.to_dict('split')
        return formatted_bars

    except Exception as e:
        print('fetch_backtest_bars error:', e)
        return {}




@eel.expose
def fetch_traders():
    """Retrieves all traders from the current session"""
    try: return [t.__dict__ for t in platform.traders]
    except Exception as e:
        print('fetch_traders error:', e)
        return []


@eel.expose
def fetch_backtesters():
    """Retrieves all backtesters from the current session"""
    try: return [bt.__dict__ for bt in platform.backtesters]
    except Exception as e:
        print('fetch_backtesters error:', e)
        return []



@eel.expose
def fetch_backtest_performances():
    """Retrieves all bt states, formatted"""
    try:
        # return {}
        performances: Dict[str, dict] = {}
        for bt in platform.backtesters:
            bt_perf = bt.trader.strategy.performance
            bt_perf.last_states = {}
            bt_perf.last_transactions = []
            performances[bt.trader.strategy.name] = bt_perf.to_dict()
            performances[bt.trader.strategy.name]['portfolios'] = [p.safe_dict() for _, p in bt.trader.strategy.portfolios.items()]
            performances[bt.trader.strategy.name]['test_size'] = bt.test_size
            performances[bt.trader.strategy.name]['stage'] = bt.stage
            performances[bt.trader.strategy.name]['name'] = bt.name

        # print(performances)
        return performances
    except Exception as e:
        print('fetch_backtest_performances error: ', e)
        return {}


@eel.expose
def fetch_analyses():
    """Retrieves all analyzers (individual, backtest & trader) from this session"""
    analyses: Dict[str, dict] = {}
    try:
        # traders = platform.traders + list(map(lambda bt: bt.trader, platform.backtesters))
        traders = list(map(lambda bt: bt.trader, platform.backtesters))
        for t in traders:
            if t.strategy.analyzer: analyses[t.strategy.name] = t.strategy.analyzer.to_dict()
        for analyzer in platform.analyzers: analyses[analyzer.name] = analyzer.to_dict()

        return analyses
    except:
        print('fetch_analyses error')
        return {}




# State Modification




# Method Execution
@eel.expose
def toggle_strategy(strategy_name: str):
    """Toggles active/inactive state for a given strategy"""
    platform.toggle_strategy(strategy_name)


@eel.expose
def backtest_strategy(strategy_name: str):
    """Begins backtesting for a given strategy"""
    platform.backtest_requested(strategy_name)



@eel.expose
def analyze_strategy(strategy_name: str):
    """Toggles active/inactive state for a given strategy"""
    platform.analysis_requested(strategy_name)



@eel.expose
def heartbeat():
    """Notifies UI that server is still alive"""
    return datetime.now().timestamp()


# Strategy Modifications
@eel.expose
def set_strategy_active_state(name: str):
    """Enables/Disables active trading for strategy with a given name"""
    platform.toggle_strategy(name)


@eel.expose
def set_strategy_capital(name: str, capital: float):
    """Updates capital allocation to a strategy with a given name"""
    matching = [t for t in platform.traders if t.strategy.name == name]
    if len(matching == 0): return
    
    trader = matching[0]
    trader.strategy.available_capital = capital
    save_strategy_config(trader.strategy)



def start_eel(develop):
    if develop:
        print('Starting Eel in dev mode')
        directory = 'src'
        app = None
        page = {'port': 3000}

    else:
        directory = 'build'
        app = 'chrome-app'
        page = 'index.html'

    eel.init(directory, ['.tsx', '.ts', '.jsx', '.js', '.html'])

    eel_kwargs = dict(host='localhost', port=8080, size=(1280, 800))
    try: eel.start(page, mode=app, **eel_kwargs)
    except Exception as e:
        print('eel error:', e)
        sys.exit(1)



if __name__ == '__main__':
    import sys
    load_dotenv()
    platform = Platform()
    start_eel(develop=len(sys.argv) == 2)
