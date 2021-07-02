import React from 'react';
import { useRecoilValue } from 'recoil';

import { getKoiState, getDarkModeEnabled, getActivePage } from '@state'
import AdminNavbar from '../navbar/Navbar';
import Trading from './trading';
import Backtest from './backtest';
import Analysis from './analysis';

const Dash = () => {
  const state = useRecoilValue(getKoiState);
  const dark = useRecoilValue(getDarkModeEnabled);
  const page = useRecoilValue(getActivePage);

  return (
    <div className={`relative min-h-screen ${dark ? 'dark' : ''} text-gray-700 dark:text-white`}>
      <div className={`relative pt-16 transition duration-150 ease-in-out bg-off-white dark:bg-off-gray min-h-screen`}>
        <AdminNavbar socketOpen={state.ib_connected} />


        {(state && state.strategies.length > 0) && (
          <div className="relative -mt-16 pt-16 px-4">
            {page === 'trade' && <Trading />}
            {page === 'backtest' && <Backtest />}
            {page === 'analysis' && <Analysis />}
          </div>
        )}


        {(!state || state.strategies.length === 0) && (
          <div className="flex -mt-16 pt-16 px-4 mx-auto w-screen h-screen items-center justify-center text-gray-700 dark:text-white">
            <h3>Initializing state...</h3>
          </div>
        )}
      </div>
    </div>
  );
}

export default Dash;
