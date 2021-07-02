import DatePicker from 'react-date-picker';
import Select from 'react-select';
import { useState } from 'react';


interface ConfigField {
  display: string;

}

interface Config {
  title: string;
  fields: ConfigField[];
}


export interface ConfigCardProps { mode: 'backtest' | 'analysis' };
const ConfigCard = ({ mode }: ConfigCardProps) => {

  const [visible, setVisible] = useState(true);
  const [useDateRange, setUseDateRange] = useState(false);
  const [useCache, setUseCache] = useState(true);
  const [endDate, setEndDate] = useState(new Date());

  const config: Config = (mode === 'analysis') ?
    { title: 'Analysis', fields: [ { display: '' } ] }
    : { title: 'Backtest', fields: [] }

  // Analysis config params
  const sequenceOptions = [...Array(100).keys()].slice(1).map(val => ({ value: val, label: `${val}` }));
  const windowOptions = [1, 2, 3].map(val => ({ value: val, label: `${val}` }));
  const extremesOptions = (
    [...Array(10).keys()].slice(1).map(val => val * 10).map(val => ({ value: val, label: `${val}` }))
  );


  // Backtest config params






  return (
    <div className="relative mb-6 flex-grow dark:text-white flex flex-col divide-y min-w-0 break-words bg-white dark:bg-off-black rounded shadow-lg border-2">
      <div className="flex flex-row items-center transition justify-between cursor-pointer p-4" onClick={() => setVisible(!visible)}>
        <h4 className="font-semibold">
          {config.title} Config
        </h4>
        <i className={`fas fa-wrench`} />
      </div>

      {visible && (
        <div className="flex flex-col w-full justify-center items-center px-4">
          <form className="w-full divide-y-2">

            {mode === 'analysis' && (
              <>
                {/* Timespan Configs */}
                <div className="pb-4">
                  <span className="text-xs uppercase text-gray-400">Timespans</span>

                  <div className="flex flex-col px-6 text-gray-700">

                    {/* Cache/custom date checkboxes  */}
                    <div className="flex flex-row space-x-6 mb-4 mt-2">
                      <label className="inline-flex items-center cursor-pointer">
                        <input onChange={() => setUseDateRange(!useDateRange)} id="customDateRange" type="checkbox" className="form-checkbox text-gray-800 ml-1 w-5 h-5 ease-linear transition-all duration-150" />
                        <span className="ml-2 text-sm font-light">
                          Custom Date Range
                        </span>
                      </label>

                      <label className="inline-flex items-center cursor-pointer">
                        <input onChange={() => setUseCache(!useCache)} id="useCache" type="checkbox" className="form-checkbox text-gray-800 ml-1 w-5 h-5 ease-linear transition-all duration-150" />
                        <span className="ml-2 text-sm font-light">
                          Use Cache
                        </span>
                      </label>
                    </div>

                    <div className="text-gray-800 flex flex-row items-center space-x-4">
                        <span>Analyze Duration</span>

                        <div className="mt-1 relative rounded-md shadow-sm">
                          <input  type="text" name="symbol" id="symbol" className="focus:ring-indigo-500 focus:border-indigo-500 block w-full pl-7 pr-12 sm:text-sm border-gray-300 rounded-md" placeholder="7" />
                          <div className="absolute inset-y-0 right-0 flex items-center">
                            <label htmlFor="analyze_duration" className="sr-only">Duration</label>
                            <select id="analyze_duration" name="analyze_duration" className="focus:ring-indigo-500 focus:border-indigo-500 h-full py-0 pl-2 pr-7 border-transparent bg-transparent text-gray-500 sm:text-sm rounded-md">
                              <option>Days</option>
                              <option>Months</option>
                              <option>Years</option>
                            </select>
                          </div>
                        </div>
                      </div>

                    {useDateRange && (
                      <div className="flex flex-row">

                        <div className="flex flex-col">
                          <span>End Date</span>
                          <DatePicker onChange={setEndDate as any} value={endDate} />
                        </div>

                      </div>
                    )}

                  </div>

                </div>




                  {/* Frame Configs */}
                  <div className="pb-4">
                    <span className="text-xs uppercase text-gray-400">Frame Sizing</span>

                    <div className="flex flex-col px-6 space-y-4">

                      {/* Sequences */}
                      <div className="my-2 flex flex-col space-y-1">
                        <div className="flex flex-row items-end justify-between">
                          <span>Sequence Sizes</span>
                        </div>

                        <Select
                          defaultValue={sequenceOptions.slice(0, 3)}
                          isMulti
                          name="Sequences"
                          options={sequenceOptions}
                          className="focus:ring-indigo-500 focus:border-indigo-500 h-full py-0 pl-2 pr-7 border-transparent bg-transparent text-gray-500 sm:text-sm rounded-md"
                          classNamePrefix="select"
                        />
                      </div>


                      {/* Windows */}
                      <div className="my-2 flex flex-col space-y-1">
                        <div className="flex flex-row items-end justify-between">
                          <span>Window Sizes</span>
                        </div>

                        <Select
                          defaultValue={windowOptions.slice(0, 1)}
                          isMulti
                          name="Windows"
                          options={windowOptions}
                          className="focus:ring-indigo-500 focus:border-indigo-500 h-full py-0 pl-2 pr-7 border-transparent bg-transparent text-gray-500 sm:text-sm rounded-md"
                          classNamePrefix="select"
                        />
                      </div>

                      

                      {/* Extremes */}
                      <div className="my-2 flex flex-col">
                        <div className="flex flex-row items-end justify-between">
                          <span>Extremes Sizes</span>
                        </div>

                        <Select
                          defaultValue={extremesOptions.slice(0, 3)}
                          isMulti
                          name="Extremes"
                          options={extremesOptions}
                          className="focus:ring-indigo-500 focus:border-indigo-500 h-full py-0 pl-2 pr-7 border-transparent bg-transparent text-gray-500 sm:text-sm rounded-md"
                          classNamePrefix="select"
                        />
                      </div>


                    </div>
                  </div>
                
                
                
                </>
              )}




              {mode === 'backtest' && (
                <>
                  {/* Timespan Configs */}
                  <div className="pb-4">
                    <span className="text-xs uppercase text-gray-400">Timespans</span>

                    <div className="flex flex-col px-6 text-gray-700">

                      {/* Cache/custom date checkboxes  */}
                      <div className="flex flex-row space-x-6 mb-4 mt-2">
                        <label className="inline-flex items-center cursor-pointer">
                          <input onChange={() => setUseDateRange(!useDateRange)} id="customDateRange" type="checkbox" className="form-checkbox text-gray-800 ml-1 w-5 h-5 ease-linear transition-all duration-150" />
                          <span className="ml-2 text-sm font-light">
                            Custom Date Range
                          </span>
                        </label>

                        <label className="inline-flex items-center cursor-pointer">
                          <input onChange={() => setUseCache(!useCache)} id="useCache" type="checkbox" className="form-checkbox text-gray-800 ml-1 w-5 h-5 ease-linear transition-all duration-150" />
                          <span className="ml-2 text-sm font-light">
                            Use Cache
                          </span>
                        </label>

                        <label className="inline-flex items-center cursor-pointer">
                          <input onChange={() => setUseCache(!useCache)} id="useCache" type="checkbox" className="form-checkbox text-gray-800 ml-1 w-5 h-5 ease-linear transition-all duration-150" />
                          <span className="ml-2 text-sm font-light">
                            Use Analysis
                          </span>
                        </label>

                      </div>

                      {useDateRange ? (
                        <div className="flex flex-row">

                          <div className="flex flex-col">
                            <span>End Date</span>
                            <DatePicker onChange={setEndDate as any} value={endDate} />
                          </div>

                        </div>

                      ) : (
                        <div className="text-gray-800 flex flex-row items-center space-x-4">
                          <span>Backtest Duration</span>

                          <div className="mt-1 relative rounded-md shadow-sm">
                            <input  type="text" name="symbol" id="symbol" className="focus:ring-indigo-500 focus:border-indigo-500 block w-full pl-7 pr-12 sm:text-sm border-gray-300 rounded-md" placeholder="7" />
                            <div className="absolute inset-y-0 right-0 flex items-center">
                              <label htmlFor="analyze_duration" className="sr-only">Duration</label>
                              <select id="analyze_duration" name="analyze_duration" className="focus:ring-indigo-500 focus:border-indigo-500 h-full py-0 pl-2 pr-7 border-transparent bg-transparent text-gray-500 sm:text-sm rounded-md">
                                <option>Days</option>
                                <option>Months</option>
                                <option>Years</option>
                              </select>
                            </div>
                          </div>
                        </div>
                      )}

                    </div>

                  </div>





                </>
              )}



              {/* Start Execution */}
              <div className="w-full flex justify-center py-4">
                <button
                  className="py-2 px-6 border border-indigo-500 text-indigo-600 hover:border-indigo-300 transition"
                  type="submit"
                >
                  Start {config.title}
                </button>
              </div>
        
            </form>
        </div>
      )}
    </div>
  );
}

export default ConfigCard;
