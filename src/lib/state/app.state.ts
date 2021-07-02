import { atom, selector } from "recoil";
import { BarInfo, BarState } from "@utils/models";
import { KoiState } from '@types';

/***************
 * PYTHON STATE
 ***************/




// Koi State
export const koiState = atom<KoiState>({
  key: 'koiState',
  default: {
    strategies: [],
    ib_connected: false,
    market_ticks_streaming: false,
    crypto_ticks_streaming: false,
  },
});
export const getKoiState = selector({
  key: 'getKoiState',
  get: ({ get }) =>  get(koiState)
});





/***************
 * APP STATE
 ***************/

export const activePage = atom<'trade' | 'analysis' | 'backtest'>({
  key: 'activePage',
  default: 'trade',
});
export const getActivePage = selector({
  key: 'getActivePage',
  get: ({ get }) =>  get(activePage)
});



export const darkModeEnabled = atom<boolean>({
  key: 'darkModeEnabled',
  default: false,
});
export const getDarkModeEnabled = selector({
  key: 'getDarkModeEnabled',
  get: ({ get }) =>  get(darkModeEnabled)
});














// Strategy Selection
export const selectedStategyIndex = atom<number>({
  key: 'selectedStrategyIndex',
  default: 0,
});

export const getSelectedStategy = selector({
  key: "getSelectedStategy",
  get: ({ get }) => {
    const { strategies } = get(koiState);
    const selectedIndex = get(selectedStategyIndex);

    if (strategies.length === 0 || strategies.length <= selectedIndex) {
      return null;
    }
    return strategies[selectedIndex];
  },
});





// Bars
export type HistoryRange = { sell: string, buy: string };
export const isHistoryRange = (obj: any): obj is HistoryRange => typeof obj === 'object' && obj['sell'] && obj['buy'];
export type HistorySize = 'none' | 'min' | 'preview' | 'full' | HistoryRange;

export const barHistorySize = atom<HistorySize>({
  key: 'barHistorySize',
  default: 'min',
});

export const barHistorySizeSelector = selector({
  key: "barHistorySizeSelector",
  get: ({ get }) =>  get(barHistorySize)
});


export const barDirection = atom<'asc' | 'desc'>({
  key: 'barDirection',
  default: 'asc',
});

export const getBarDirection = selector({
  key: "getBarDirection",
  get: ({ get }) =>  get(barDirection)
});




export const selectedBarsSymbol = atom<string | null>({
  key: 'selectedBarsSymbol',
  default: null,
});

export const selectedBarsSymbolSelector = selector({
  key: "selectedBarsSymbolSelector",
  get: ({ get }) =>  get(selectedBarsSymbol)
});


export const barsState = atom<BarState>({
  key: 'barsState',
  default: {},
});
export const getBarsState = selector<BarState | null>({
  key: 'getBarsState',
  get: ({ get }) =>  {
    const state = get(barsState);
    
    console.log('getting bar state:', state);
    if (!state) return {};
    if (typeof state === 'object' && Object.keys(state).length > 0) return state;
    return {};
  }
});

export const visibleBars = selector<BarInfo | null>({
  key: 'visibleBars',
  get: ({ get }) => {
    const allBars = get(barsState);
    const direction = get(getBarDirection);
    const activeSymbol = get(selectedBarsSymbolSelector);

    if (!allBars || !activeSymbol) return null;

    // Grab bars forr selected symbol & reverse to show to most recent first
    const activeBars = { ...allBars[activeSymbol] };
    if (!activeBars || !activeBars.data) return null;
  
    // activeBars.data = activeBars.data.reverse();
    // const reversedData = activeBars.data.reverse();
    if (direction === 'desc') activeBars.data = activeBars.data.reverse()

    const size = get(barHistorySize);
    if (isHistoryRange(size)) {
      // Date is the second index + we reversed so we start our range at the sell point - a window of 3
      let start_range = activeBars.data.findIndex(d => d[1] === size.sell);
      console.log(`start range:${start_range}`)
      if (direction === 'asc') {
        if (start_range + 3 < activeBars.data.length) start_range += 3;
        else start_range = activeBars.data.length;
      } else {
        if (start_range > 3) start_range -= 3;
        else start_range = 0;
      }
      console.log(`adj start range:${start_range}`)


      let end_range = activeBars.data.findIndex(d => d[1] === size.buy);
      console.log(`end range:${end_range}`)
      if (direction === 'asc') {
        if (end_range > 3) end_range -= 3;
        else end_range = 0;
      } else {
        if (end_range + 3 < activeBars.data.length) end_range += 3;
        else end_range = activeBars.data.length;
      }
      console.log(`adj end range:${end_range}`)

      if (direction === 'asc') {
        console.log(`bars for (${end_range}, ${start_range})`)
        activeBars.data = activeBars.data.slice(end_range, start_range);
      } else {
        console.log(`bars for (${start_range}, ${end_range})`)
        activeBars.data = activeBars.data.slice(start_range, end_range);
      }
    } else {
      switch (get(barHistorySize)) {
        case 'none':
          activeBars.data = [];
          break;
        case 'min':
          activeBars.data = activeBars.data.slice(0, 5);
          break;
        case 'preview':
          activeBars.data = activeBars.data.slice(0, 30);
          break;
      }
    }

    return activeBars;
  },
});


