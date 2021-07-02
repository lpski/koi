import { atom, selector } from "recoil";

export interface Stat {
  correct: number;
  incorrect: number;
  unsure: number;
  total: number;
  percentage: number;
}
export interface TransactionHistory {
  purchase_date: string;
  sell_date: string;
  pl: number;
  symbol: string;
}
export interface TransactionReport {
  date: string;
  symbol: string;
  transaction_type: 'Buy' | 'Sell';
  strike: number;
  quantity: number;
  confidence: number;
  hold_length: number;
  tradePL: number;
  portfolioPL: number;
  totalPL: number;
  reason: string;

  [key: string]: any;
}
export interface Portfolio {
  has_stock: boolean;
  hold_start_price: number;
  hold_start_shares: number;
  gross_profit: number;
  profit: number;
  purchase_date: string;
  purchase_price: number;
  purchases: number;
  quantity: number;
  stop_loss_pct: number;
  stop_loss_price: number;
  symbol: string;
}
export interface Backtest {
  name: string;
  active: boolean;
  observations: number;
  initial_capital: number;
  buys: {[symbol: string]: number};
  total_buys: number;
  total_sells: number;
  hold_profit: number;
  strategy_profit: number;
  largest_profit?: TransactionHistory;
  largest_loss?: TransactionHistory;
  largest_missed_profit?: TransactionHistory;
  stage: 'setup' | 'testing' | 'complete';
  good_buys: TransactionReport[];
  bad_buys: TransactionReport[];
  bad_sells: TransactionReport[];
  all_transactions: TransactionReport[];
  portfolios: Portfolio[];
  test_size: number;
  prediction_stats: {[symbol: string]: {[field: string]: Stat }}
}
export type BacktestsState = { [symbol: string]: Backtest }



export const backtestsState = atom<BacktestsState>({
  key: 'backtestsState',
  default: {},
});
export const getBacktestsState = selector({
  key: 'getBacktestsState',
  get: ({ get }) => get(backtestsState)
});

export const selectedBacktestName = atom<string | null>({
  key: 'selectedBacktestName',
  default: null,
});
export const getSelectedBacktestName = selector({
  key: 'getSelectedBacktestName',
  get: ({ get }) => get(selectedBacktestName)
});


export const getSelectedBacktest = selector({
  key: 'getSelectedBacktest',
  get: ({ get }) => {
    const name = get(getSelectedBacktestName)
    const backtests = get(getBacktestsState)
    if (!name || !(Object.keys(backtests).includes(name))) return null;
    return backtests[name]
  }
});


export type TransactionCategory = 'all' | 'buys' | 'sells' | 'good' | 'bad';
export const transactionCategory = atom<TransactionCategory>({
  key: 'transactionCategory',
  default: 'all',
});
export const getTransactionCategory = selector({
  key: 'getTransactionCategory',
  get: ({ get }) => get(transactionCategory)
});





export type TransactionPair = { buy: TransactionReport, sell: TransactionReport }
export const isTransactionPairList = (obj: any): obj is TransactionPair[] => {
  if (!Array.isArray(obj)) return false;
  if (obj.length === 0) return false;
  

  return obj.every(item => ('buy' in item && 'sell' in item))
}

const getTransactionPairs = (transactions: TransactionReport[]): TransactionPair[] => {
  const pairs: TransactionPair[] = [];

  // Iterate through all transactions to pair up transactions
  let pairMap: {[sym: string]: { buy: TransactionReport, sell?: TransactionReport }} = {}
  for (let t of transactions) {
    if (t.symbol in pairMap) {
      if (t.transaction_type === 'Buy') {
        pairMap[t.symbol] = { buy: t }
      } else {
        pairMap[t.symbol].sell = t
        pairs.push({ ...pairMap[t.symbol] } as TransactionPair)
        delete pairMap[t.symbol]
      }
    }
  }


  return pairs;
}

export const getVisibleTransactions = selector<TransactionReport[] | TransactionPair[]>({
  key: 'getVisibleTransactions',
  get: ({ get }) => {
    const category = get(getTransactionCategory)
    const backtest = get(getSelectedBacktest)
    if (!backtest) return []

    try {
      switch (category) {
        case 'all': return backtest.all_transactions;
        case 'buys': return backtest.all_transactions.filter(t => t.transaction_type === 'Buy');
        case 'sells': return backtest.all_transactions.filter(t => t.transaction_type === 'Sell');
        case 'good':
          const goodPairs = getTransactionPairs(backtest.all_transactions).filter(({ sell }) => sell.tradePL > 0)
          return goodPairs.sort((a, b) => b.sell.tradePL - a.sell.tradePL)
        case 'bad':
          const badPairs = getTransactionPairs(backtest.all_transactions).filter(({ sell }) => sell.tradePL < 0)
          return badPairs.sort((a, b) => a.sell.tradePL - b.sell.tradePL)
      }
    } catch (e) {
      console.log('getVisibleTransactions: error:', e)
      return []
    }
  }
});
