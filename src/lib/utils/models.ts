
export interface BarData {
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  average: number;
  barCount: number;
  vol_diff: number
  vol_pct_change: number;
  price_diff: number;
  price_pct_change: number;
  vol_ma_20: number;
  vol_std_20: number;
  low_vol: boolean;
  SMA_6: number;
  SMA_18: number;
  ADX_4: number;
  DMP_4: number;
  DMN_4: number;
  ADX_3: number;
  DMP_3: number;
  DMN_3: number;
  ADX_16: number;
  DMP_16: number;
  DMN_16: number;
};

export interface TickData {
  ask?: string;
  prevAsk?: string;
  askSize?: string;
  prevAskSize?: string;
  bid?: string;
  prevBid?: string;
  bidSize?: string;
  prevBidSize?: string;
  close?: string;
  high?: string;
  low?: string;
  open?: string;
  time?: string;
}

export interface TickState {
  market: { [symbol: string]: TickData };
  crypto: { [symbol: string]: TickData };
}
// export type BarState = {[symbol: string]: BarData};


// Python format is as so:
// {
//      'index': ['row1', 'row2'],
//      'columns': ['col1', 'col2'],
//      'data': [[1, 0.5], [2, 0.75]]
// }


export interface BarInfo {
  index: string[];
  columns: string[];
  data: any[][];
}
export interface BarState {
  [symbol: string]: BarInfo;
}





// TICKERS
export interface TickerDisplay {
  symbol: string;
  close: string;

  ask: string;
  rawAsk: number;
  askDiff: string;
  askIcon: string;
  askColor: string;

  askVol: string;
  askVolIcon: string;
  askVolColor: string;
  rawAskVol: number;
  askVolDiff: string;

  bidVol: string;
  bidVolIcon: string;
  bidVolColor: string;
  rawBidVol: number;
  bidVolDiff: string;

  day_change: number;
  day_change_pct: number;
}















// Temp
export interface Strategy {
  name: string;
  // aggressiveness: number;
  tickers: string[];
  active: boolean;
  capital: number;
  description: string;
  percentage: number;
  iconName: string;
  iconColor: string;
  direction: 'up' | 'down' | 'flat'
}

export interface StrategyStats {
  holdProfit: number;
  strategyPerformance: number; // Total gain percentage for the strategy vs initial capital
  comparedPerformance: number; // Strategy performance over that of holding the stocks proportionally
}