from datetime import datetime
from typing import Union, Dict, List
import numpy as np
from pandas.core.series import Series

from koi.models import TransactionReport, TransactionType
from koi.portfolio import Portfolio


class Stat(object):
    correct: int
    incorrect: int
    unsure: int
    total: int
    percentage: float

    def __init__(self):
        self.correct = 0
        self.incorrect = 0
        self.unsure = 0
        self.percentage = 0
        self.total = 0



def to_date_string(date: Union[datetime, str]):
    if isinstance(date, datetime):
        return date.strftime('%Y-%m-%d %H:%M:%S')
    else:
        return date

class TransactionHistory(object):
    purchase_date: str
    sell_date: str
    pl: float
    symbol: str

    def __init__(self, purchase_date: Union[datetime, str], sell_date: Union[datetime, str], pl: float, symbol: str):
        self.purchase_date = to_date_string(purchase_date)
        self.sell_date = to_date_string(sell_date)
        self.pl = pl
        self.symbol = symbol

class StrategyPerformance(object):
    active: bool = True
    stage: str = 'data'
    initial_capital: float = 0
    observations: int = 0
    buys: Dict[str, int] = {}
    total_buys: int = 0
    total_sells: int = 0
    hold_profit: float = 0
    strategy_profit: float = 0
    largest_profit: TransactionHistory = None
    largest_loss: TransactionHistory = None
    largest_missed_profit: TransactionHistory = None
    good_buys: List[TransactionReport] = []
    bad_buys: List[TransactionReport] = []
    bad_sells: List[TransactionReport] = []
    all_transactions: List[TransactionReport] = []
    prediction_stats: Dict[str, Dict[str, Stat]] = {}

    last_states: Dict[str, Series] = None
    last_transactions: List[TransactionReport] = []

    def __init__(self, initial_capital: float = 0):
        self.observations = 0
        self.total_buys = 0
        self.total_sells = 0
        self.hold_profit = 0
        self.strategy_profit = 0
        self.initial_capital = initial_capital

    def update(self, portfolios: Dict[str, Portfolio], transactions: List[TransactionReport], states: Dict[str, Series]):
        self.observations += 1
        self.all_transactions += transactions

        # get hold profit
        initial_hold_capital_per_portfolio = self.initial_capital / len(portfolios.keys())
        self.hold_profit = sum([p.hold_profit(states[sym]['close'], initial_hold_capital_per_portfolio) for sym, p in portfolios.items()])

        # Update performance based on transactions
        for transaction in transactions:
            relevant_portfolio = portfolios[transaction.symbol]

            if transaction.transaction_type == TransactionType.MarketBuy:
                if transaction.symbol not in self.buys: self.buys[transaction.symbol] = 0
                self.buys[transaction.symbol] += 1
                self.total_buys += 1

            elif transaction.transaction_type == TransactionType.MarketSell:
                self.strategy_profit = transaction.totalPL
                self.total_sells += 1

                # Check if sell had highest profit
                if transaction.tradePL > 0 and (self.largest_profit is None or transaction.tradePL > self.largest_profit.pl):
                    self.largest_profit = TransactionHistory(relevant_portfolio.purchase_date, transaction.date, transaction.tradePL, transaction.symbol)
                
                # Check if sell had highest loss
                if transaction.tradePL < 0 and (self.largest_loss is None  or transaction.tradePL < self.largest_loss.pl):
                    self.largest_loss = TransactionHistory(relevant_portfolio.purchase_date, transaction.date, transaction.tradePL, transaction.symbol)

        # Compare states with previous step's states to determine if buys/sells were good/bad
        if self.last_states is not None:
            self.update_prediction_stats(states)

            # Check transaction accuracy
            for transaction in self.last_transactions:
                state = states[transaction.symbol]
                relevant_portfolio = portfolios[transaction.symbol]

                if transaction.transaction_type == TransactionType.MarketBuy:
                    # Check if next price would've been a better place to buy
                    # if state['close'] < transaction.strike: self.bad_buys.append(transaction)
                    # elif state['close'] > transaction.strike: self.good_buys.append(transaction)
                    pass

                elif transaction.transaction_type == TransactionType.MarketSell:
                    # Check if sell had worst missed profit
                    price_diff = state['close'] - self.last_states[transaction.symbol]['close']
                    missed_profit = price_diff * relevant_portfolio.quantity
                    if self.largest_missed_profit is None or missed_profit > self.largest_missed_profit.pl:
                        self.largest_missed_profit = TransactionHistory(relevant_portfolio.purchase_date, transaction.date, missed_profit, transaction.symbol)

                    if transaction.tradePL < 0: self.bad_buys.append(transaction)
                    elif transaction.tradePL > 0: self.good_buys.append(transaction)


                    # Check if next price would've been a better place to sell
                    if state['close'] > transaction.strike:
                        self.bad_sells.append(transaction)


        # update last state tracking
        self.last_states = states
        self.last_transactions = transactions


    def update_prediction_stats(self, new_states: Dict[str, Series]):
        """Given the latest states for each instrument, determines accuracy of the previous round of predictions"""
        prediction_fields = ['arima prediction', 'gmm prediction', 'mixed prediction', 'analysis prediction', 'cnn prediction']
        joined_fields = ['arima+cnn prediction']
        for sym, last_state in self.last_states.items():
            # Initialize symbol in prediction stats if needed
            if sym not in self.prediction_stats:
                self.prediction_stats[sym] = { field: Stat() for field in prediction_fields + joined_fields }

            # Update stats for each prediction field
            for field in prediction_fields:
                if sym not in self.last_states or field not in last_state: continue

                last_prediction = last_state[field]
                if not np.isnan(last_prediction):
                    # cur_diff = new_states[sym]['price_diff']
                    cur_label = new_states[sym]['label']

                    self.prediction_stats[sym][field].total += 1
                    if (last_prediction > 0 and cur_label == 2) or (last_prediction < 0 and cur_label == 0):
                        self.prediction_stats[sym][field].correct += 1
                    elif (last_prediction > 0 and cur_label == 0) or (last_prediction < 0 and cur_label == 2):
                        self.prediction_stats[sym][field].incorrect += 1
                    elif last_prediction == 0:
                        self.prediction_stats[sym][field].unsure += 1

                    self.prediction_stats[sym][field].percentage = (self.prediction_stats[sym][field].correct / self.prediction_stats[sym][field].total) * 100

            # Also update stat for custom joined accuracy fields
            for field_a, field_b in [('arima prediction', 'cnn prediction')]:
                if sym not in self.last_states or field_a not in last_state or field_b not in last_state: continue

                joined_field = f'{field_a.split(" ")[0]}+{field_b.split(" ")[0]} prediction'
                last_a_pred, last_b_pred = last_state[field_a], last_state[field_b]
                last_prediction = 1 if last_a_pred > 0 and last_b_pred > 0 else -1 if last_a_pred < 0 and last_b_pred < 0 else 0
                
                if not np.isnan(last_a_pred) and not np.isnan(last_b_pred):
                    cur_label = new_states[sym]['label']

                    self.prediction_stats[sym][joined_field].total += 1
                    if (last_prediction > 0 and cur_label == 2) or (last_prediction < 0 and cur_label == 0):
                        self.prediction_stats[sym][joined_field].correct += 1
                    elif (last_prediction > 0 and cur_label == 0) or (last_prediction < 0 and cur_label == 2):
                        self.prediction_stats[sym][joined_field].incorrect += 1
                    elif last_prediction == 0:
                        self.prediction_stats[sym][joined_field].unsure += 1

                    self.prediction_stats[sym][joined_field].percentage = (self.prediction_stats[sym][joined_field].correct / self.prediction_stats[sym][joined_field].total) * 100

                    



    # Util to help convert transaction histories to dict format
    def to_dict(self):
        data = self.__dict__.copy()
        if self.largest_profit is not None:
            data['largest_profit'] = self.largest_profit.__dict__
        if self.largest_loss is not None:
            data['largest_loss'] = self.largest_loss.__dict__
        if self.largest_missed_profit is not None:
            data['largest_missed_profit'] = self.largest_missed_profit.__dict__

        data['good_buys'] = [b.to_safe_dict() for b in self.good_buys]
        data['bad_buys'] = [b.to_safe_dict() for b in self.bad_buys]
        data['bad_sells'] = [b.to_safe_dict() for b in self.bad_sells]
        data['all_transactions'] = [b.to_safe_dict() for b in self.all_transactions]

        stat_data = {}
        for sym, field_data in self.prediction_stats.items():
            stat_data[sym] = {}
            for field, stat in field_data.items():
                stat_data[sym][field] = stat.__dict__
        data['prediction_stats'] = stat_data

        return data


