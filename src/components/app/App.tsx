import { RecoilRoot } from 'recoil';
import WithStateRefresh from '@hooks/withStateRefresh';
import Dash from '../pages/dash';
import './App.css';


// EEL Logic


// Point Eel web socket to the instance
export const eel = window.eel;
if (eel) eel.set_host('ws://localhost:8080')

// Web Logic

const App = () => (
  <RecoilRoot>
    <WithStateRefresh>
      <Dash />
    </WithStateRefresh>
  </RecoilRoot>
)
export default App;
