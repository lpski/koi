import asyncio
import math
from typing import Optional, Tuple
import eel
from ib_insync import IB
from ib_insync.order import LimitOrder, Order, MarketOrder
from ibapi.contract import Contract
from pandas.core.series import Series

from koi.models import BuyQuantity, CB_Order, CryptoContract, Decision, Transaction, TransactionType
from koi.market_data import IB_Client, CB_Client
from koi.market_data.root import CryptoOrder



known_conIds = {
    "AAPL": 265598,
    "PLTR": 444857009,
    "SPY": 756733,
    "GME": 36285627,
    "SPCE": 388824891,
    "AMC": 1140070600,
    "BBBY": 266630,
    "TSLA": 76792991,
    "GE": 7516,
    "GM": 80986742,
    "GOOG": 208813720,
    "FB": 107113386,
    'AMZN': 3691937,
    'F': 9599491,
    'SPOT': 312496724,
    'EA': 268995,
    'BA': 4762,
    'UAL': 79498203,
    'LYFT': 359130923,
    'BABA': 166090175,
    'SQ': 212671971,
    'ABNB': 459530964,
    'XOM': 13977,

    'SRNE': 132304979,
    'PLUG': 88385302,
    'MARA': 360205428,
    'GEVO': 320228879,
    'TRXC': 393993722,
    'WKHS': 215119556,
    'BLNK': 287428879,
    'PHUN': 347896223,
    'XPEV': 441828902,
    'VIAC': 393897513,
    'CMCSA': 267748,
    'BAC': 10098,

    'QCOM': 273544,
    'DD': 365921621,
    'LLY': 9160,
    'PFE': 11031,
    'XSPA': 426480588,
    'TIGR': 356857464,
    'MVIS': 102558681,
    'KO': 8894,
    'RIOT': 292830677,
    'ACB': 420446448,
    'TLRY': 326196509,
    'SNDL': 376499916,
    'GILD': 269753,

    'DIS': 6459,
    'MU': 9939,
    'NOK': 661513,
    'PTON': 385087203,
    'TWTR': 137780444,
    'SBUX': 274105,
    'UBER': 365207014,

    'COF': 5941,
    'T': 37018770,
    'CCL': 5516,
    'DKNG': 419221909,
    'NIO': 332794741,
    'SNAP': 268060148,
    'NVDA': 4815747,
    'NCLH': 120643512,
    'PINS': 360975915,
    'SBUX': 274105,
    'PYPL': 199169591,
    'MGM': 9560,
    'WFC': 10375,
    'AMD': 4391,
    'TSM': 6223250,
    'AMAT': 266093,
    'ADBE': 265768,
    'TLRY': 326196509,
    'JD': 152486141,
    'V': 49462172,
    'VALE': 60581038,
}

def wait_for_ib_order_fill(ib: IB, order: Order, contract: Contract) -> Tuple[float, int, bool]:
    fut = asyncio.Future()
    try:
        contract.conId = known_conIds[contract.symbol]
        trade = ib.placeOrder(contract, order)
        while not trade.isDone():
            print('waiting on trade to be filled:', trade.filled())
            ib.waitOnUpdate(1)
            # ib.sleep(.1)

        print(f'@ {trade.orderStatus.avgFillPrice} - {trade.orderStatus.filled} Shares')
        fut.set_result((trade.orderStatus.avgFillPrice, trade.orderStatus.filled, True))
    except Exception as e:
        print('wait_for_ib_order_fill error:', e)
        fut.set_result((0, 0, False))
    return fut
    


def wait_for_cb_order_fill(cb: CB_Client, contract: CryptoContract, side: str, quantity: float, price: Optional[float] = None) -> Tuple[float, int, bool]:    
    fut = asyncio.Future()

    try:
        # new version
        status = cb.add_order(CryptoOrder(contract.symbol, side, quantity, price))
        print('initial order status:', status.__dict__)
        while not status.settled and not status.failed:
            status = cb.update_order_status(status)
            eel.sleep(.25)

        if status.failed: raise Exception('Order Fill Failure: ', status.__dict__)
        print(f'Order filled @ ${status.price} (ex. value: {status.executed_value} fees: ${status.fees}) - {status.fill_quantity} {contract.symbol}')
        fut.set_result((status.price, status.fill_quantity, True))

    except Exception as e:
        print('wait_for_cb_order_fill error:', e)
        fut.set_result((0, 0, False))

    return fut


class Broker:
    ib_client: IB_Client
    cb_client: CB_Client
    allow_fractional: bool = False

    # testing
    trade_volume: float
    trade_volume_shares: float
    total_fees: float

    def __init__(self, ib: IB_Client, cb: CB_Client):
        self.ib_client = ib
        self.cb_client = cb
        
        self.trade_volume = 0
        self.trade_volume_shares = 0
        self.total_fees = 0


    def latest_price(self, symbol: str, state: Series, is_backtest: bool, crypto: bool, side: str = 'buy') -> float:
        """Returns latest ticker ask. For backtesting, returns last close price"""
        if is_backtest:
            if crypto:
                if side == 'buy': return state['close']
                else: return state['close']
            else: return state['close']
        else:
            if crypto:
                try: ask, bid = self.cb_client.latest_symbol_price(symbol)
                except Exception as e:
                    print(e)
                    raise Exception(f'Latest crypto buy-side tick data for {symbol} not available: ', e)

                print(f'latest_price:spread: {ask-bid:.5f} ({(ask-bid)/ask*100:.3f})')
                if side == 'buy': return ask
                else: return bid
            else:
                if side == 'buy':
                    if symbol in self.ib_client.latest:
                        try: return float(self.ib_client.latest[symbol].ask)
                        except: return self.ib_client.latest[symbol].ask
                    else:
                        print(f'{symbol} buy-side not in {self.ib_client.latest}')
                        raise 'Latest market buy-side tick data for {} not available'.format(symbol)
                else:
                    if symbol in self.ib_client.latest:
                        try: return float(self.ib_client.latest[symbol].bid)
                        except: return self.ib_client.latest[symbol].bid
                    else:
                        print(f'{symbol} sell-side not in {self.ib_client.latest}')
                        raise 'Latest market sell-side tick data for {} not available'.format(symbol)


    def attempt_market_buy(self, decision: Decision, available_capital: float, state: Series, is_backtest: bool = False, crypto: bool = False) -> Transaction:
        """
        Sends buy order to broker for given symbol, returns success state
        """
        try: latest_price = self.latest_price(decision.symbol, state, is_backtest, crypto)
        except:
            print('Error retrieving latest price')
            return Transaction(False, TransactionType.MarketBuy, 0, 0, decision, state['date'])

        # Determine how many shares we can/should purchase given a decision
        share_quantity = 0
        if isinstance(decision.quantity, BuyQuantity):
            diviser = 1 if decision.quantity == BuyQuantity.Max else 2
            share_quantity = ((available_capital * .9) / diviser) / latest_price
        else:
            max_purchase_quantity = (available_capital * .9) / latest_price
            if not self.allow_fractional and not crypto: max_purchase_quantity = math.floor(max_purchase_quantity)

            if decision.quantity < max_purchase_quantity: # decision is valid quantity
                share_quantity = decision.quantity
            else: # Can't afford requested amount, instead buy as much as possible
                share_quantity = max_purchase_quantity

        if not self.allow_fractional and not crypto:
            try: share_quantity = math.floor(share_quantity)
            except: print('Error getting share quantity:', share_quantity, decision.quantity, available_capital, self.latest_price(decision.symbol, state, is_backtest, crypto))

        strike_price: float
        succeeded = True
        
        if share_quantity == 0 or (not self.allow_fractional and not crypto and share_quantity < 0):
            print('share_quantity=0 error - returning')
            strike_price = 0
            share_quantity = 0
            succeeded = False
        elif is_backtest:
            c_type = 'crypto' if crypto else 'stock'
            # spread = .01 if c_type == 'stock' else 0
            spread = 0
            buy_fee = state['close'] * self.get_fee_pct(c_type)[0] + self.get_fixed_fee(c_type, state["close"], share_quantity)
            self.total_fees += buy_fee
            self.trade_volume_shares += share_quantity
            print(f'unadjusted price: {state["close"]} | fee: {buy_fee} | trade volume: {self.trade_volume} | total fees: {self.total_fees}')
            strike_price = state['close'] + buy_fee + spread
        else:
            try:
                if crypto:
                    try:
                        print('attempting crypto market buy @ ', latest_price)
                        res = asyncio.get_event_loop().run_until_complete(wait_for_cb_order_fill(self.cb_client, decision.contract, 'buy', share_quantity, latest_price))
                        (strike_price, share_quantity, succeeded) = res
                    except Exception as e:
                        print('asnycio wait_for_cb_order_fill error:', e)
                        strike_price = 0
                        succeeded = False
                else:
                    print(f'attempting {decision.symbol} ib market buy @ {latest_price}')
                    # buy_order = MarketOrder('BUY', share_quantity)
                    buy_order = LimitOrder('BUY', share_quantity, latest_price)
                    res = asyncio.get_event_loop().run_until_complete(wait_for_ib_order_fill(self.ib_client.ib, buy_order, decision.contract))
                    
                    print('market buy res:', res)
                    (strike_price, share_quantity, succeeded) = res

            except Exception as e: # Failed to purchase at limit price
                print('market buy error:', e)
                succeeded = False
                strike_price = 0
                share_quantity = 0

        self.trade_volume += (strike_price * share_quantity)
        return Transaction(succeeded, TransactionType.MarketBuy, strike_price, share_quantity, decision, state['date'])


    def attempt_market_sell(self, decision: Decision, state: Series, is_backtest: bool = False, crypto: bool = False) -> Transaction:
        """
        Sends sell order to broker for given symbol, returns success state.
        """
        # Currently, selling will only support closing out our entire position
        # TODO: support partial sells in the future
        share_quantity = decision.quantity
        try: latest_price = self.latest_price(decision.symbol, state, is_backtest, crypto, 'sell')
        except: return Transaction(False, TransactionType.MarketSell, 0, 0, decision, state['date'])

        strike_price: float
        succeeded = True
        if is_backtest:
            c_type = 'crypto' if crypto else 'stock'
            spread = .01 if c_type == 'stock' else 0
            sell_fee = state['close'] * self.get_fee_pct(c_type)[1] + self.get_fixed_fee(c_type, state['close'], share_quantity)
            self.total_fees += sell_fee
            self.trade_volume_shares += share_quantity
            print(f'sell fee: {sell_fee} | trade volume: {self.trade_volume} | total fees: {self.total_fees}')
            strike_price = state['close'] - sell_fee - spread
        else:
            # TODO: Communicate with market here
            try:
                if crypto:
                    print('attempting crypto market sell @ ', latest_price)
                    (strike_price, share_quantity, succeeded) = asyncio.get_event_loop().run_until_complete(wait_for_cb_order_fill(self.cb_client, decision.contract, 'sell', share_quantity, latest_price))
                else:
                    print('attempting ib market sell @ ', latest_price)
                    # sell_order = MarketOrder('SELL', share_quantity)
                    sell_order = LimitOrder('SELL', share_quantity, latest_price)
                    (strike_price, share_quantity, succeeded) = asyncio.get_event_loop().run_until_complete(wait_for_ib_order_fill(self.ib_client.ib, sell_order, decision.contract))


            except Exception as e: # Failed to sell at limit price
                succeeded = False
                strike_price = 0
                share_quantity = 0
    
        self.trade_volume += (strike_price * share_quantity)
        return Transaction(succeeded, TransactionType.MarketSell, strike_price, share_quantity, decision, state['date'])



    # backtest methods
    CRYPTO_EXCHANGE = 'robinhood'
    def get_fee_pct(self, contract_type: str) -> Tuple[float, float]:
        """Returns (taker, maker) fees for current volume"""
        if contract_type == 'forex':
            return (0.00002, 0.00002)
        elif contract_type == 'crypto':
            if self.CRYPTO_EXCHANGE == 'binance':
                if self.trade_volume < 50_000:
                    return (.001, .001)
                elif self.trade_volume < 100_000:
                    return (.0009, .0009)
                elif self.trade_volume < 5000_000:
                    return (.0009, .0008)
                elif self.trade_volume < 1_000_000:
                    return (.0008, .0007)
                elif self.trade_volume < 5_000_000:
                    return (.0007, .0005)
                elif self.trade_volume < 10_000_000:
                    return (.0006, .0004)
                elif self.trade_volume < 25_000_000:
                    return (.0006, 0)
                elif self.trade_volume < 100_000_000:
                    return (.0005, 0)
                elif self.trade_volume < 250_000_000:
                    return (.0004, 0)
                elif self.trade_volume < 500_000_000:
                    return (.0003, 0)
                else: return (.0002, 0)
            elif self.CRYPTO_EXCHANGE == 'kraken':
                if self.trade_volume < 50_000:
                    return (.0026, .0016)
                elif self.trade_volume < 100_000:
                    return (.0024, .0014)
                elif self.trade_volume < 250_000:
                    return (.0022, .0012)
                elif self.trade_volume < 500_000:
                    return (.002, .001)
                elif self.trade_volume < 1_000_000:
                    return (.0018, .0008)
                elif self.trade_volume < 2_500_000:
                    return (.0016, .0006)
                elif self.trade_volume < 5_000_000:
                    return (.0014, .0004)
                elif self.trade_volume < 10_000_000:
                    return (.0012, .0002)
                else: return (.001, 0)
            elif self.CRYPTO_EXCHANGE == 'coinbase':
                if self.trade_volume < 10_000:
                    return (.005, .005)
                elif self.trade_volume < 50_000:
                    return (.0035, .0035)
                elif self.trade_volume < 100_000:
                    return (.0025, .0015)
                elif self.trade_volume < 1_000_000:
                    return (.002, .001)
                elif self.trade_volume < 10_000_000:
                    return (.0018, .0008)
                elif self.trade_volume < 50_000_000:
                    return (.0015, .0005)
                elif self.trade_volume < 300_000_000:
                    return (.0007, 0)
                elif self.trade_volume < 500_000_000:
                    return (.0005, 0)
                else: return (.0004, 0)
            elif self.CRYPTO_EXCHANGE == 'robinhood':
                return (0.0001, 0.0001)
        return (0, 0)

    IBKR_PRICING_STRUCTURE = 'tiered'
    def get_fixed_fee(self, contract_type: str, share_price: float, buy_quantity: float) -> float:
        if contract_type == 'stock':
            if self.IBKR_PRICING_STRUCTURE == 'tiered':

                fee_per_share: float
                if self.trade_volume_shares < 300_000: fee_per_share = .0035
                elif self.trade_volume_shares < 3_000_000: fee_per_share = .002
                elif self.trade_volume_shares < 20_000_000: fee_per_share = .0015
                elif self.trade_volume_shares < 100_000_000: fee_per_share = .001
                else: fee_per_share = .0005

                # Ensure min fee is met
                trade_value = buy_quantity * share_price
                min_fee, expected_fees = .35, buy_quantity * fee_per_share

                if expected_fees < min_fee:
                    fee_per_share += (min_fee - expected_fees) / buy_quantity
                    expected_fees = buy_quantity * fee_per_share

                # Ensure max fee is not exceeded
                if expected_fees / trade_value > .01: fee_per_share = (trade_value * .01) / buy_quantity

                return fee_per_share
        
            else: return .005
        else: return 0
