import Moment from 'react-moment';
import { useRecoilValue } from 'recoil';
import { useRef, useState } from 'react';

import { TickState } from '@utils/models';
import { getHoldings, getStrategyStats } from '@state';
import { isCryptoDataList, StrategyInfo } from '@types';


export interface StrategyCardProps { strategy: StrategyInfo, ticks: TickState };
const StrategyCard =  ({ strategy }: StrategyCardProps) => {
  const { name, equity, available_capital, portfolios, contracts, trade_config } = strategy;

  const [showConfig, setShowConfig] = useState(false);
  const capitalInput = useRef<HTMLInputElement>()
  const allStats = useRecoilValue(getStrategyStats);
  const holdings = useRecoilValue(getHoldings);

  if (!(name in allStats)) return (
    <div className="relative flex flex-col min-w-0 break-words bg-white dark:bg-off-black rounded mb-6 xl:mb-0 shadow-lg">
      <div className="flex-auto p-4">
        <div className="flex flex-wrap">
         ...
        </div>
      </div>
    </div>
  );

  const stats = allStats[name];
  const modifyStrategyCapital = () => {
    if (capitalInput && capitalInput.current && window.eel) {
      const newCapitalString = capitalInput.current.value;
      try {
        const newCapital = parseFloat(newCapitalString);
        window.eel.set_strategy_capital(strategy.name, newCapital);
      } catch {}
    }
  }

  const triggerBacktest = () => {
    if (window.eel) {
      window.eel.backtest_strategy(strategy.name);
      
      const bt_card = document.querySelector('#backtests');
      bt_card?.scrollIntoView({ block: 'center', behavior: 'smooth'});
    }
  }

  const triggerAnalysis = () => {
    // TODO: check for already running analysis?
    if (window.eel) {
      window.eel.analyze_strategy(strategy.name);
    }
  }

  const toggleStrategyTrading = () => {
    if (window.eel) {
      window.eel.toggle_strategy(strategy.name);
    }
  }

  const formattedTradeFrequency = (): string => {
    const freq = trade_config.trade_frequency
    if (freq < 60) return `${freq} secs`;
    else if (freq / 60 < 60) {
      const mins = Math.floor(freq / 60)
      return `${mins} ${mins > 1 ? 'mins' : 'min'}`;
    } else if (freq / 3600 < 24) {
      const hrs = Math.floor(freq / 3600);
      return `${hrs} ${hrs > 1 ? 'hrs' : 'hr'}`;
    } else {
      const days = Math.floor(freq / 3600 / 24);
      return `${days} ${days > 1 ? 'days' : 'day'}`;
    }
  }


  const normalConfig = ({
    icon: 'fas fa-arrow-' + (stats.strategyPerformance > 0 ? 'up' : stats.strategyPerformance < 0 ? 'down' : 'right'),
    color: 'text-' + (stats.strategyPerformance > 0 ? 'green' : stats.strategyPerformance < 0 ? 'red' : 'orange') + '-500'
  });
  const comparedConfig = ({
    icon: 'fas fa-arrow-' + (stats.comparedPerformance > 0 ? 'up' : stats.comparedPerformance < 0 ? 'down' : 'right'),
    color: 'text-' + (stats.comparedPerformance > 0 ? 'green' : stats.comparedPerformance < 0 ? 'red' : 'orange') + '-500'
  });

  return (
    <>
      <div className="relative flex flex-col divide-y min-w-0 break-words bg-white dark:bg-off-black rounded mb-6 xl:mb-0 shadow-lg border-2 hover:border-indigo-300">
        <div className="flex-auto p-4">
          <div className="flex flex-wrap">

            {/* Name / Equity */}
            <div className="relative pr-4 flex flex-grow flex-1 flex-col">
              <h5 className="text-gray-500 dark:text-white uppercase font-bold text-xs">
                {name}
              </h5>
              <span className="font-semibold text-xl text-gray-800 dark:text-white">
                ${equity}

                <span className="text-xs text-gray-500 dark:text-white ml-1 font-light">{'| equity'}</span>
              </span>
            </div>
            
            {/* Actions */}
            <div className="flex flex-row">
                {/* Strategy Active Toggle */}
                <div className="relative w-auto pl-4 flex-initial cursor-pointer">
                  <div
                    onClick={toggleStrategyTrading}
                    className={`text-white p-3 transition text-center inline-flex items-center justify-center w-8 h-8 shadow-lg rounded-full ${strategy.active ? 'bg-green-400' : 'bg-red-400'} transform hover:scale-105`}
                  >
                    <i className={strategy.active ? 'fas fa-play' : 'fas fa-pause'}></i>
                  </div>
                </div>


                {/* Analyze Strategy Toggle */}
                <div className="relative w-auto pl-4 flex-initial cursor-pointer">
                  <div
                    onClick={triggerAnalysis}
                    className={`text-purple-800 transition p-3 text-center inline-flex items-center justify-center w-8 h-8 shadow-lg rounded-full border border-purple-400 transform hover:scale-105`}
                  >
                    <i className='fas fa-chart-pie'></i>
                  </div>
                </div>

                
                {/* Strategy Backtest Toggle */}
                <div className="relative w-auto pl-4 flex-initial cursor-pointer">
                  <div
                    onClick={triggerBacktest}
                    className={`text-blue-800 transition p-3 text-center inline-flex items-center justify-center w-8 h-8 shadow-lg rounded-full border border-blue-400 transform hover:scale-105`}
                  >
                    <i className='fas fa-vial'></i>
                  </div>
                </div>

                
                {/* Strategy Backtest Toggle */}
                <div className="relative w-auto pl-4 flex-initial cursor-pointer">
                  <div
                    onClick={() => console.log('refreshing portfolios')}
                    className={`text-yellow-600 transition p-3 text-center inline-flex items-center justify-center w-8 h-8 shadow-lg rounded-full border border-yellow-300 transform hover:scale-105`}
                  >
                    <i className='fas fa-sync'></i>
                  </div>
                </div>
                

                {/* Strategy Settings */}
                <div className="relative w-auto pl-4 flex-initial cursor-pointer">
                  <div
                    onClick={() => setShowConfig(!showConfig)}
                    className={`text-gray-400 transition p-3 text-center inline-flex items-center justify-center w-8 h-8 shadow-lg rounded-full border border-gray-400 transform hover:scale-105`}
                  >
                    <i className={`fas fa-${showConfig ? 'times' : 'sliders-h'}`}></i>
                  </div>
                </div>
              </div>
            </div>

          {/* Today Performance */}
          <div className="flex flex-wrap">
            {/* Overall Historical Performance */}
            <p className="text-sm text-gray-500 mt-4">
              <span className="mb-2">today:</span>
              <br />
              <span className={`mr-2 ${normalConfig.color}`}>
                <i className={normalConfig.icon} />
                {" "}
                {stats.strategyPerformance.toFixed(2)}%
              </span>
            </p>

            {/* Vs Hold Performance */}
            <p className="text-sm text-gray-500 mt-4 ml-8">
              <span className="mb-2">vs hold</span>
              <br />
              <span className={`mr-2 ${comparedConfig.color}`}>
                <i className={comparedConfig.icon} />
                {" "}
                {stats.strategyPerformance.toFixed(2)}%
              </span>
            </p>
          </div>


          {/* Strategy Lifetime Performance */}
          <div className="flex flex-wrap">
            {/* Overall Historical Performance */}
            <p className="text-sm text-gray-500 mt-4">
              <span className="mb-2">historical:</span>
              <br />
              <span className={`mr-2 ${normalConfig.color}`}>
                <i className={normalConfig.icon} />
                {" "}
                {stats.strategyPerformance.toFixed(2)}%
              </span>
            </p>

            {/* Vs Hold Performance */}
            <p className="text-sm text-gray-500 mt-4 ml-8">
              <span className="mb-2">vs hold</span>
              <br />
              <span className={`mr-2 ${comparedConfig.color}`}>
                <i className={comparedConfig.icon} />
                {" "}
                {stats.strategyPerformance.toFixed(2)}%
              </span>
              <span className="whitespace-no-wrap">
                {"since "}
                <Moment fromNow>{strategy.start_date}</Moment>
              </span>
            </p>
          </div>

        </div>
        
        {showConfig && (
          <div className="flex flex-col">

            {/* Portfolios */}
            <div className="flex flex-row p-4">

              <div className="flex flex-col relative w-auto ml-1 pr-4 max-w-full flex-grow flex-1">
                <span className="text-xs text-gray-500 font-light">portfolio</span>
                <div className="flex flex-row flex-wrap">

                  {contracts.length > 0 && (
                    isCryptoDataList(contracts) ? (
                      contracts.map(({ currency, market}) => (
                        <span className="border border-indigo-700 py-1 px-2 m-2 text-xs text-indigo-700">
                          {`${market}-${currency}`}
                        </span>
                      ))
                    ) : (
                      contracts.map(({ symbol}) => (
                        <span className="border border-indigo-700 py-1 px-2 m-2 text-xs text-indigo-700">
                          {symbol}
                        </span>
                      ))
                    )
                  )}

                  {contracts.length === 0 && (
                    <span className="text-base text-gray-800 dark:text-white font-medium">No portfolios added</span>
                  )}
                </div>

              </div>
            </div>


            {/* All Holdings */}
            <div className="flex flex-row px-4 py-2">

              <div className="flex flex-col relative w-auto ml-1 pr-4 max-w-full flex-grow flex-1">
                <span className="text-xs text-gray-500 font-light">holdings</span>
                <div className="flex flex-col">
                  {holdings.length > 0 && holdings.map(holding => (
                    <div className="flex space-x-8">
                      
                      <span className="text-base font-semibold">
                        <i className="fas fa-door-closed cursor-pointer hover:text-red-500 mr-1" title="Close Position" />
                        {holding.symbol}
                      </span>
                      <span>{holding.quantity} @ ${holding.price}</span>
                      <span className={`${holding.pl > 0 ? 'text-green-500' : holding.pl < 0 ? 'text-red-500' : 'text-gray-500'}`}>
                        ${isNaN(holding.pl) ? holding.pl : (parseFloat(holding.pl as any)).toFixed(5)}
                      </span>
                    </div>
                  ))}
                  {holdings.length == 0 && (
                    <span className="text-base text-gray-600 dark:text-white font-base">No holdings</span>
                  )}
                </div>

              </div>
            </div>

            {/* Configs */}
            <div className="flex flex-row px-4 py-2 space-x-8 items-start">

              {/* Capital Modification */}
              <div className="flex flex-row min-w-1/2">
                <div className="flex flex-col relative pr-4 w-full">
                  <span className="text-xs text-gray-500 ml-1 font-light">allocated capital</span>
                  <label className="block relative">
                    <div className="absolute inset-y-0 left-0 ml-1 mt-1 flex items-center">
                      <span>$</span>
                    </div>
                    <input type="number" min={0} max={available_capital} className="mt-1 pl-4 block w-full rounded-md bg-gray-100 border-transparent dark:border dark:bg-transparent dark:border-gray-300 dark:text-white focus:border-gray-500 focus:bg-white focus:ring-0" placeholder={available_capital.toFixed(2)} />
                  </label>
                </div>
                <div className="flex items-end pb-2">
                  <svg onClick={modifyStrategyCapital} className="w-6 h-6 cursor-pointer transition transition-color text-gray-400 hover:text-green-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
              </div>

              {/* Trade Frequency */}
              <div className="flex flex-col">
                  <span className="text-xs text-gray-500 ml-1 font-light">trade frequency</span>
                  <span className="text-base text-gray-600 dark:text-white font-base">
                    {formattedTradeFrequency()}
                  </span>
              </div>
            </div>
          </div>
        )}

      </div>
    </>
  );
}

export default StrategyCard;
