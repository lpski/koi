
export interface Portfolio {
  hold_start_price: number;
  hold_start_shares: number;
  has_stock: boolean;
  purchase_price: number;
  profit: boolean;
  quantity: number;
  gross_profit: number;
  stop_loss_pct: number;
  stop_loss_price: number;
  purchases: number;
}

export interface ContractData {
  symbol: string;
  exchange: string;
  currency: string;
  contract_type: 'FOREX' | 'STOCK' | 'INDEX';
  whatToShow?: string;
  pair?: string;
  primaryExchange?: string;
}

export interface CryptoData {
  market: string;
  currency: string;
}
export const isCryptoData = (obj: any): obj is CryptoData => (
  typeof obj === 'object' && typeof obj.market === 'string' && typeof obj.currency === 'string'
)
export const isCryptoDataList = (obj: any): obj is CryptoData[] => (
  Array.isArray(obj) && obj.every(c => (
    typeof c === 'object' && typeof c.market === 'string' && typeof c.currency === 'string'
  ))
)

export interface StrategyInfo {
  name: string;
  equity: number;
  available_capital: number;
  initial_capital: number;
  active: boolean;
  contracts: ContractData[] | CryptoData[];
  portfolios: { [sym: string]: Portfolio }
  start_date: string;
  description: string;
  crypto: boolean;

  trade_config: {
    trade_frequency: number;
    stop_loss_pct: number;
    recent_data_duration: string;
    train_pct: number;
    train_duration: string;
  }
  analysis_config: {
    duration: string;
    correlation_threshold: number;
    accuracy_threshold: number;
  }
}

export interface KoiState {
  strategies: StrategyInfo[];
  market_data?: { [sym: string]: { [attr: string]: number } };
  ib_connected: boolean;
  market_ticks_streaming: boolean;
  crypto_ticks_streaming: boolean;
}


export const isKoiState = (obj: any): obj is KoiState => {
  if (typeof (obj) !== 'object') return false;
  if (typeof(obj.ib_connected) !== 'boolean') return false;
  if (typeof(obj.market_ticks_streaming) !== 'boolean' || typeof(obj.crypto_ticks_streaming) !== 'boolean' )
  if (!Array.isArray(obj.strategies)) return false;

  return true;
}
