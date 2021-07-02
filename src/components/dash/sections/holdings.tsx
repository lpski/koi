import { useRef, useState } from 'react';
import { useRecoilValue, useRecoilState } from 'recoil';
import { StrategyInfo } from '@types';
import { barHistorySize, getKoiState, isHistoryRange, selectedBarsSymbol, visibleBars, barDirection } from '@state';


export interface HoldingsProps { strategy: StrategyInfo }
const Holdings = ({ strategy }: HoldingsProps) => {
  const bars = useRecoilValue(visibleBars);
  const state = useRecoilValue(getKoiState);
  const [currentHistorySize, setHistorySize] = useRecoilState(barHistorySize);
  const [direction, setDirection] = useRecoilState(barDirection);
  const [selectedSymbol, setSelectedSymbol] = useRecoilState(selectedBarsSymbol);
  const [addingInstrument, setAddingInstrument] = useState<boolean>(false);
  const addInstrumentForm = useRef<HTMLFormElement>(null);

  const addInstrumentToStrategy = (e: React.FormEvent<HTMLFormElement>) => {
    console.log('adding new instrument:', e)
    setAddingInstrument(false)
  }

  const extractRowIdentifier = (rowData: any[], index: number): string => {
    const dateColumn = bars?.columns.findIndex(col => col === 'date');
    print()
    if (dateColumn) return rowData[dateColumn] as string;
    else return `${index}`;
  }

  return (
    <div className="holdings-card relative flex flex-col min-w-0 break-words bg-white dark:bg-off-black w-full mb-6 shadow-lg rounded">
      {/* Card Header */}
      <div className="rounded-t mb-0 px-4 py-3 border-0">
        <div className="flex flex-wrap items-center">
          <div className="relative w-full px-4 max-w-full flex-grow flex-1">
            <h3 className="font-semibold text-base text-gray-800 dark:text-white">
              Latest Bars
            </h3>
          </div>
          
          {/* Symbol Tabs */}
          <div className="flex flex-col items-baseline pb-8">
            <div className="ml-auto mr-auto text-xs dark:text-white underline mb-4">Strategy Instruments</div>

            <div className="relative flex text-center text-sm leading-none font-bold text-gray-500">
              {/* {(strategy.contracts || []).map(c => (
                <div className={`relative flex pl-4 pr-4 flex-col justify-center items-center`}>
                  <span onClick={() => setSelectedSymbol(c.symbol)} className={`z-10 w-auto cursor-pointer flex text-black dark:text-white`}>{c.symbol}</span>
                  {(selectedSymbol === c.symbol) && <span className="z-0 w-8 h-1 -mt-1 bg-green-200 dark:bg-gren-800"></span>}
                </div>
              ))} */}

              {/* Add New Instrument */}
              <div className={`relative flex pl-4 pr-4 flex-col items-center`}>
                {addingInstrument ? (
                  <form ref={addInstrumentForm} onSubmit={addInstrumentToStrategy}>
                    <div className="mt-1 relative rounded-md shadow-sm">
                      <input  type="text" name="symbol" id="symbol" className="focus:ring-indigo-500 focus:border-indigo-500 block w-full pl-7 pr-12 sm:text-sm border-gray-300 rounded-md" placeholder="AAPL" />
                      <div className="absolute inset-y-0 right-0 flex items-center">
                        <label htmlFor="instrument_type" className="sr-only">Type</label>
                        <select id="instrument_type" name="instrument_type" className="focus:ring-indigo-500 focus:border-indigo-500 h-full py-0 pl-2 pr-7 border-transparent bg-transparent text-gray-500 sm:text-sm rounded-md">
                          <option>Stock</option>
                          <option>Forex</option>
                          <option>Index</option>
                        </select>
                      </div>

                      <div className="absolute inset-y-0 -right-8 pl-3 flex items-center cursor-pointer w-8 h-full">
                        <svg onClick={() => addInstrumentForm.current?.submit()} className="w-full text-gray-300 hover:text-green-400 transition-colors" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      </div>
                    </div>
                  </form>
                ) : (
                  <span
                    onClick={() => setAddingInstrument(true)}
                    className="z-10 w-4 h-4 cursor-pointer flex text-black hover:text-green-700 transition-all"
                  >
                    <svg className="w-full" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v3m0 0v3m0-3h3m-3 0H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </span>
                )}
              </div>
            </div>
          </div>
          
          
          {/* Visible Quantity / Direction Select */}
          <div className="relative w-full px-4 max-w-full flex-grow flex-1 text-right">
            <div className="flex flex-row justify-end items-center">
              <div className="flex">
                <label htmlFor="barHistorySize" className="sr-only">History</label>
                <select
                  defaultValue="preview"
                  value={isHistoryRange(currentHistorySize) ? 'custom' : currentHistorySize}
                  onChange={(e) => e.target.value !== 'custom' && setHistorySize(e.target.value as any)}
                  id="barHistorySize"
                  name="barHistorySize"
                  className="focus:ring-green-800 focus:border-green-800 cursor-pointer h-full py-0 pl-2 pr-7 border-transparent bg-transparent text-gray-500 sm:text-sm rounded-md"
                >
                  <option value="none">0</option>
                  <option value="min">5</option>
                  <option value="preview">30</option>
                  <option value="full">All</option>
                  {isHistoryRange(currentHistorySize) && <option value="custom">Custom</option>}
                </select>
              </div>

              <div className="flex text-black dark:text-white">
                {direction === 'asc' ? (
                  <svg onClick={() => setDirection('desc')} className="h-4 cursor-pointer" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4h13M3 8h9m-9 4h9m5-4v12m0 0l-4-4m4 4l4-4" />
                  </svg>
                ) : (
                  <svg onClick={() => setDirection('asc')} className="h-4 cursor-pointer" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4h13M3 8h9m-9 4h6m4 0l4-4m0 0l4 4m-4-4v12" />
                  </svg>
                )}
              </div>
            </div>

          </div>

        </div>
      </div>

      <div className="block w-full overflow-x-auto">

        {(state.ib_connected || bars) ? (
          <>
            {bars ? (
              <table className="relative bars-table items-center w-full bg-transparent border-collapse">

                {/* Table Header */}
                <thead>
                  <tr>
                    {bars.columns.map(col => (
                      <th className="px-6 bg-gray-100 text-gray-600 align-middle border border-solid border-gray-200 py-3 text-xs uppercase border-l-0 border-r-0 whitespace-no-wrap font-semibold text-left">
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>

                <tbody>
                  {bars.data.map((rowData, i) => (
                    <tr id={`${selectedSymbol}_` + extractRowIdentifier(rowData, i).replace(/[\:\/ ]/g, '_')}>
                      {rowData.slice(0, 1).map(val => (
                        <th className="border-t-0 px-6 align-middle border-l-0 border-r-0 text-xs whitespace-no-wrap p-4 text-left">
                          {val}
                        </th>
                      ))}
                      {rowData.slice(1).map((val, i) => (
                        <td className="border-t-0 px-6 align-middle border-l-0 border-r-0 text-xs whitespace-no-wrap p-4">
                          <div className='tooltip relative'>
                            {isNaN(val) ? val : (parseFloat(val)).toFixed(5)}
                            <span className="tooltip-text bg-yellow-400 border rounded border-orange-500 text-orange-700 -mt-10 left-0">{bars.columns[i + 1]}</span>
                          </div>
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="w-full h-full flex flex-col mb-4 justify-center items-center">
                {/* No Active Instrument Warning */}
                <span className="text-xl text-gray-800 dark:text-white font-semibold">No Instrument Selected</span>
                <span className="text-md text-gray-600 dark:text-white">Select a symbol above to view recent bar data.</span>
              </div>
            )}
          </>
        ) : (
          <div className="w-full h-full flex flex-col mb-4 justify-center items-center">
            {/* No Active Connection Warning */}
            <span className="text-xl text-gray-800 dark:text-white font-semibold">No Market Data Connection</span>
            <span className="text-md text-gray-600 dark:text-white">Unable to load bars.</span>
          </div>
        )}
        
      </div>
    </div>
  );
}

export default Holdings;
