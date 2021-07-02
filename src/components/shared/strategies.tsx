import React from 'react';
import { useRecoilState } from 'recoil';

import { TickState } from '@utils/models';
import { selectedStategyIndex } from '@state';
import StrategyCard from '@components/cards/StrategyCard';
import { KoiState } from '@types';


export interface StrategiesProps { state: KoiState, ticks: TickState, width: '4/12' | '8/12' };
const Strategies = ({ state, ticks, width = '8/12' }: StrategiesProps) => {
  const [selectedIndex, setSelectedIndex] = useRecoilState(selectedStategyIndex);

  return (
    <div className={`px-10 lg:px-4 mx-auto mb-6 w-full lg:w-${width}`}>
      <div className={`grid gap-4 grid-cols-2 ${width === '4/12' && 'lg:grid-cols-1'}`}>

        {state.strategies.length > 0 && state.strategies.map((strategy, i) => (
          <div className={`w-full strategy cursor-default ${i === selectedIndex ? 'selected' : ''}`} onClick={() => setSelectedIndex(i)}>
            <StrategyCard strategy={strategy} ticks={ticks} />
          </div>
        ))}

        {state.strategies.length === 0 && (
          <div>
            <h4>No Strategies Available</h4>
          </div>
        )}
      </div>
    </div>
  );
};

export default Strategies;
