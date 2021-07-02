import { useRecoilState, useRecoilValue, useSetRecoilState } from 'recoil';
import {
  analysisState, getAnalysisState, getSelectedAnalysis, selectedAnalysisName,
  selectedAnalysisSymbol, selectedExtremesSize, getSelectedExtremesSizeData,
  selectedAnalysisWindow,
} from '@state';


const AnalysesCard = () => {
  const analyses = useRecoilValue(getAnalysisState);
  const setCurrentAnalysis = useSetRecoilState(selectedAnalysisName);
  const currentAnalysis = useRecoilValue(getSelectedAnalysis);
  const visibleExtremesData = useRecoilValue(getSelectedExtremesSizeData);
  const [currentAnalysisSymbol, setAnalysisSymbol] = useRecoilState(selectedAnalysisSymbol);
  const [currentExtremesSize, setExtremesSize] = useRecoilState(selectedExtremesSize);
  const [currentWindowSize, setWindowSize] = useRecoilState(selectedAnalysisWindow);


  const notableFieldClass = (classification: string, overall: number, positive: number, negative: number, std: number): string => {
    if (classification !== 'Positive' && classification !== 'Negative') return '';
    const isSignificant = (val: number, mult: number = 1, comp: number = overall) => Math.abs(Math.abs(val) - Math.abs(comp)) > (std * mult);

    // Either positive or negative value extremely significant
    if ((classification === 'Positive' && isSignificant(positive, 2)) || (classification === 'Negative' && isSignificant(negative, 2))) {
      return 'bg-yellow-400';
    }

    // Positive and negative values are > std dev away from each other
    if (isSignificant(positive, 1, negative)) return 'bg-purple-200';

    // Both positive and negative values are statiscally signifcant for the field
    if (isSignificant(positive) && isSignificant(negative)) return 'bg-red-200';

    // Either positive or negative value pretty significant
    if ((classification === 'Positive' && isSignificant(positive, 1.5)) || (classification === 'Negative' && isSignificant(negative, 1.5))) {
      return 'bg-green-200';
    }

    return '';
  }



  return (
    <div id="analyses" className="relative flex flex-col min-w-0 break-words bg-white dark:bg-off-black w-full mb-6 py-6 shadow-lg rounded">
      {/* Card Header */}
      <div className="rounded-t px-8 pb-5 border-0 mb-4">
        <div className="relative flex flex-row justify-between items-top">
          <div className="relative">
            <h3 className="font-semibold text-base text-gray-800 dark:text-white">
              Analyses
            </h3>
          </div>

          {/* Active Analyses Tabs */}
          <div className={`flex flex-col items-center w-full absolute ${Object.keys(analyses).length > 0 ? 'pb-8' : 'pb-1'}`}>
            {Object.keys(analyses).length > 0 && (
              <>
                <div className="ml-auto mr-auto text-xs underline mb-4 dark:text-white">Available Analyses</div>
                <div className="relative flex text-center space-x-3 text-sm leading-none font-bold text-gray-500">
                  {Object.keys(analyses).map((name) => (
                    <div className={`relative flex flex-col justify-center items-center`}>
                      <span onClick={() => setCurrentAnalysis(name)} className={`z-10 w-auto cursor-pointer flex text-black dark:text-gray-100`}>{name}</span>
                      {(currentAnalysis?.name === name) && <span className="z-0 w-full h-1 -mt-1 bg-green-200 dark:bg-green-700"></span>}
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>

          {/* Stage Indicator */}
          <div className="relative text-right text-gray-500 dark:text-white">
            {currentAnalysis && (
              <div className="flex flex-col w-full items-center">
                <span className="text-xs text-gray-500 mb-2">Current Stage</span>
                <div className="flex flex-row items-center space-x-2 text-xs uppercase">
                  <span className={`cursor-default ${(!(currentAnalysis.stage) || currentAnalysis.stage === 'inactive') ? 'font-semibold text-sm text-indigo-800 dark:text-indigo-600' : 'font-light'}`}>
                    Inactive
                  </span>
                  <span className={`cursor-default ${(currentAnalysis.stage === 'data') ? 'font-semibold text-sm text-indigo-800 dark:text-indigo-600' : 'font-light'}`}>
                    Fetching Data
                  </span>
                  <span className={`cursor-default ${currentAnalysis.stage === 'sequencing' ? 'font-semibold text-sm text-indigo-800 dark:text-indigo-600' : 'font-light'}`}>
                    Sequencing
                  </span>
                  <span className={`cursor-default ${currentAnalysis.stage === 'analysis' ? 'font-semibold text-sm text-indigo-800 dark:text-indigo-600' : 'font-light'}`}>
                    Analysis
                  </span>
                  <span className={`cursor-default ${currentAnalysis.stage === 'complete' ? 'font-semibold text-sm text-indigo-800 dark:text-indigo-600' : 'font-light'}`}>
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

          {Object.keys(analyses).length > 0 ? (
            <>
              {currentAnalysis && currentAnalysis.analysis_data ? (
                <>

                  {/* Positive vs Negative comparison table */}
                  <div className="flex w-full flex-col mt-4 p-4">
                    <span className="text-sm font-base mb-2 underline text-gray-500 dark:text-white"></span>


                    {/* Portfolio / Extremes Selection */}
                    <div className={`flex flex-row items-center space-x-10 justify-center ${Object.keys(analysisState).length > 0 ? 'pb-4' : 'pb-1'}`}>

                      {Object.keys(currentAnalysis.analysis_data).length > 0 ? (
                        <>
                          {/* Porfolios */}
                          <div className="flex flex-col items-center">
                            <div className="ml-auto mr-auto text-xs underline mb-4 dark:text-white">Portfolios</div>
                            <div className="relative flex text-center space-x-3 text-sm leading-none font-bold text-gray-500">
                              {Object.keys(currentAnalysis.analysis_data).map(symbol => (
                                <div className={`relative flex flex-col justify-center items-center`}>
                                  <span
                                    onClick={() => setAnalysisSymbol(currentAnalysisSymbol === symbol ? null : symbol)}
                                    className={`z-10 w-auto cursor-pointer flex text-black dark:text-gray-100`}
                                  >
                                    {symbol}
                                  </span>
                                  {currentAnalysisSymbol === symbol && <span className="z-0 w-full h-1 -mt-1 bg-green-200 dark:bg-green-800"></span>}
                                </div>
                              ))}
                            </div>
                          </div>

                          {/* Extremes */}
                          <div className="flex flex-col items-center">
                            <div className="ml-auto mr-auto text-xs underline mb-4 dark:text-white">
                              Extremes Count
                            </div>

                            <div className="relative flex text-center space-x-3 text-sm leading-none font-bold text-gray-500">
                              {(currentAnalysis.extremes_sizes || []).map(size => (
                                <div className={`relative flex flex-col justify-center items-center`}>
                                  <span
                                    onClick={() => setExtremesSize(currentExtremesSize === size ? null : size)}
                                    className={`z-10 w-auto cursor-pointer flex text-black dark:text-gray-100`}
                                  >
                                    {size}
                                  </span>
                                  {currentExtremesSize === size && <span className="z-0 w-full h-1 -mt-1 bg-green-200 dark:bg-green-800"></span>}
                                </div>
                              ))}
                            </div>
                          </div>

                          {/* Last States Window */}
                          <div className="flex flex-col items-center">
                            <div className="ml-auto mr-auto text-xs underline mb-4 dark:text-white">
                              History Window
                            </div>

                            <div className="relative flex text-center space-x-3 text-sm leading-none font-bold text-gray-500">
                              {(currentAnalysis.window_sizes || []).map(size => (
                                <div className={`relative flex flex-col justify-center items-center`}>
                                  <span
                                    onClick={() => setWindowSize(currentWindowSize === size ? null : size)}
                                    className={`z-10 w-auto cursor-pointer flex text-black dark:text-gray-100`}
                                  >
                                    {size}
                                  </span>
                                  {currentWindowSize === size && <span className="z-0 w-full h-1 -mt-1 bg-green-200 dark:bg-green-800"></span>}
                                </div>
                              ))}
                            </div>
                          </div>
                        </>
                      ) : (
                          <div className="flex flex-col justify-center items-center w-full p-8">
                            <span className="text-xl text-gray-800 dark:text-white font-semibold">No Data Available</span>
                            <span className="text-md text-gray-600 dark:text-white">Analysis has not yet formatted sharable data.</span>
                          </div>
                        )}

                    </div>



                    {visibleExtremesData && (
                      Object.entries(visibleExtremesData)
                        .map(([sequenceSize, { positive, negative, overall, std, positiveData, negativeData }], i) => (
                          <div className="flex flex-col">

                            {/* Size/Sequence Info & Indicator Key */}
                            <div className={`flex flex-row mb-3 items-end justify-between ${i === 0 ? 'mt-0 lg:-mt-2' : 'mt-6'}`}>

                              <div className="flex flex-row space-x-5 items-center">
                                <span className="font-base text-sm">Sequence Size: {sequenceSize}</span>
                                {positiveData && negativeData && (
                                  <div className="flex flex-col">
                                    <div className="text-xs font-light">
                                      <span className="font-base mr-3">Positive:</span>
                                      <span className="mr-2">Sum: {(positiveData.sum || 0).toFixed(2)}</span>
                                      <span>Average: {(positiveData.average || 0).toFixed(2)}</span>
                                    </div>

                                    <div className="text-xs font-light">
                                      <span className="font-base mr-3">Negative:</span>
                                      <span className="mr-2">Sum: {(negativeData.sum || 0).toFixed(2)}</span>
                                      <span>Average: {(negativeData.average || 0).toFixed(2)}</span>
                                    </div>
                                  </div>
                                )}
                              </div>

                              {/* Indicator */}
                              {i === 0 && (
                                <div className="flex flex-col items-end space-y-1">
                                  <div className="flex flex-row items-center justify-center space-x-3">
                                    <span className="font-light text-xs">field extremely sig.</span>
                                    <div className="w-6 h-6 rounded-xl bg-yellow-400" />
                                  </div>

                                  <div className="flex flex-row items-center justify-center space-x-3">
                                    <span className="font-light text-xs">pos vs neg sig.</span>
                                    <div className="w-6 h-6 rounded-xl bg-purple-200" />
                                  </div>

                                  <div className="flex flex-row items-center justify-center space-x-3">
                                    <span className="font-light text-xs">pos &amp; neg sig.</span>
                                    <div className="w-6 h-6 rounded-xl bg-red-200" />
                                  </div>

                                  <div className="flex flex-row items-center justify-center space-x-3">
                                    <span className="font-light text-xs">field sig.</span>
                                    <div className="w-6 h-6 rounded-xl bg-green-200" />
                                  </div>
                                </div>
                              )}
                            </div>


                            {/* Sequence Table */}
                            <div className="flex overflow-x-scroll">

                              <table className="table-auto text-blue-900 dark:text-gray-200 border-collapse">
                                <thead>
                                  <tr>
                                    <th className="px-6 bg-gray-50 dark:bg-gray-500 dark:text-black align-middle border border-solid border-blue-50 dark:border-gray-400 py-3 text-xs uppercase border-l-0 border-r-0 whitespace-no-wrap font-semibold text-left">
                                      Category
                                    </th>
                                    {Object.keys(positive).map(field => (
                                      // If positive[field]
                                      <th className="px-6 bg-gray-50 dark:bg-gray-500 dark:text-black align-middle border border-solid border-blue-50 dark:border-gray-400 py-3 text-xs uppercase border-l-0 border-r-0 whitespace-no-wrap font-semibold text-left">
                                        {field}
                                      </th>
                                    ))}
                                  </tr>
                                </thead>

                                <tbody>
                                  {Object.entries(({ 'Overall': overall, 'Positive': positive, 'Negative': negative, 'Std.Dev.': std }))
                                    .map(([classification, averages = {}], i) => (
                                      <tr
                                        className={`cursor-pointer transition ${i % 2 === 0 ? 'hover:bg-gray-100 dark:hover:bg-gray-900' : 'bg-blue-50 hover:bg-blue-200 dark:bg-gray-800 dark:hover:bg-gray-900'}`}
                                        onClick={() => { }}
                                      >
                                        <td className="border-t-0 px-6 align-middle border-l-0 border-r-0 text-xs whitespace-no-wrap p-4">
                                          {classification}
                                        </td>
                                        {Object.entries(averages).map(([field, value], i) => (
                                          <td
                                            className={`border-t-0 px-6 align-middle border-l-0 border-r-0 text-xs whitespace-no-wrap p-4 ${notableFieldClass(classification, overall[field], positive[field], negative[field], std[field])}`}
                                          >
                                            {!(value === undefined || value === null) ? (
                                              isNaN(value) ? value : (value as number).toFixed(4)
                                            ) : 'nan'}
                                          </td>
                                        ))}
                                      </tr>
                                    ))
                                  }
                                </tbody>
                              </table>

                            </div>
                          </div>
                        ))
                    )}

                  </div>


                </>
              ) : (
                  <div className="flex flex-col justify-center items-center w-full p-8">
                    <span className="text-xl text-gray-800 dark:text-white font-semibold">No Analysis Selected</span>
                    <span className="text-md text-gray-600 dark:text-white">Select an analysis above to view statistics</span>
                  </div>
                )}
            </>
          ) : (
              <div className="flex flex-col justify-center items-center w-full p-8">
                <span className="text-xl text-gray-800 dark:text-white font-semibold">No Analyses Available</span>
                <span className="text-md text-gray-600 dark:text-white">Start an analysis in the strategies panel above.</span>
              </div>
            )}

        </div>
      </div>
    </div>
  );
}

export default AnalysesCard;
