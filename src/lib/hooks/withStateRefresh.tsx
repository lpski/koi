import { useRecoilState, useRecoilValue, useSetRecoilState } from 'recoil';
import useInterval from 'use-interval';
import { TickData, BarState, TickState } from '@utils/models';
import {
  BacktestsState, backtestsState, tickState, koiState, getSelectedStategy,
  barsState, analysisState, AnalysisState, getTickStreamingActive, selectedAnalysisName,
  selectedAnalysisWindow, selectedAnalysisSymbol, selectedExtremesSize, getActivePage,
  getSelectedBacktestName, getTickTab
} from '@state';
import { isKoiState } from '../types/app.types';


const WithStateRefresh = ({ children }: any) => {
  const [currentTickState, setTickState] = useRecoilState(tickState);
  const setKoiState = useSetRecoilState(koiState);
  const setBarsState = useSetRecoilState(barsState);
  const setBacktestsState = useSetRecoilState(backtestsState);
  const selectedStrategy = useRecoilValue(getSelectedStategy);
  const page = useRecoilValue(getActivePage);




  // Koi State
  useInterval(() => {
    if (!window.eel) return;

    window.eel.fetch_state()((data: string) =>{
      try {
        const state = JSON.parse(data);
        if (isKoiState(state)) setKoiState(state)
      } catch {}
    });
  }, 1000);



useInterval(() => {
  window.eel.heartbeat()((message: string) => {
    console.log('heartbeat:', message)
  })
}, 5000)
  

  // Tick State
  const tickStreamingActive = useRecoilValue(getTickStreamingActive);
  const tickTab = useRecoilValue(getTickTab);
  useInterval(() => {
    if (!window.eel || !tickStreamingActive || page !== 'trade') return;

    if (tickTab === 'crypto') {
      window.eel.fetch_crypto_tick_data()((data: { [symbol: string]: TickData }) => {
        const newState: TickState = { market: currentTickState.market, crypto: data };
        setTickState(newState);
      });
    } else {
      window.eel.fetch_market_tick_data()((data: { [symbol: string]: TickData }) => {
        const newState: TickState = { crypto: currentTickState.crypto, market: data };
        setTickState(newState);
      });
    }

  }, 1000);



  // Trader Bars
  useInterval(() => {
    if (!window.eel || !selectedStrategy || page !== 'trade') return;
    
    console.log(`fetching trader bars: ${selectedStrategy.name}`);
    window.eel.fetch_trader_bars(selectedStrategy.name)((data: BarState) => {
      console.log('fetched bars:', data)
      setBarsState(data);
    });
  }, 1000);


  // Backtest State & bars
  useInterval(() => {
    if (!window.eel || page !== 'backtest') return;

    try {
      window.eel.fetch_backtest_performances()((backtests: BacktestsState) => {
        setBacktestsState(backtests)
      });
    }
    catch {}
  }, 500);

  const btName = useRecoilValue(getSelectedBacktestName);
  useInterval(() => {
    if (!window.eel || !selectedStrategy || page !== 'backtest' || !btName) {
      return;
    }

    window.eel.fetch_backtest_bars(btName)((data: BarState) => {
      console.log('backtest bars:', data)
      setBarsState(data);
    });
  }, 1000);



  // Analysis State
  const setAnalysisState = useSetRecoilState(analysisState);
  const [selectedAnalysis, setSelectedAnalysis] = useRecoilState(selectedAnalysisName);
  const [analysisWindow, setAnalysisWindow] = useRecoilState(selectedAnalysisWindow);
  const [analysisSymbol, setAnalysisSymbol] = useRecoilState(selectedAnalysisSymbol);
  const [extremesSize, setExtremesSize] = useRecoilState(selectedExtremesSize);

  useInterval(() => {
    if (!window.eel || page !== 'analysis') return;
  
    window.eel.fetch_analyses()((analyses: AnalysisState) => {
      setAnalysisState(analyses);

      // Set initial selections if necessary
      if (Object.keys(analyses).length > 0) {
        let selected = selectedAnalysis;
        if (!selectedAnalysis) {
          selected = Object.keys(analyses)[0];
          setSelectedAnalysis(Object.keys(analyses)[0]);
        }

        if (selected) {
          if (!analysisWindow && analyses[selected].window_sizes && analyses[selected].window_sizes.length > 0) {
            setAnalysisWindow(analyses[selected].window_sizes[0]);
          }

          if (!extremesSize && analyses[selected].extremes_sizes && analyses[selected].extremes_sizes.length > 0) {
            setExtremesSize(analyses[selected].extremes_sizes[0]);
          }
  
          if (!analysisSymbol && analyses[selected].analysis_data && Object.keys(analyses[selected].analysis_data).length > 0) {
            setAnalysisSymbol(Object.keys(analyses[selected].analysis_data)[0]);
          }
        }
      }
    });
  }, 5000);


  return <>{children}</>
}

export default WithStateRefresh;
