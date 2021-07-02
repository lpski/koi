import React from 'react';
import { useRecoilState } from 'recoil';

import { TickState } from '@utils/models';
import { selectedStategyIndex } from '@state';
import StrategyCard from '@components/cards/StrategyCard';
import { KoiState } from '@types';


export interface StrategiesProps { state: KoiState, ticks: TickState };
const Strategies = ({ state, ticks }: StrategiesProps) => {
  const [selectedIndex, setSelectedIndex] = useRecoilState(selectedStategyIndex);

  const toggledActiveState = (name: string, index: number, toActive: boolean) => {
    window.eel.set_strategy_active_state(name, toActive)
    state.strategies[index].active = toActive
  }

  return (
    <div className="px-10 lg:px-4 mx-auto min-w-1/4 lg:w-4/12 w-full">
      <div className="grid gap-4 grid-cols-2 lg:grid-cols-1">
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
