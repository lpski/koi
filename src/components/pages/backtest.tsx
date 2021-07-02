import React from 'react';
import { useRecoilValue } from 'recoil';

import Strategies from '@components/shared/strategies';
import ConfigCard from '@components/cards/Config';
import BacktestsCard from '@components/cards/BacktestsCard';
import { getKoiState, getTickState, getBacktestsState, getSelectedStategy } from '@state';
import Holdings from '@components/cards/Holdings';

const Backtest = () => {
  const state = useRecoilValue(getKoiState);
  const strategy = useRecoilValue(getSelectedStategy);
  const ticks = useRecoilValue(getTickState);
  const backtests = useRecoilValue(getBacktestsState);

  return (
    <div className="flex flex-col w-full mt-6">

      <div className="px-10 flex-col flex-wrap items-center lg:items-start lg:flex-row flex lg:px-4 mx-auto w-full">
        <Strategies ticks={ticks} state={state} width="8/12" />
        <ConfigCard mode={'backtest'} />
        {Object.keys(backtests).length > 0 && <BacktestsCard />}
        {Object.keys(backtests).length > 0 && strategy && <Holdings strategy={strategy} />}

      </div>

    </div>
  );
}

export default Backtest;
