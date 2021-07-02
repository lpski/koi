import { useRecoilState, useRecoilValue, useSetRecoilState } from 'recoil';
import {
  getKoiState, selectedBacktestName, selectedBarsSymbol, barHistorySize,
  getSelectedBacktest, getBacktestsState, getBarsState, TransactionCategory, isTransactionPairList, getVisibleTransactions, transactionCategory, 
} from '@state';


const BacktestsCard = () => {
  const state = useRecoilValue(getKoiState);
  const backtests = useRecoilValue(getBacktestsState);
  const [currentBacktestName, setCurrentBacktest] = useRecoilState(selectedBacktestName);
  const currentBacktest = useRecoilValue(getSelectedBacktest);
  const barsState = useRecoilValue(getBarsState);
  const transactions = useRecoilValue(getVisibleTransactions);
  const setBarsSymbol = useSetRecoilState(selectedBarsSymbol);
  const setBarHistorySize = useSetRecoilState(barHistorySize);
  const [tradeCategory, setTradeCategory] = useRecoilState(transactionCategory);


  const transactionFields: { key: string, display: string }[] = [
    { key: 'symbol', display: 'Symbol' },
    { key: 'transaction_type', display: 'Trade Type' },
    { key: 'date', display: 'Date' },
    { key: 'strike', display: 'Price' },
    { key: 'quantity', display: 'Quantity' },
    { key: 'confidence', display: 'Confidence' },
    { key: 'tradePL', display: 'Trade P/l' },
    { key: 'totalPL', display: 'Total P/L' },
    { key: 'reason', display: 'Trade Reason' },
  ];

  const tradeCategories: { key: TransactionCategory, display: string }[] = [
    { key: 'all', display: 'All' },
    { key: 'buys', display: 'Buys' },
    { key: 'sells', display: 'Sells' },
    { key: 'good', display: 'Good Trades' },
    { key: 'bad', display: 'Bad Trades' },
  ];

  const viewStateForTransaction = (symbol: string, date: string, buyDate?: string) => {
    console.log(`viewStateForTransaction (${buyDate}, ${date})`)
    setBarsSymbol(symbol);

    if (buyDate) {
      // Expands/Contracts history to relevant range then highlights buy & sell row
      setBarHistorySize({ buy: buyDate, sell: date });
      setTimeout(() => {
        const sellRowId = symbol + '_' + date.replace(/[\:\/ ]/g, '_');
        const sellRow = document.querySelector(`.bars-table #${sellRowId}`);
        sellRow?.classList.add('bg-blue-100');
  
        const buyRowId = symbol + '_' + buyDate.replace(/[\:\/ ]/g, '_');
        const buyRow = document.querySelector(`.bars-table #${buyRowId}`);
        buyRow?.classList.add('bg-red-200');

        sellRow?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }, 400);
    } else {
      // Expands all bar history & highlights row for given date
      setBarHistorySize('full');
    
      setTimeout(() => {
        // Scroll to correct date
        const rowId = symbol + '_' + date.replace(/[\:\/ ]/g, '_');
        const row = document.querySelector(`.bars-table #${rowId}`);
        if (row) {
          row.classList.add('bg-blue-100');
          row.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }, 400);
    }
  }

  const lastPrice = (symbol: string): number | null => {
    if (barsState && barsState[symbol]) console.log(barsState[symbol].data.slice(0, 1))
    if (!barsState || !barsState[symbol] || barsState[symbol].data.length === 0) return null;
    const lastRow = barsState[symbol].data.slice(-1)[0];

    const closeIndex = barsState[symbol].columns.findIndex(c => c === 'close');
    return lastRow[closeIndex] as number;
  }


  return (
    <div id="backtests" className="relative flex flex-col min-w-0 break-words bg-white dark:bg-off-black w-full mb-6 py-6 shadow-lg rounded">

      {/* Card Header */}
      <div className="rounded-t px-8 pb-5 border-0 mb-4">
        <div className="relative flex flex-row justify-between items-top">
          <div className="relative">
            <h3 className="font-semibold text-base text-gray-800 dark:text-white">
              Backtests
            </h3>
          </div>

          {/* Active Analyses Tabs */}
          <div className={`flex flex-col items-center w-full absolute ${Object.keys(backtests).length > 0 ? 'pb-8' : 'pb-1'}`}>
            {Object.keys(state.strategies).length > 0 && (
              <>
                <div className="ml-auto mr-auto text-xs underline mb-4 dark:text-white">Available Backtests</div>
                <div className="relative flex text-center space-x-3 text-sm leading-none font-bold text-gray-500">
                  {state.strategies.map(({ name }) => (
                    <div className={`relative flex flex-col justify-center items-center`}>
                      <span onClick={() => setCurrentBacktest(name)} className={`z-10 w-auto cursor-pointer flex text-black dark:text-gray-100`}>{name}</span>
                      {(currentBacktestName === name) && <span className="z-0 w-full h-1 -mt-1 bg-green-200 dark:bg-green-700"></span>}
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>

          {/* Stage Indicator */}
          <div className="relative text-right text-gray-500 dark:text-white">
            {currentBacktest && (
              <div className="flex flex-col w-full items-center">
                <span className="text-xs text-gray-500 mb-2">Current Stage</span>
                <div className="flex flex-row items-center space-x-2 text-xs uppercase">
                  <span className={`cursor-default ${(!(currentBacktest.stage) || currentBacktest.stage === 'setup') ? 'font-semibold text-sm text-indigo-800 dark:text-indigo-600' : 'font-light'}`}>
                    Data + Analysis + Training
                  </span>
                  <span className={`cursor-default ${currentBacktest.stage === 'testing' ? 'font-semibold text-sm text-indigo-800 dark:text-indigo-600' : 'font-light'}`}>
                    Trading
                  </span>
                  <span className={`cursor-default ${currentBacktest.stage === 'complete' ? 'font-semibold text-sm text-indigo-800 dark:text-indigo-600' : 'font-light'}`}>
                    Complete
                  </span>
                </div>
              </div>
            )}
          </div>

        </div>
      </div>



      {/* Card Content */}
      <div className="block w-full overflow-x-auto px-4 pb-3">
        <div className="relative flex flex-col w-full">

          {Object.keys(backtests).length > 0 ? (
            <>
              {currentBacktest ? (
                <>

                  <div className="flex w-full flex-col mt-4 p-4">

                      {/* Stats */}
                    <div className="flex flex-row flex-wrap justify-around w-full">

                      {/* Performance */}
                      <div className="flex flex-col px-4 max-w-1/2">
                        <span className="text-sm text-center font-base text-gray-500 dark:text-white underline mb-2">Performance</span>

                        {/* Observation/purchase counts */}
                        <div className="counts flex flex-row mb-4">
                          <div className="flex flex-col text-gray-700 dark:text-white mr-4 items-center">
                            <span className="font-semibold">
                              {currentBacktest.observations}
                              <span className="font-light text-xs"> /{Math.ceil(currentBacktest.test_size)}</span>
                            </span>
                            <span className="font-light">Observations</span>
                          </div>
                          <div className="flex flex-col text-gray-700 dark:text-white items-center">
                            <span className="font-semibold">{currentBacktest.total_buys}</span>
                            <span className="font-light">Purchases</span>
                          </div>
                        </div>


                        {/* Strategy Performance */}
                        <div className="flex flex-col justify-center items-center mb-4 text-gray-700 dark:text-white">
                          <span className="font-bold">Strategy</span>

                          <div className="flex flex-row flex-wrap space-x-6">
                            <div className="flex flex-col items-center">
                              <span className={`font-semibold ${currentBacktest.strategy_profit > 0 ? 'text-green-700' : 'text-red-700'}`}>
                                ${currentBacktest.strategy_profit.toFixed(3)}
                              </span>
                              <span className="font-light text-sm">P/L</span>
                            </div>
                            <div className="flex flex-col items-center">
                              <span className={`font-semibold ${currentBacktest.strategy_profit > 0 ? 'text-green-700' : 'text-red-700'}`}>
                                {(currentBacktest.strategy_profit / currentBacktest.initial_capital * 100).toFixed(2)}%
                              </span>
                              <span className="font-light text-sm">P/L %</span>
                            </div>
                          </div>
                        </div>
                        

                        {/* Hold Performance */}
                        <div className="flex flex-col justify-center items-center text-gray-700 dark:text-white">
                          <span className="font-bold">Hold</span>

                          <div className="flex flex-row flex-wrap space-x-6">
                            <div className="flex flex-col items-center">
                              <span className={`font-semibold ${currentBacktest.hold_profit > 0 ? 'text-green-700' : 'text-red-700'}`}>
                                ${currentBacktest.hold_profit.toFixed(3)}
                              </span>
                              <span className="font-light text-sm">P/L</span>
                            </div>
                            <div className="flex flex-col items-center">
                              <span className={`font-semibold ${currentBacktest.hold_profit > 0 ? 'text-green-700' : 'text-red-700'}`}>
                              {(currentBacktest.hold_profit / currentBacktest.initial_capital * 100).toFixed(2)}%
                              </span>
                              <span className="font-light text-sm">P/L %</span>
                            </div>
                          </div>
                        </div>

                      </div>


                      {/* Notable Trades */}
                      <div className="flex flex-col px-4">
                        <span className="text-sm text-center font-base mb-2 underline text-gray-500 dark:text-off-white">Notable Trades</span>
                        
                        <div className="grid grid-cols-1 gap-2 dark:text-white">
                          {currentBacktest.largest_profit && (
                            <div className="flex flex-col border p-2">
                              <div className="flex flex-row divide-x-2 items-baseline space-x-2">
                                <span className="font-light text-sm mb-1">Best Overall</span>
                                <span className="font-light text-xs mb-1 pl-2">Trade with the highest P/L</span>
                              </div>

                              <div className="grid grid-cols-2 gap-2 w-full">
                                <div className="flex flex-col justify-center items-center">
                                  <span className="font-semibold">{currentBacktest.largest_profit.symbol}</span>
                                  <span className="font-light text-sm">Symbol</span>
                                </div>
                                <div className="flex flex-col justify-center items-center">
                                  <span className="font-semibold text-green-700">${currentBacktest.largest_profit.pl.toFixed(3)}</span>
                                  <span className="font-light text-sm">Profit/Loss</span>
                                </div>
                                <div className="flex flex-col justify-center items-center">
                                  <span className="font-semibold">{currentBacktest.largest_profit.purchase_date}</span>
                                  <span className="font-light text-sm">Purchase Date</span>
                                </div>
                                <div className="flex flex-col justify-center items-center">
                                  <span className="font-semibold">{currentBacktest.largest_profit.sell_date}</span>
                                  <span className="font-light text-sm">Sell Date</span>
                                </div>
                              </div>
                            </div>
                          )}

                          {currentBacktest.largest_loss && (
                            <div className="flex flex-col border p-2">
                              <div className="flex flex-row divide-x-2 items-baseline space-x-2">
                                <span className="font-light text-sm mb-1">Worst Overall</span>
                                <span className="font-light text-xs mb-1 pl-2">Trade with the most negative P/L</span>
                              </div>

                              <div className="grid grid-cols-2 gap-2 w-full">
                                <div className="flex flex-col justify-center items-center">
                                  <span className="font-semibold">{currentBacktest.largest_loss.symbol}</span>
                                  <span className="font-light text-sm">Symbol</span>
                                </div>
                                <div className="flex flex-col justify-center items-center">
                                  <span className="font-semibold text-red-700">${currentBacktest.largest_loss.pl.toFixed(3)}</span>
                                  <span className="font-light text-sm">Profit/Loss</span>
                                </div>
                                <div className="flex flex-col justify-center items-center">
                                  <span className="font-semibold">{currentBacktest.largest_loss.purchase_date}</span>
                                  <span className="font-light text-sm">Purchase Date</span>
                                </div>
                                <div className="flex flex-col justify-center items-center">
                                  <span className="font-semibold">{currentBacktest.largest_loss.sell_date}</span>
                                  <span className="font-light text-sm">Sell Date</span>
                                </div>
                              </div>
                            </div>
                          )}

                          {currentBacktest.largest_missed_profit && (
                            <div className="flex flex-col border p-2">
                              <div className="flex flex-row divide-x-2 items-baseline space-x-2">
                                <span className="font-light text-sm mb-1">Worst Early Sell</span>
                                <span className="font-light text-xs mb-1 pl-2">Largest missed profit (window=1)</span>
                              </div>

                              <div className="grid grid-cols-2 gap-2 w-full">
                                <div className="flex flex-col justify-center items-center">
                                  <span className="font-semibold">{currentBacktest.largest_missed_profit.symbol}</span>
                                  <span className="font-light text-sm">Symbol</span>
                                </div>
                                <div className="flex flex-col justify-center items-center">
                                  <span className="font-semibold">${currentBacktest.largest_missed_profit.pl.toFixed(3)}</span>
                                  <span className="font-light text-sm">Profit/Loss</span>
                                </div>
                                <div className="flex flex-col justify-center items-center">
                                  <span className="font-semibold">{currentBacktest.largest_missed_profit.purchase_date.slice(-8)}</span>
                                  <span className="font-light text-sm">Purchase Date</span>
                                </div>
                                <div className="flex flex-col justify-center items-center">
                                  <span className="font-semibold">{currentBacktest.largest_missed_profit.sell_date.slice(-8)}</span>
                                  <span className="font-light text-sm">Sell Date</span>
                                </div>
                              </div>
                            </div>
                          )}

                        </div>
                      </div>


                      {/* Accuracy */}
                      <div className="flex flex-col px-4">
                        <span className="text-sm text-center font-base mb-2 underline text-gray-500 dark:text-off-white">Accuracy</span>

                        {/* Buy Decision Accuracy */}
                        <div className="counts flex flex-row mb-4 text-gray-700 dark:text-white">
                          <div className="flex flex-col mr-4 items-center">
                            <span className="font-semibold">
                              {currentBacktest.bad_buys.length} ({(currentBacktest.bad_buys.length / currentBacktest.total_buys * 100).toFixed(2)}%)
                            </span>
                            <span className="font-light">Bad Buys (n=1)</span>
                          </div>
                          <div className="flex flex-col items-center">
                            <span className="font-semibold">nan</span>
                            <span className="font-light">Bad Buys (n=2)</span>
                          </div>
                        </div>


                        {/* Sell Decision Accuracy */}
                        <div className="counts flex flex-row mb-4 text-gray-700 dark:text-white">
                          <div className="flex flex-col mr-4 items-center">
                            <span className="font-semibold">
                              {currentBacktest.bad_sells.length} ({(currentBacktest.bad_sells.length / currentBacktest.total_sells * 100).toFixed(2)}%)
                            </span>
                            <span className="font-light">Bad Sells (n=1)</span>
                          </div>
                          <div className="flex flex-col items-center">
                            <span className="font-semibold">nan</span>
                            <span className="font-light">Bad Sells (n=2)</span>
                          </div>
                        </div>


                        {/* Avg Confidences Accuracy */}
                        {/* <div className="counts flex flex-row mb-4 text-gray-700 dark:text-white">
                          <div className="flex flex-col mr-4 items-center">
                            <span className="font-semibold">
                              {(currentBacktest.good_buys.map(gb => gb.confidence).reduce((a, b) => a + b)) / currentBacktest.good_buys.length}
                            </span>
                            <span className="font-light">Avg. Good Buy Conf.</span>
                          </div>
                          <div className="flex flex-col items-center">
                            <span className="font-semibold">
                              {(currentBacktest.bad_buys.map(bb => bb.confidence).reduce((a, b) => a + b)) / currentBacktest.bad_buys.length}
                            </span>
                            <span className="font-light">Avg. Bad Buy Conf.</span>
                          </div>
                        </div> */}

                          
                      </div>


                      {/* Portfolios */}
                      <div className="flex flex-col px-4">
                        <span className="text-sm font-base text-center text-gray-500 dark:text-gray-200 underline mb-2 mt-4">Portfolios</span>
                        {/* <div className="counts grid grid-cols-1 gap-6 mb-4 text-gray-700 dark:text-white"> */}
                        <div className="counts flex flex-row flex-wrap space-x-4 mb-4 text-gray-700 dark:text-white">
                          {(currentBacktest.portfolios || [])
                            .map(p => ({ price: lastPrice(p.symbol), portfolio: p, stats: currentBacktest.prediction_stats && currentBacktest.prediction_stats[p.symbol] }))
                            .map(({ price, stats, portfolio: { symbol, purchases, gross_profit, hold_start_price, hold_start_shares }}) => (
                              <div className="flex flex-col justify-center items-center mb-4">
                                <span className="font-bold">{symbol}</span>
                                <span className="font-base text-xs">
                                  Start Price: ${hold_start_price}
                                  <span className="px-4" />
                                  End Price: ${price || ''}
                                </span>
                                <span className="font-base text-xs">
                                  Hold Shares: {(hold_start_shares || 0).toFixed(2)}
                                  <span className="px-4" />
                                  Hold Gain: ${((hold_start_shares * ((price || hold_start_price) - hold_start_price)) || 0).toFixed(2)}
                                </span>

                                {/* Profits */}
                                <div className="flex flex-row flex-wrap space-x-6 mt-2">
                                  <div className="flex flex-col  items-center">
                                    <span className="font-semibold">{purchases}</span>
                                    <span className="font-light">Buys</span>
                                  </div>
                                  <div className="flex flex-col items-center">
                                    <span className={`font-semibold ${gross_profit > 0 ?'text-green-700' : 'text-red-700'}`}>
                                      ${gross_profit.toFixed(2)}
                                      {/* ${gross_profit.toFixed(2)} ({((gross_profit / (hold_start_shares * ((price || hold_start_price) - hold_start_price))) - 1).toFixed(2)}% vs. hold) */}
                                    </span>
                                    <span className="font-light">Strategy Profit</span>
                                  </div>
                                  {price && (
                                    <div className="flex flex-col items-center">
                                      <span className={`font-semibold ${(price - hold_start_price) > 0 ?'text-green-700' : 'text-red-700'}`}>
                                        ${((price - hold_start_price)).toFixed(2)} ({((price - hold_start_price) / hold_start_price * 100).toFixed(2)}%)
                                      </span>
                                      <span className="font-light">Change</span>
                                    </div>
                                  )}
                                </div>

                                {/* Prediction Stats */}
                                <div className="grid grid-cols-2 gap-4 mt-4">
                                  {stats && Object.entries(stats).map(([field, stat]) => (
                                    <div className="flex flex-col justify-center items-center">
                                      <span className="font-semibold">
                                        {stat.correct}
                                        <span className="text-xs font-light"> /{stat.total}</span>
                                      </span>
                                      <span className="text-xs font-light"> ({stat.incorrect} incorrect | {stat.unsure} unsure)</span>
                                      <span className="font-light text-sm">{field.split(' ')[0]}</span>
                                    </div>
                                  ))}
                                </div>

                              </div>
                            ))
                          }
                        </div>
                      </div>

                    </div>





                    {/* Transactions */}
                    <div className="flex w-full flex-col mt-4 p-4">
                      <span className="text-sm font-base mb-2 underline text-gray-500 dark:text-white"></span>

                      {/* Transaction Section Tabs */}
                      <div className={`flex flex-col items-center w-full ${Object.keys(backtests).length > 0 ? 'pb-4' : 'pb-1'}`}>
                        <div className="ml-auto mr-auto text-xs underline mb-4 dark:text-white">Transactions</div>
                        <div className="relative flex text-center space-x-3 text-sm leading-none font-bold text-gray-500">

                          {tradeCategories.map(({ key, display}) => (
                            <div className={`relative flex flex-col justify-center items-center`}>
                              <span onClick={() => setTradeCategory(key)} className={`z-10 w-auto cursor-pointer flex text-black dark:text-gray-100`}>{display}</span>
                              {tradeCategory === key && <span className="z-0 w-full h-1 -mt-1 bg-green-200 dark:bg-green-800"></span>}
                            </div>
                          ))}
                        </div>
                      </div>

                      <table className="table-auto text-blue-900 dark:text-gray-200 border-collapse">
                        <thead>
                          <tr>
                            {transactionFields.map(({ display }) => (
                              <th className="px-6 bg-gray-50 dark:bg-gray-500 dark:text-black align-middle border border-solid border-blue-50 dark:border-gray-400 py-3 text-xs uppercase border-l-0 border-r-0 whitespace-no-wrap font-semibold text-left">{display}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {isTransactionPairList(transactions) ? (
                            transactions.map(({ buy, sell }, i) => (
                              <>
                                <tr
                                  className={`cursor-pointer transition ${i % 2 === 0 ? 'hover:bg-gray-100 dark:hover:bg-gray-900' : 'bg-blue-50 hover:bg-blue-200 dark:bg-gray-800 dark:hover:bg-gray-900'}`}
                                  onClick={() => viewStateForTransaction(buy.symbol, sell.date, buy.date)}
                                >
                                  {transactionFields.map(({ key, display }) => (
                                    <td className="border-t-0 px-6 align-middle border-l-0 border-r-0 text-xs whitespace-no-wrap p-4">
                                      <div className='tooltip relative'>
                                        {!(buy[key] === undefined || buy[key] === null)  ? (
                                          isNaN(buy[key]) ? buy[key] : (buy[key] as number).toFixed(2)
                                        ) : 'nan'}
                                        <span className="tooltip-text bg-yellow-400 border rounded border-orange-500 text-orange-700 -mt-10 left-0">{display}</span>
                                      </div>
                                    </td>
                                  ))}
                                </tr>
                                <tr
                                  className={`cursor-pointer transition ${i % 2 === 0 ? 'hover:bg-gray-100 dark:hover:bg-gray-900' : 'bg-blue-50 hover:bg-blue-200 dark:bg-gray-800 dark:hover:bg-gray-900'}`}
                                  onClick={() => viewStateForTransaction(sell.symbol, sell.date, buy.date)}
                                >
                                  {transactionFields.map(({ key, display }) => (
                                    <td className="border-t-0 px-6 align-middle border-l-0 border-r-0 text-xs whitespace-no-wrap p-4">
                                      <div className='tooltip relative'>
                                        {!(sell[key] === undefined || sell[key] === null)  ? (
                                          isNaN(sell[key]) ? sell[key] : (sell[key] as number).toFixed(2)
                                        ) : 'nan'}
                                        <span className="tooltip-text bg-yellow-400 border rounded border-orange-500 text-orange-700 -mt-10 left-0">{display}</span>
                                      </div>
                                    </td>
                                  ))}
                                </tr>
                              </>
                            ))
                          ) : (
                            transactions.map((trade, i) => (
                              <tr
                                className={`cursor-pointer transition ${i % 2 === 0 ? 'hover:bg-gray-100 dark:hover:bg-gray-900' : 'bg-blue-50 hover:bg-blue-200 dark:bg-gray-800 dark:hover:bg-gray-900'}`}
                                onClick={() => viewStateForTransaction(trade.symbol, trade.date)}
                              >
                                {transactionFields.map(({ key, display }) => (
                                  <td className="border-t-0 px-6 align-middle border-l-0 border-r-0 text-xs whitespace-no-wrap p-4">
                                    <div className='tooltip relative'>
                                      {!(trade[key] === undefined || trade[key] === null)  ? (
                                        isNaN(trade[key]) ? trade[key] : (trade[key] as number).toFixed(2)
                                      ) : 'nan'}
                                      <span className="tooltip-text bg-yellow-400 border rounded border-orange-500 text-orange-700 -mt-10 left-0">{display}</span>
                                    </div>
                                  </td>
                                ))}
                              </tr>
                            ))
                          )}
                        </tbody>
                      </table>
                    </div>




                  </div>


                </>
              ) : (
                  <div className="flex flex-col justify-center items-center w-full p-8">
                    <span className="text-xl text-gray-800 dark:text-white font-semibold">No Backtest Selected</span>
                    <span className="text-md text-gray-600 dark:text-white">Select a backtest above to view performance</span>
                  </div>
                )}
            </>
          ) : (
              <div className="flex flex-col justify-center items-center w-full p-8">
                <span className="text-xl text-gray-800 dark:text-white font-semibold">No Backtests Available</span>
                <span className="text-md text-gray-600 dark:text-white">Start a backtest in the strategies panel above.</span>
              </div>
            )}

        </div>
      </div>
    </div>
  );
}

export default BacktestsCard;
