import { useRecoilState, useRecoilValue } from 'recoil';

import { getTickers, getTickStreamingActive, tickTab } from '@state';
import { TickState } from '@utils/models';
import { KoiState } from '@types';


export interface TickersProps { state: KoiState, ticks: TickState };
const Tickers = ({ state }: TickersProps) => {
  const [activeTab, setTickTab] = useRecoilState(tickTab);
  const tickers = useRecoilValue(getTickers);
  const streaming = useRecoilValue(getTickStreamingActive);

  const toggleStreaming = () => {
    if (window.eel) {
      if (activeTab === 'crypto') window.eel.toggle_crypto_streaming()
      else window.eel.toggle_market_streaming()
    }
  }

  return (
    <div className="tickers-card relative flex flex-col w-auto mx-0 lg:w-8/12 break-words bg-white dark:bg-off-black mb-6 shadow-lg rounded">
      <div className="rounded-t mb-0 px-4 py-3 border-0">
        <div className="flex flex-wrap items-end justify-between">
          <div className="relative px-4 flex items-end">
            <h3 className="font-semibold text-base text-gray-800 dark:text-white">
              Active Tickers
            </h3>

            {/* Ticker tabs */}
            <div className="relative flex text-center pl-4 space-x-2 text-sm leading-none text-gray-500">
              <div className={`relative flex px-1 flex-col justify-center items-center`}>
                <span onClick={() => setTickTab('market')} className={`z-10 w-auto cursor-pointer flex text-black dark:text-white`}>Stocks</span>
                {(activeTab === 'market') && <span className="z-0 w-8 h-1 -mt-1 bg-green-200 dark:bg-gren-800"></span>}
              </div>
              <div className={`relative flex px-1 flex-col justify-center items-center`}>
                <span onClick={() => setTickTab('crypto')} className={`z-10 w-auto cursor-pointer flex text-black dark:text-white`}>Crypto</span>
                {(activeTab === 'crypto') && <span className="z-0 w-8 h-1 -mt-1 bg-green-200 dark:bg-gren-800"></span>}
              </div>
            </div>
         </div>

          {/* Streaming Toggle */}
          <div onClick={toggleStreaming} className="relative flex cursor-pointer items-center justify-center px-4 text-right">
            {streaming ? (
              <>
                <svg className="text-green-700 w-4 h-4 mr-1" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className="text-gray-600">Active</span>
              </>
            ) : (
              <>
                <svg className="text-gray-700 dark:text-gray-300 w-4 h-4 mr-1" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className="text-gray-600 dark:text-gray-200">Paused</span>
              </>
            )}
            
          </div>
        </div>
      </div>
      
      <div className="block w-full overflow-x-auto">
        {/* Projects table */}
        <table className="items-center w-full bg-transparent border-collapse">
          <thead className="thead-light">
            <tr>
              {/* <th className="bg-gray-100 align-middle border border-solid border-gray-200 py-3 border-l-0 border-r-0 whitespace-no-wrap text-left w-8"></th> */}
              <th className="px-6 bg-gray-100 text-gray-600 align-middle border border-solid border-gray-200 dark:bg-transparent dark:border-white dark:text-white py-3 text-xs uppercase border-l-0 border-r-0 whitespace-no-wrap font-semibold text-left">
                Symbol
              </th>
              <th className="px-6 bg-gray-100 text-gray-600 align-middle border border-solid border-gray-200 dark:bg-transparent dark:border-white dark:text-white py-3 text-xs uppercase border-l-0 border-r-0 whitespace-no-wrap font-semibold text-left">
                Close
              </th>
              <th className="px-6 bg-gray-100 text-gray-600 align-middle border border-solid border-gray-200 dark:bg-transparent dark:border-white dark:text-white py-3 text-xs uppercase border-l-0 border-r-0 whitespace-no-wrap font-semibold text-left">
                Price
              </th>
              <th className="px-6 bg-gray-100 text-gray-600 align-middle border border-solid border-gray-200 dark:bg-transparent dark:border-white dark:text-white py-3 text-xs uppercase border-l-0 border-r-0 whitespace-no-wrap font-semibold text-left">
                Price Change
              </th>
              <th className="px-6 bg-gray-100 text-gray-600 align-middle border border-solid border-gray-200 dark:bg-transparent dark:border-white dark:text-white py-3 text-xs uppercase border-l-0 border-r-0 whitespace-no-wrap font-semibold text-left">
                Ask Vol
              </th>
              <th className="px-6 bg-gray-100 text-gray-600 align-middle border border-solid border-gray-200 dark:bg-transparent dark:border-white dark:text-white py-3 text-xs uppercase border-l-0 border-r-0 whitespace-no-wrap font-semibold text-left">
                Ask Vol Change
              </th>
              <th className="px-6 bg-gray-100 text-gray-600 align-middle border border-solid border-gray-200 dark:bg-transparent dark:border-white dark:text-white py-3 text-xs uppercase border-l-0 border-r-0 whitespace-no-wrap font-semibold text-left">
                Bid Vol
              </th>
              <th className="px-6 bg-gray-100 text-gray-600 align-middle border border-solid border-gray-200 dark:bg-transparent dark:border-white dark:text-white py-3 text-xs uppercase border-l-0 border-r-0 whitespace-no-wrap font-semibold text-left">
                Bid Vol Change
              </th>
            </tr>
          </thead>

          <tbody>
            {tickers.map(display => (
              <tr className="ticker-row">
                {/* <td className="items-center justify-center flex h-12">
                  <svg className="ticker-delete cursor-pointer hidden w-4 text-red-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </td> */}
                <th className="border-t-0 px-6 align-middle border-l-0 border-r-0 text-xs whitespace-no-wrap p-4 text-left">
                  {display.symbol}
                </th>

                {/* Close Price */}
                <td className="border-t-0 px-6 align-middle border-l-0 border-r-0 text-xs whitespace-no-wrap p-4">
                  {display.close}
                </td>

                {/* Ask Price */}
                <td className="border-t-0 px-6 align-middle border-l-0 border-r-0 text-xs whitespace-no-wrap p-4">
                  {display.ask}
                </td>
                <td className="border-t-0 px-6 align-middle border-l-0 border-r-0 text-xs whitespace-no-wrap p-4">
                  <div className="flex items-center">
                    <span className="mr-2">{display.askDiff}</span>
                    <i className={`fas ${display.askIcon} ${display.askColor} mr-4`} />
                  </div>
                </td>

                {/* Ask Volume */}
                <td className="border-t-0 px-6 align-middle border-l-0 border-r-0 text-xs whitespace-no-wrap p-4">
                  {display.askVol}
                </td>
                <td className="border-t-0 px-6 align-middle border-l-0 border-r-0 text-xs whitespace-no-wrap p-4">
                  <div className="flex items-center">
                    <span className="mr-2">{display.askVolDiff}</span>
                    <i className={`fas ${display.askVolIcon} ${display.askVolColor} mr-4`} />
                  </div>
                </td>

                {/* Bid Volume */}
                <td className="border-t-0 px-6 align-middle border-l-0 border-r-0 text-xs whitespace-no-wrap p-4">
                  {display.bidVol}
                </td>
                <td className="border-t-0 px-6 align-middle border-l-0 border-r-0 text-xs whitespace-no-wrap p-4">
                  <div className="flex items-center">
                    <span className="mr-2">{display.bidVolDiff}</span>
                    <i className={`fas ${display.bidVolIcon} ${display.bidVolColor} mr-4`} />
                  </div>
                </td>
              </tr>
            ))}

          </tbody>
        </table>
      </div>
  
      {(!tickers || tickers.length === 0) && (
        <div className='w-full min-h-8 mt-4 flex flex-col items-center justify-center'>
          <h3 className="font-semibold">No Ticks Available</h3>
          <span className="font-light">Start streaming to view tick data.</span>
        </div>
      )}
    </div>
  );
}

export default Tickers;
