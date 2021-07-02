import asyncio
from asyncio.events import AbstractEventLoop
from threading import Thread
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple

from koi.strategies.root import StrategyInterface, StrategyTarget
from koi.models import BuyQuantity, Decision, Direction, Move, Opportunity, Prediction, TradeConfig
from koi.modeling.gmm import GMM
from koi.modeling.arima import predict as arima_predict

class Strategy(StrategyInterface):
    # Interface attributes
    name = 'Social-Managed'
    description = '5 minute ranged v1 mixed + arima estimation'
    targets = [StrategyTarget.volume, StrategyTarget.arima, StrategyTarget.gmm]
    trade_config = TradeConfig(60, 0.03, '7 D', 0.5)

    # Strategy-specific attributes
    predictions: Dict[str, List[Prediction]] = {}

    # gmm
    gmm_models: Dict[str, GMM] = {}
    RANDOM_STATE = 17
    MAX_ITER = 500
    N_INIT = 50
    N_COMPS = 6
    N_SAMPLES = 1000




    
    def determine_next_move(self, dfs: Dict[str, pd.DataFrame]) -> Tuple[List[Decision], Dict[str, List[Prediction]]]:
        """Called with each new iteration of data - fits, predicts, and decides using updated dataframe"""

        # If date hasn't been set yet (likely backtest) go ahead and set it
        if not self.start_date or self.start_date == '':
            self.start_date = list(dfs.values())[0].iloc[0]['date']

        self.fit(dfs)

        decisions: List[Decision] = []
        buy_opportunities: List[Opportunity] = []
        for c in self.contracts:
            p = self.portfolios[c.symbol]

            if p.has_stock:
                (sell, confidence, reason) = self.should_sell(dfs[c.symbol], c.symbol)
                if sell:
                    decisions.append(Decision(Move.Sell, c, p.quantity, confidence, reason))

            else:
                (buy, confidence, reason) = self.should_buy(dfs[c.symbol], c.symbol)
                if buy:
                    buy_opportunities.append(Opportunity(c, confidence, reason))

        if len(buy_opportunities) > 0 and self.available_capital > 0:
            # TODO: Allow for more than one opportunity to be taken at a time
            best_opportunity = sorted(buy_opportunities, key=lambda o:o.confidence, reverse=True)[0]
            decisions.append(Decision(Move.Buy, best_opportunity.contract, BuyQuantity.Max, best_opportunity.confidence, best_opportunity.description))

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

        group = asyncio.gather(*[
            # self.train_gmms(train_dfs),
            self.analyzer.start(analyze_dfs, None, main_loop, True)
        ])
        asyncio.get_event_loop().run_until_complete(group)

        print(f'{self.name}:Strategy:prepare complete')
        self.prepared = True
        return True


    # GMMs

    async def train_gmms(self, dfs: Dict[str, pd.DataFrame]):
        """Kicks off gmm training for multiple dataframes in parallel"""
        print(f'{self.name}:Strategy:train_gmms')

        threads: List[Thread] = []
        for sym, df in dfs.items():
            self.gmm_models[sym] = GMM(500, 50, 6, 1000)
            threads.append(Thread(target=self.gmm_models[sym].train, args=(df, sym)))
        for t in threads: t.start()
        for t in threads: t.join()

        print(f'{self.name}:Strategy:train_gmms complete')
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
            # gmm_pred = self.gmm_models[sym].predict(df)
            # arima_pred = arima_predict(df)
            # mixed_prediction = self.mixed_predict(sym, df, arima_pred.direction)
            analysis_prediction = self.analyzer.predict(sym, df)

            # Save them for later decision making
            # self.predictions[sym] = [gmm_pred, arima_pred, mixed_prediction, analysis_prediction]
            self.predictions[sym] = [analysis_prediction]
            


    def mixed_predict(self, symbol: str, df: pd.DataFrame, arima_pred: Direction) -> Prediction:
        frame = df.iloc[-1]

        def ma_analysis() -> Tuple[float, float, bool, bool]:
            ma_18 = frame['SMA_18']
            ma_6 = frame['SMA_6']
            below_ma_18 = frame['close'] < frame['SMA_18']
            below_ma_6 = frame['close'] < frame['SMA_6']
            return (ma_18, ma_6, below_ma_18, below_ma_6)
    
        def trend_analysis() -> Tuple[bool, bool, bool, bool]:
            """
            ERI: 75% Accuracy at negative movement detection (~2% of all negatives captured)
            ADX: 65% correlation for trend direction following existing trend
            """

            # ERI:
            df['bear_2_up'] = (df['BEARP_13'] > df.shift()['BEARP_13']) & (df.shift()['BEARP_13'] > df.shift(2)['BEARP_13'])
            df['bull_2_down'] = (df['BULLP_13'] < df.shift()['BULLP_13']) & (df.shift()['BULLP_13'] < df.shift(2)['BULLP_13'])
            
            frame = df.iloc[-1]
            eri_negative_indicator = frame['bear_2_up'] and frame['bull_2_down']

            # ADX:
            #  First check for a trend drought. If present, it is likely that the price will hover around moving average until breakout ~65% certainty
            #  Then, check current trend directions, both around 65% correlation
            adx_active_drought = all(df['ADX_16'][j] < 25 for j in range(df.last_valid_index() - 20, df.last_valid_index() + 1))
            adx_positive_trend = frame['ADX_4'] > 25 and frame['DMP_4'] > frame['DMN_4'] + 10
            adx_negative_trend = frame['ADX_4'] > 25 and frame['DMP_4'] < frame['DMN_4']

            return (eri_negative_indicator, adx_active_drought, adx_positive_trend, adx_negative_trend)


        def flow_analysis(positive_trend: bool, negative_trend: bool) -> Tuple[bool, bool, bool]:
            frame = df.iloc[-1]
            mfi_reversal_signal = False
            if positive_trend:
                recently_above_80 = any([df['MFI_14'][j] >= 80 for j in range(df.last_valid_index() - 4, df.last_valid_index())])
                mfi_reversal_signal = recently_above_80 and frame['MFI_14'] < 80
            elif negative_trend:
                recently_below_20 = any([df['MFI_14'][j] <= 20 for j in range(df.last_valid_index() - 4, df.last_valid_index())])
                mfi_reversal_signal = recently_below_20 and frame['MFI_14'] > 20

            rsi_overbought = frame['RSI_14'] > 70
            rsi_oversold = frame['RSI_14'] < 30

            return (mfi_reversal_signal, rsi_overbought, rsi_oversold)

        
        def psar_analysis() -> Tuple[int, int]:
            consecutive_over = 0
            consecutive_under = 0

            u_i = 1
            while u_i <= len(df) and not np.isnan(df.iloc[-u_i]['PSARl_0.02_0.2']):
                consecutive_under += 1
                u_i += 1

            o_i = 1
            while o_i <= len(df) and not np.isnan(df.iloc[-o_i]['PSARs_0.02_0.2']):
                consecutive_over += 1
                o_i += 1

            return (consecutive_over, consecutive_under)



        # Obtain indicators
        (ma_18, ma_6, below_ma_18, below_ma_6) = ma_analysis()
        (eri_negative_indicator, adx_active_drought, adx_positive_trend, adx_negative_trend) = trend_analysis()
        (mfi_trend_reversal_likely, rsi_overbought, rsi_oversold) = flow_analysis(adx_positive_trend, adx_negative_trend)
        (consecutive_over, consecutive_under) = psar_analysis()

        # small ones
        bear_indicator: bool = frame['BEARP_13'] > 0 and frame['BEARP_13'] < .01
        large_support_indicator: bool = frame['vol_pct_change'] > 1 and frame['price_diff'] < 0 and below_ma_18 and below_ma_6



        # Make mixed prediction based on indicators
        mixed_preds: List[Prediction] = []


        ## POSITIVE PREDICTORS

        if large_support_indicator and (rsi_oversold or adx_active_drought):
            mixed_preds.append(Prediction('mixed', Direction.Up, .8, 'last move was down but there appears to be large support'))


        # trend based
        if adx_active_drought and below_ma_18 and frame['MFI_14'] < 28:
            mixed_preds.append(Prediction('mixed', Direction.Up, .8, 'active drought with support, will likely move back to ma'))

        if rsi_oversold and not eri_negative_indicator:
            mixed_preds.append(Prediction('mixed', Direction.Up, .5, 'oversold with no indicator for continued negative trend'))

        if adx_active_drought and below_ma_18 and below_ma_6 and frame['vol_diff'] > 0 and arima_pred == Direction.Up:
            mixed_preds.append(Prediction('mixed', Direction.Up, .65, 'active drought, below ma, arima positive prediction'))

        if adx_negative_trend and frame['ADX_3'] > 90 and below_ma_18 and below_ma_6 and frame['vol_pct_change'] > 0:
            mixed_preds.append(Prediction('mixed', Direction.Up, .65, 'negative trend, trend reversal likely, volume increasing'))

        if adx_negative_trend and frame['ADX_3'] > 90 and below_ma_18 and below_ma_6 and frame['vol_pct_change'] > 0:
            mixed_preds.append(Prediction('mixed', Direction.Up, .65, 'negative trend, trend reversal likely, volume increasing'))

        if below_ma_18 and not adx_positive_trend and not adx_negative_trend and frame['ADX_3'] > 40 and frame['DMP_3'] - frame['DMN_3'] > 15 and mfi_trend_reversal_likely:
            mixed_preds.append(Prediction('mixed', Direction.Up, .65, 'no active longterm trend, below ma, recent surge'))


        if frame['SQZ_NO'] > 0:
            mixed_preds.append(Prediction('mixed', Direction.Up, .8, 'active squeeze'))



        ## NEGATIVE PREDICTORS

        if rsi_overbought and adx_positive_trend and (mfi_trend_reversal_likely or arima_pred == Direction.Down) and not below_ma_18:
            mixed_preds.append(Prediction('mixed', Direction.Down, .9, 'overbought, pos trend, above ma and one of [trend reversal signal, negative arima prediction]'))


        if adx_positive_trend and not below_ma_18 and not below_ma_6 and frame['vol_pct_change'] < -.4 and frame['price_diff'] > 0:
            mixed_preds.append(Prediction('mixed', Direction.Down, .6, 'low support at above moving average prices'))

        if consecutive_over > 2 and self.portfolios[symbol].hold_duration > 3 and arima_pred == Direction.Down:
            mixed_preds.append(Prediction('mixed', Direction.Down, .8, 'psar over'))



        ## EXPERIMENTAL PREDICTORS

        # if bear_indicator:
        #     mixed_preds.append(Prediction('mixed', Direction.Up, .75, 'very low but still positive eri bear indicator'))



        # Return most likely prediction
        if len(mixed_preds) == 0: return Prediction('mixed', Direction.Unsure, .5, 'no matched prediction')
        return sorted(mixed_preds, key=lambda p: p.confidence, reverse=True)[0]






    ##################
    #
    #   DECISION
    #
    ##################

    def should_buy(self, df: pd.DataFrame, symbol: str) -> Tuple[bool, float, str]:
        """
        Given a dataframe for a particular asset, determines if there is a good buy opportunity
        Returns: Tuple[should_buy: bool, confidence: float]
        """

        # Low available capital, ignore predictions
        if self.available_capital < 20:
            return (False, 1, 'low available capital')

        # End of day, don't buy
        frame = df.iloc[-1]
        if frame['date'].hour >= 15 and frame['date'].minute > 55:
            return (False, 1, 'end of day')



        # Otherwise, make a decision based fitted predictions
        preds = self.predictions[symbol]
        # arima_pred = list(filter(lambda p: p.source == 'arima', preds))[0]
        # gmm_pred = list(filter(lambda p: p.source == 'gmm', preds))[0]
        # mixed_pred = list(filter(lambda p: p.source == 'mixed', preds))[0]
        analysis_pred = list(filter(lambda p: p.source == 'analysis', preds))[0]

        # if all([s.direction == Direction.Up for s in preds]):
        #     return (True, 1, 'all pos:' + mixed_pred.description)

        # if all([s.direction == Direction.Down for s in preds]):
        #     return (False, 1, 'all neg:' + mixed_pred.description)

        # if analysis_pred.direction != Direction.Unsure and not (mixed_pred.direction != Direction.Up and arima_pred.direction == Direction.Down):
        #     return (analysis_pred.direction == Direction.Up, analysis_pred.confidence, analysis_pred.description)

        if analysis_pred.direction != Direction.Unsure:
            return (analysis_pred.direction == Direction.Up, analysis_pred.confidence, analysis_pred.description)

        # if mixed_pred.confidence > arima_pred.confidence:
        #     return (mixed_pred.direction == Direction.Up, mixed_pred.confidence, mixed_pred.description)

        # arima dir = mixed dir + high vol?
        # if gmm_pred.direction == arima_pred.direction:
        #     return (arima_pred.direction, arima_pred.confidence, 'gmm+arima')
        

        return (False, 0, 'no solid prediction')


    def should_sell(self, df: pd.DataFrame, symbol: str) -> Tuple[bool, float, str]:
        """
        Given a dataframe for a particular asset, determines if selling is the best decision
        """
        frame = df.iloc[-1]
        portfolio = self.portfolios[symbol]

        # If stop loss was hit, ignore predictions & sell
        if frame['close'] < self.portfolios[symbol].stop_loss_price:
            return (True, 1, 'hit stop loss')

        # End of day, close position if profitable
        frame = df.iloc[-1]
        # if frame['date'].hour > 15 and frame['date'].minute > 55 and self.portfolios[symbol].purchase_price < frame['close']:
        if frame['date'].hour >= 15 and frame['date'].minute > 52:
            return (True, 1, 'end of day')

        # Min hold period not met
        


        # Otherwise, make a decision based fitted predictions
        preds = self.predictions[symbol]
        # arima_pred = list(filter(lambda p: p.source == 'arima', preds))[0]
        # gmm_pred = list(filter(lambda p: p.source == 'gmm', preds))[0]
        # mixed_pred = list(filter(lambda p: p.source == 'mixed', preds))[0]
        analysis_pred = list(filter(lambda p: p.source == 'analysis', preds))[0]

        # pred_sum = sum([1 if p.direction == Direction.Up else -1 if p.direction == Direction.Down else 0 for p in preds])

        # if all([s.direction == Direction.Up for s in preds]):
        #     return (False, 1, 'all pos:' + mixed_pred.description)

        # if all([s.direction == Direction.Down for s in preds]):
        #     return (True, 1, 'all neg:' + mixed_pred.description)

        # if analysis_pred.direction != Direction.Down and (mixed_pred.direction == Direction.Down and arima_pred.direction == Direction.Down):
        #     return (True, .6, 'mixed down + arima down')

        if analysis_pred.direction != Direction.Unsure:
            return (analysis_pred.direction == Direction.Down, analysis_pred.confidence, analysis_pred.description)

        not_yet_profitable = frame['close'] - portfolio.purchase_price < 0
        if portfolio.hold_duration < 3 and not_yet_profitable:
            return (False, .5, 'Not yet profitable + under 3 hold iterations')

        # if mixed_pred.confidence > arima_pred.confidence:
        #     return (mixed_pred.direction == Direction.Down, mixed_pred.confidence, mixed_pred.description)

        # if gmm_pred.direction == arima_pred.direction:
        #     return (arima_pred.direction, arima_pred.confidence, 'gmm+arima')

        return (True, 0, 'no matched prediction')

