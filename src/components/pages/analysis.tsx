import React from 'react';
import { useRecoilValue } from 'recoil';

import Strategies from '@components/shared/strategies';
import ConfigCard from '@components/cards/Config';
import { getAnalysisState, getKoiState, getTickState } from '@state';
import AnalysesCard from '@components/cards/AnalysesCard';

const Analysis = () => {
  const state = useRecoilValue(getKoiState);
  const ticks = useRecoilValue(getTickState);
  const analyses = useRecoilValue(getAnalysisState);

  return (
    <div className="flex flex-col w-full mt-6">

      <div className="px-10 flex-col flex-wrap items-center lg:items-start lg:flex-row flex lg:px-4 mx-auto w-full">
        <Strategies ticks={ticks} state={state} width="8/12" />
        <ConfigCard mode={'analysis'} />
        {Object.keys(analyses).length > 0 && <AnalysesCard />}
      </div>

    </div>
  );
}

export default Analysis;
