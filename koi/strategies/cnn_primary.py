import asyncio
from asyncio.events import AbstractEventLoop
from threading import Thread
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple

from koi.strategies.root import StrategyInterface, StrategyTarget
from koi.models import BuyQuantity, Decision, Direction, Move, Opportunity, Prediction
from koi.modeling.cnn import CNN_Manager
from koi.modeling.arima import predict as arima_predict

class Strategy(StrategyInterface):
    # Interface attributes
    name = 'CNN-Managed'
    description = 'CNN based predictions with ARIMA confirmation'
    targets = [StrategyTarget.cnn]

    # Strategy-specific attributes
    predictions: Dict[str, List[Prediction]] = {}

    
    def determine_next_move(self, dfs: Dict[str, pd.DataFrame]) -> Tuple[List[Decision], Dict[str, List[Prediction]]]:
        """Called with each new iteration of data - fits, predicts, and decides using updated dataframe"""

        # If date hasn't been set yet (likely backtest) go ahead and set it
        if not self.start_date or self.start_date == '':
            self.start_date = list(dfs.values())[0].iloc[0]['date']

        self.fit(dfs)

        decisions: List[Decision] = []
        buy_opportunities: List[Opportunity] = []
        pending_capital: float = self.available_capital # dictates quantity gained by potential sells
        for c in self.contracts:
            p = self.portfolios[c.symbol]

            if p.has_stock:
                (sell, confidence, reason) = self.should_sell(dfs[c.symbol], c.symbol)
                print(f'{c.symbol} should sell: {sell} | {reason}')
                if sell:
                    decisions.append(Decision(Move.Sell, c, p.quantity, confidence, reason))
                    pending_capital += (p.quantity * p.purchase_price * .8)
            else:
                (buy, confidence, reason) = self.should_buy(dfs[c.symbol], c.symbol)
                print(f'{c.symbol} should buy: {buy} | {reason}')
                if buy: buy_opportunities.append(Opportunity(c, confidence, reason))

        # If we've been holding on to stock for a while and there are better opportunities, take them
        # long_owned = [c for c in self.contracts if self.portfolios[c.symbol].has_stock and self.portfolios[c.symbol].hold_duration >= self.cnn_config.lookback]
        # for contract in long_owned:
        #     sym_decisions = [d for d in decisions if d.symbol == contract.symbol]
        #     lo_decision: Optional[Decision] = sym_decisions[0] if len(sym_decisions) > 0 else None

        #     if lo_decision is None or lo_decision.move == Move.Buy:
        #         lo_buy_conf = self.portfolios[contract.symbol].confidence if lo_decision is None else lo_decision.confidence
        #         better_opp_available = any([(opp.confidence >= lo_buy_conf and opp.contract.symbol != contract.symbol) for opp in buy_opportunities])

        #         if better_opp_available:
        #             print('Forcing sell of long held symbol')
        #             decisions = [d for d in decisions if d.symbol != contract.symbol] + [Decision(Move.Sell, contract, self.portfolios[contract.symbol].quantity, 0, 'Better capital opportunities present')]
        #             buy_opportunities = [opp for opp in buy_opportunities if opp.contract.symbol != contract.symbol]

        if len(buy_opportunities) > 0 and pending_capital > 10:
            # TODO: Allow for more than one opportunity to be taken at a time
            # best_opportunity = sorted(buy_opportunities, key=lambda o:o.confidence, reverse=True)[0]
            best_opportunity = sorted(buy_opportunities, key=lambda o:o.confidence - self.cnn_manager.conf_threshold[o.contract.symbol], reverse=True)[0]
            decisions.append(Decision(Move.Buy, best_opportunity.contract, BuyQuantity.Max, best_opportunity.confidence, best_opportunity.description))

        print('\n\n')
        return (decisions, self.predictions)

    





    ##################
    #
    #   PREPARATION
    #
    ##################

    async def prepare(self, train_dfs: Dict[str, pd.DataFrame] = None, analyze_dfs: Dict[str, pd.DataFrame] = None, main_loop: AbstractEventLoop = None):
        """Kicks off pre-trading training & analysis"""
        print(f'{self.name}:Strategy:prepare')

        if train_dfs is None or analyze_dfs is None:
            raise 'One of train_dfs or analyze_dfs not provided.'

        # group = asyncio.gather(*[self.train_cnns(train_dfs)])
        # asyncio.get_event_loop().run_until_complete(group)
        asyncio.get_event_loop().run_until_complete(self.train_cnns(train_dfs))

        print(f'{self.name}:Strategy:prepare complete')
        self.prepared = True
        return True


    # Models

    async def train_cnns(self, dfs: Dict[str, pd.DataFrame]):
        """Kicks off cnn training for multiple dataframes in parallel"""
        threads: List[Thread] = []
        for sym, df in dfs.items():
            threads.append(Thread(target=self.cnn_manager.train, args=(df, sym)))
        for t in threads: t.start()
        for t in threads: t.join()

        # Ensure All previously trained models are also loaded in
        # self.cnn_manager.load_existing_models(list(self.portfolios.keys()))
        self.cnn_manager.load_existing_models([c.symbol for c in self.contracts])

        print(f'{self.name}:Strategy:train_cnns complete')
        return True



    ##################
    #
    #   FITTING
    #
    ##################

    def fit(self, dfs: Dict[str, pd.DataFrame]):
        # reset state vars
        self.predictions = {}

        for sym, df in dfs.items():
            # Update portfolio hold duration if has stock
            if self.portfolios[sym].has_stock: self.portfolios[sym].hold_duration += 1

            # Get predictions for the various estimation strategies
            # arima_pred = arima_predict(df)
            cnn_pred = self.cnn_manager.predict(df, sym, self.is_backtest)
            # Save them for later decision making
            self.predictions[sym] = [cnn_pred]
            # print(f'{sym} arima recomendation: {arima_pred.direction}')
            




    ##################
    #
    #   DECISION
    #
    ##################

    def should_buy(self, df: pd.DataFrame, symbol: str) -> Tuple[bool, float, str]:
        """
        Given a dataframe for a particular asset, determines if there is a good buy opportunity
        Returns: Tuple[should_buy: bool, confidence: float, reason: str]
        """

        # Low available capital, ignore predictions
        if self.available_capital < 20:
            return (False, 1, 'low available capital')

        # End of day, don't buy
        frame = df.iloc[-1]
        if frame['date'].hour >= 15 and frame['date'].minute > 50:
            return (False, 1, 'end of day')



        # Otherwise, make a decision based fitted predictions
        preds = self.predictions[symbol]
        # arima_pred = list(filter(lambda p: p.source == 'arima', preds))[0]
        cnn_pred = list(filter(lambda p: p.source == 'cnn', preds))[0]

        if cnn_pred.direction != Direction.Unsure:
            if cnn_pred.direction == Direction.Up and cnn_pred.confidence > self.cnn_manager.conf_threshold[symbol]:
                return (True, cnn_pred.confidence, cnn_pred.description)
            elif cnn_pred.direction == Direction.Up:
                print('Low confidence up prdiction | Consider buying here if arima pred is Up?')
            elif cnn_pred.direction == Direction.Down:
                return (False, cnn_pred.confidence, cnn_pred.description)
        

        return (False, 0, 'no solid prediction')


    def should_sell(self, df: pd.DataFrame, symbol: str) -> Tuple[bool, float, str]:
        """
        Given a dataframe for a particular asset, determines if selling is the best decision
        """
        frame = df.iloc[-1]
        portfolio = self.portfolios[symbol]
        profitable = portfolio.purchase_price < df.iloc[-1]['close']

        # If stop loss was hit, ignore predictions & sell
        if frame['close'] < self.portfolios[symbol].stop_loss_price:
            return (True, 1, 'hit stop loss')

        # End of day, close position if profitable
        frame = df.iloc[-1]
        # if frame['date'].hour > 15 and frame['date'].minute > 55 and self.portfolios[symbol].purchase_price < frame['close']:
        if frame['date'].hour >= 15 and frame['date'].minute > 50:
            return (True, 1, 'end of day')

        # Min hold period not met
        


        # Otherwise, make a decision based fitted predictions
        preds = self.predictions[symbol]
        # arima_pred = list(filter(lambda p: p.source == 'arima', preds))[0]
        cnn_pred = list(filter(lambda p: p.source == 'cnn', preds))[0]


        if portfolio.hold_duration < self.cnn_manager.models[symbol][4]:
            return (False, .5, 'under CNN hold duration threshold')

        # if cnn_pred.direction == Direction.Down:
        if cnn_pred.direction != Direction.Up:
            return (True, cnn_pred.confidence, cnn_pred.description)

        if cnn_pred.direction == Direction.Up:
            # if not profitable: return (False, cnn_pred.confidence, 'under CNN high confidence threshold, not yet profitable')
            # else: return (cnn_pred.confidence < self.cnn_manager.conf_threshold[symbol], cnn_pred.confidence, 'under CNN high confidence threshold, at a profitable point')
            threshold_met = cnn_pred.confidence >= self.cnn_manager.conf_threshold[symbol]
            return (not threshold_met, cnn_pred.confidence, f'{"over" if threshold_met else "under"} CNN high confidence threshold ({cnn_pred.confidence} {">" if threshold_met else "<"} {self.cnn_manager.conf_threshold[symbol]})')


        print(f'{symbol} should sell | no matched prediction')
        return (True, 0, 'no matched prediction')

