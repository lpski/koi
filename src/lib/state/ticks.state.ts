import { atom, selector } from "recoil";
import { TickerDisplay, TickState } from "@utils/models";
import { getKoiState } from "./app.state";


export const tickState = atom<TickState>({
  key: 'tickState',
  default: { market: {}, crypto: {} },
});

export const getTickState = selector({
  key: 'getTickState',
  get: ({ get }) => get(tickState)
});


export const tickTab = atom<'market' | 'crypto'>({ key: 'tickTab', default: 'market' });
export const getTickTab = selector({ key: 'getTickTab', get: ({ get }) => get(tickTab) });

export const getVisibleTicks = selector({
  key: 'getVisibleTicks',
  get: ({ get }) => {
    const selectedTickTab = get(getTickTab);
    const state = get(tickState);
    if (selectedTickTab === 'market') return state.market;
    else return state.crypto;
  }
});

export const getTickers = selector<TickerDisplay[]>({
  key: 'tickStateSelector',
  get: ({ get }) => {

    return Object.entries(get(getVisibleTicks)).map(([symbol, data]) => {
      const close = parseFloat(data.close || '0'),
        ask = parseFloat(data.ask || '0'),
        prevAsk = parseFloat(data.prevAsk || '0'),
        askVol = parseFloat(data.askSize || '0'),
        prevAskVol = parseFloat(data.prevAskSize || '0'),
        bidVol = parseFloat(data.bidSize || '0'),
        prevBidVol = parseFloat(data.prevBidSize || '0'),
        open = parseFloat(data.open || '0');

      return {
        symbol,
        close: close.toFixed(3),

        ask: ask.toFixed(4),
        askIcon: ask > prevAsk ? 'fa-arrow-up' : ask < prevAsk ? 'fa-arrow-down' : 'fa-arrow-right',
        askColor: ask > prevAsk ? 'text-green-500' : ask < prevAsk ? 'text-red-500' : 'text-orange-500',
        rawAsk: ask,
        askDiff: (ask - prevAsk).toFixed(3),

        askVol: askVol.toFixed(3),
        askVolDiff: (askVol - prevAskVol).toFixed(3),
        askVolIcon: askVol > prevAskVol ? 'fa-arrow-up' : askVol < prevAskVol ? 'fa-arrow-down' : 'fa-arrow-right',
        askVolColor: askVol > prevAskVol ? 'text-green-500' : askVol < prevAskVol ? 'text-red-500' : 'text-orange-500',
        rawAskVol: askVol,

        bidVol: bidVol.toFixed(3),
        bidVolDiff: (bidVol - prevBidVol).toFixed(3),
        bidVolIcon: bidVol > prevBidVol ? 'fa-arrow-up' : bidVol < prevBidVol ? 'fa-arrow-down' : 'fa-arrow-right',
        bidVolColor: bidVol > prevBidVol ? 'text-green-500' : bidVol < prevBidVol ? 'text-red-500' : 'text-orange-500',
        rawBidVol: bidVol,

        day_change: ask - open,
        day_change_pct: (ask - open) / open * 100
      }
    })
  }
});


export const getTickStreamingActive = selector({
  key: 'getTickStreamingActive',
  get: ({ get }) => {
    const koiState = get(getKoiState);
    const tickTab = get(getTickTab);

    if (tickTab === 'crypto') return koiState.crypto_ticks_streaming;
    return koiState.market_ticks_streaming;
  }
});
