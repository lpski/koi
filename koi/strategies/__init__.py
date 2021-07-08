from typing import Type, List
from koi.strategies.root import StrategyInterface
import os

def get_defined_strategies() -> List[Type[StrategyInterface]]:
    strategies = []
    for file in os.listdir('koi/strategies'):
        if file.endswith(".py") and not file.startswith('__init__') and not file.startswith('root'):

            module_name = os.path.join("koi/strategies", file)
            with open(module_name) as f:
                file_content = {}
                exec(f.read(), file_content)
                if 'Strategy' not in file_content:
                    print(f'Invalid Strategy Found: {module_name} | No "Strategy" class defined')
                else:
                    strategies.append(file_content['Strategy'])

    print(f'Found {len(strategies)} defined strategies')
    return strategies

