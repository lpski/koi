import { atom, selector } from "recoil";

export interface Sequence {
  size: number;
  start_index: number;
  cumulative_diff: number;
}

export interface AveragesData {
  overall: {[field: string]: number};
  std: {[field: string]: number};
  positive: {[field: string]: number};
  positiveData: { sum: number; average: number };
  negative: {[field: string]: number};
  negativeData: { sum: number; average: number };
}

export interface ExtremesData {
  sum: number;
  average: number;
  field_averages: { [field: string]: number };
}

export interface AnalysisSizeData {
  sequences: Sequence[];
  window_size_data: { [windowSize: string]: {
    positive_extremes_averages: { [extremesSize: string]: ExtremesData };
    negative_extremes_averages: { [extremesSize: string]: ExtremesData };
    overall_field_averages: {[field: string]: number};
    overall_field_std: {[field: string]: number};
  }}
}
export interface Analysis {
  name?: string;
  stage: 'inactive' | 'data' | 'sequencing' | 'analysis' | 'complete';
  analysis_data: AnalysisData;
  extremes_sizes: number[];
  sequence_sizes: number[];
  window_sizes: number[];
}
export type AnalysisData = { [symbol: string]: { [sequence_size: string]: AnalysisSizeData } };
export type AnalysisState = { [symbol: string]: Analysis }





// Overall State / Active State
export const analysisState = atom<AnalysisState>({
  key: 'analysisState',
  default: {},
});
export const getAnalysisState = selector({
  key: 'getAnalysisState',
  get: ({ get }) => get(analysisState)
});




// Analysis Name
export const selectedAnalysisName = atom<string | null>({
  key: 'selectedAnalysisName',
  default: null,
});
export const getSelectedAnalysisName = selector({
  key: 'getSelectedAnalysisName',
  get: ({ get }) => {
    const selected = get(selectedAnalysisName);
    if (selected) return selected;
    
    const state = get(analysisState);
    if (Object.keys(state).length > 0) return Object.keys(state)[0]

    return null;
  }
});

export const getSelectedAnalysis = selector({
  key: 'getSelectedAnalysis',
  get: ({ get }) => {
    const name = get(getSelectedAnalysisName)
    const analyses = get(getAnalysisState)
    if (!name || !(Object.keys(analyses).includes(name))) return null;
    return analyses[name]
  }
});




// Selected Symbol
export const selectedAnalysisSymbol = atom<string | null>({
  key: 'selectedAnalysisSymbol',
  default: null,
});
export const getSelectedAnalysisSymbol = selector({
  key: 'getSelectedAnalysisSymbol',
  get: ({ get }) => get(selectedAnalysisSymbol)
});

export const getSelectedAnalysisSymbolData = selector({
  key: 'getSelectedAnalysisSymbolData',
  get: ({ get }) => {
    const analysis = get(getSelectedAnalysis)
    const symbol = get(getSelectedAnalysisSymbol)
    if (!analysis || !symbol || !analysis.analysis_data[symbol]) return null;
    return analysis.analysis_data[symbol]
  }
});




// Selected Window Size
export const selectedAnalysisWindow = atom<number | null>({
  key: 'selectedAnalysisWindow',
  default: null,
});
export const getSelectedAnalysisWindow = selector({
  key: 'getSelectedAnalysisWindow',
  get: ({ get }) => get(selectedAnalysisWindow)
});




// Selected Extremes Size
export const selectedExtremesSize = atom<number | null>({
  key: 'selectedExtremesSize',
  default: null,
});
export const getSelectedExtremesSize = selector({
  key: 'getSelectedExtremesSize',
  get: ({ get }) => get(selectedExtremesSize)
});

export const getSelectedExtremesSizeData = selector<{[size: string]: AveragesData} | null>({
  key: 'getSelectedExtremesSizeData',
  get: ({ get }) => {
    const symbolData = get(getSelectedAnalysisSymbolData);
    const extremesSize = get(getSelectedExtremesSize);
    const windowSize = get(getSelectedAnalysisWindow);
    if (!symbolData || !extremesSize || !windowSize) return null;

    const combined: {[size: string]: AveragesData} = {};
    Object.entries(symbolData).forEach(([sequenceSize, sizeData]) => {
      if (sizeData && sizeData.window_size_data && sizeData.window_size_data[windowSize]) {
        const posData = sizeData.window_size_data[windowSize].positive_extremes_averages[`${extremesSize}`];
        const negData = sizeData.window_size_data[windowSize].negative_extremes_averages[`${extremesSize}`];

        if (posData && negData) {
          combined[sequenceSize] = {
            overall: sizeData.window_size_data[windowSize].overall_field_averages,
            std: sizeData.window_size_data[windowSize].overall_field_std,
            positive: posData.field_averages,
            negative: negData.field_averages,
            positiveData: {
              sum: posData.sum,
              average: posData.average
            },
            negativeData: {
              sum: negData.sum,
              average: negData.average
            },
          }
        }
      }
    });

    return combined;
  }
});





