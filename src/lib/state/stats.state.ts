import { StrategyStats } from "@utils/models";
import { selector } from "recoil";
import { getKoiState, getSelectedStategy } from './app.state';
import { getTickState } from './ticks.state';

// Profit

export const getStrategyStats = selector<{[symbol: string]: StrategyStats}>({
  key: "getStrategyStats",
  get: ({ get }) => {
    const { strategies } = get(getKoiState);
    // const strategy = get(getSelectedStategy);
    const ticks = get(getTickState);

    const stats: {[symbol: string]: StrategyStats} = {};
    if (strategies.length === 0) return stats;
    if (!ticks || Object.keys(ticks).length === 0) {
      strategies.forEach(({ portfolios, name }) => {
        stats[name] = { holdProfit: 0, strategyPerformance: 0, comparedPerformance: 0 };
      })
    } else {

      strategies.forEach(({ portfolios, name, initial_capital, crypto }) => {
        if (Object.keys(portfolios).length === 0) {
          stats[name] = { holdProfit: 0, strategyPerformance: 0, comparedPerformance: 0 };
        } else {
          // Hold stats
          const relevant_ticks = crypto ? ticks.crypto : ticks.market;
          const holdProfits = Object.entries(portfolios).map(([sym, portfolio]) => (
            (initial_capital / portfolio.hold_start_price) * parseFloat(relevant_ticks[sym]?.ask || '0') / Object.keys(portfolios).length
          ));
          const totalHoldProfit = holdProfits.reduce((sum, cur) => sum + cur, 0);

          const totalStrategyProfit = Object.values(portfolios).map(p => p.gross_profit).reduce((sum, cur) => sum + cur, 0)
          const strategyPerformance = totalStrategyProfit / initial_capital * 100
          const comparedPerformance = (totalStrategyProfit - totalHoldProfit) / initial_capital * 100
          stats[name] = { holdProfit: totalHoldProfit, strategyPerformance, comparedPerformance };
        }
      })
    }

    return stats;
  },
});


interface Holding { symbol: string; quantity: number; price: number; pl: number; }
export const getHoldings = selector<Holding[]>({
  key: "getHoldings",
  get: ({ get }) => {
    const strategy = get(getSelectedStategy);
    const tickState = get(getTickState);

    // Ensure data is populated
    if (!strategy || !tickState) return [];
    const ticks = strategy.crypto ? tickState.crypto : tickState.market;
    if (!ticks || !(Object.keys(ticks).length > 0) || !(Object.keys(strategy.portfolios).length > 0)) {
      return []
    }

    const holdings: Holding[] = [];
    Object.entries(strategy.portfolios).forEach(([symbol, portfolio]) => {
      if (portfolio.has_stock) {
        const tickData = ticks[symbol];
        const ask = tickData.ask ? parseFloat(tickData.ask) : portfolio.purchase_price;
        holdings.push({
          symbol,
          quantity: portfolio.quantity,
          price: portfolio.purchase_price,
          pl: ask - portfolio.purchase_price
        });
      }
    });

    return holdings;
  },
});