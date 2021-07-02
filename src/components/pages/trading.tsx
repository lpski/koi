import React from 'react';
import { useRecoilValue } from 'recoil';

import { getSelectedStategy, getKoiState, getTickState } from '@state';
import Strategies from '@components/shared/strategies';
import Tickers from '@components/cards/Tickers';
import Holdings from '@components/cards/Holdings';

const Trading = () => {
  const state = useRecoilValue(getKoiState);
  const strategy = useRecoilValue(getSelectedStategy);
  const ticks = useRecoilValue(getTickState);

  return (
    <div className="flex flex-col w-full mt-6">

      <div className="px-10 flex flex-row flex-wrap items-start lg:px-4 mx-auto w-full">
        <Strategies ticks={ticks} state={state} width="4/12" />
        <Tickers ticks={ticks} state={state} />
      </div>

      <div className="px-10 lg:px-4 mx-auto w-full">
        <div className="flex flex-wrap">
          <div className="w-full xl:w-12/12 mb-12 xl:mb-0 px-4">
            {strategy && <Holdings strategy={strategy} />}
          </div>
        </div>
      </div>

    </div>
  );
}

export default Trading;
