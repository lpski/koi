import { useRecoilState } from 'recoil';
import { darkModeEnabled, activePage } from '@state';

export interface NavbarProps { socketOpen: boolean, socketError?: string }
const Navbar = ({ socketOpen }: NavbarProps) => {
  const [useDarkMode, setUseDarkMode] = useRecoilState(darkModeEnabled);
  const [currentPage, setCurrentPage] = useRecoilState(activePage);

  return (
    <>
      {/* Navbar */}
      <nav className="top-0 fixed left-0 w-full z-10 bg-off-white dark:bg-off-gray opacity-80 md:flex-row md:flex-no-wrap md:justify-start flex items-center p-4">
        <div className="w-full mx-autp items-center flex justify-between md:flex-no-wrap flex-wrap md:px-10 px-4">
          {/* Brand */}
          <a
            className="text-white text-sm uppercase inline-block font-semibold"
            href="#"
            onClick={(e) => e.preventDefault()}
          >
            <svg className="h-8 w-9 text-black dark:text-off-white hover:animate-spin" xmlns="http://www.w3.org/2000/svg" height="512pt" version="1.1" viewBox="0 0 512.0015 512" width="512pt">
              <g id="surface1" className="fill-current">
                <path d="M 175.667969 321.332031 C 169.84375 321.332031 164.195312 320.558594 158.816406 319.117188 L 158.816406 263.21875 C 158.816406 254.9375 152.101562 248.21875 143.816406 248.21875 C 135.53125 248.21875 128.816406 254.9375 128.816406 263.21875 L 128.816406 301.472656 C 117.390625 289.699219 110.335938 273.664062 110.335938 256 C 110.335938 221.976562 136.480469 193.957031 169.734375 190.949219 L 189.730469 210.945312 C 192.660156 213.871094 196.5 215.335938 200.335938 215.335938 C 204.175781 215.335938 208.015625 213.871094 210.945312 210.945312 C 216.800781 205.085938 216.800781 195.589844 210.945312 189.730469 L 196.878906 175.667969 L 210.945312 161.601562 C 216.800781 155.746094 216.800781 146.246094 210.945312 140.390625 C 205.085938 134.53125 195.589844 134.53125 189.730469 140.390625 L 169.328125 160.792969 C 75.390625 164.144531 0 241.59375 0 336.332031 C 0 379.375 15.570312 418.847656 41.359375 449.425781 L 4.394531 486.394531 C -1.464844 492.25 -1.464844 501.75 4.394531 507.609375 C 7.324219 510.535156 11.160156 512 15 512 C 18.839844 512 22.679688 510.535156 25.605469 507.605469 L 62.574219 470.636719 C 93.15625 496.429688 132.625 512 175.667969 512 C 228.234375 512 271 469.234375 271 416.667969 C 271 364.101562 228.234375 321.332031 175.667969 321.332031 Z M 175.667969 482 C 95.347656 482 30 416.65625 30 336.332031 C 30 289.316406 52.398438 247.425781 87.078125 220.773438 C 82.726562 231.675781 80.335938 243.566406 80.335938 256 C 80.335938 294.910156 103.769531 328.445312 137.265625 343.246094 C 137.640625 343.429688 138.019531 343.597656 138.410156 343.75 C 149.863281 348.628906 162.453125 351.332031 175.667969 351.332031 C 211.691406 351.332031 241 380.640625 241 416.664062 C 241 452.691406 211.691406 482 175.667969 482 Z M 175.667969 482" />
                <path d="M 175.667969 401.667969 C 171.71875 401.667969 167.847656 403.269531 165.058594 406.058594 C 162.269531 408.847656 160.667969 412.71875 160.667969 416.667969 C 160.667969 420.617188 162.269531 424.488281 165.058594 427.277344 C 167.847656 430.066406 171.71875 431.667969 175.667969 431.667969 C 179.617188 431.667969 183.488281 430.066406 186.277344 427.277344 C 189.066406 424.488281 190.667969 420.617188 190.667969 416.667969 C 190.667969 412.71875 189.066406 408.847656 186.277344 406.058594 C 183.480469 403.269531 179.617188 401.667969 175.667969 401.667969 Z M 175.667969 401.667969 " />
                <path d="M 470.640625 62.574219 L 507.609375 25.609375 C 513.464844 19.75 513.464844 10.253906 507.609375 4.394531 C 501.75 -1.464844 492.253906 -1.464844 486.394531 4.394531 L 449.425781 41.363281 C 418.84375 15.570312 379.375 0 336.335938 0 C 283.765625 0 241 42.769531 241 95.332031 C 241 147.898438 283.765625 190.667969 336.335938 190.667969 C 342.15625 190.667969 347.804688 191.441406 353.183594 192.878906 L 353.183594 248.78125 C 353.183594 257.066406 359.898438 263.78125 368.183594 263.78125 C 376.464844 263.78125 383.183594 257.066406 383.183594 248.78125 L 383.183594 210.527344 C 394.609375 222.296875 401.667969 238.335938 401.667969 256 C 401.667969 290.023438 375.519531 318.042969 342.265625 321.054688 L 322.269531 301.058594 C 316.414062 295.199219 306.914062 295.199219 301.058594 301.058594 C 295.199219 306.914062 295.199219 316.410156 301.058594 322.269531 L 315.121094 336.332031 L 301.058594 350.398438 C 295.199219 356.253906 295.199219 365.753906 301.058594 371.613281 C 303.984375 374.539062 307.824219 376.003906 311.660156 376.003906 C 315.503906 376.003906 319.339844 374.539062 322.269531 371.613281 L 342.671875 351.207031 C 436.609375 347.859375 512 270.40625 512 175.667969 C 512 132.625 496.429688 93.15625 470.640625 62.574219 Z M 346.941406 105.9375 C 344.148438 108.726562 340.28125 110.335938 336.328125 110.335938 C 332.378906 110.335938 328.519531 108.726562 325.71875 105.9375 C 322.929688 103.148438 321.328125 99.289062 321.328125 95.335938 C 321.328125 91.386719 322.929688 87.519531 325.71875 84.726562 C 328.519531 81.9375 332.378906 80.335938 336.328125 80.335938 C 340.28125 80.335938 344.148438 81.9375 346.941406 84.726562 C 349.730469 87.519531 351.328125 91.386719 351.328125 95.335938 C 351.328125 99.285156 349.730469 103.148438 346.941406 105.9375 Z M 346.941406 105.9375 " />
              </g>
            </svg>
          </a>

          
          <div className="flex flex-row">
            {/* Pages */}

            <div className="flex flex-row mr-8 space-x-6 text-gray-500">

              <a
                className={`flex flex-row space-x-2 hover:text-indigo-300 dark:hover:text-gray-600 transition items-center cursor-pointer ${currentPage === 'trade' && 'text-indigo-600 dark:text-indigo-300'}`}
                onClick={() => setCurrentPage('trade')}
              >
                <i className={`fas fa-dollar-sign`} />
                <span>Trading</span>
              </a>

              <a
                className={`flex flex-row space-x-2 hover:text-indigo-300 dark:hover:text-gray-600 transition items-center cursor-pointer ${currentPage === 'analysis' && 'text-indigo-600 dark:text-indigo-300'}`}
                onClick={() => setCurrentPage('analysis')}
              >
                <i className={`fas fa-chart-pie`} />
                <span>Analyses</span>
              </a>

              <a
                className={`flex flex-row space-x-2 hover:text-indigo-300 dark:hover:text-gray-600 transition items-center cursor-pointer ${currentPage === 'backtest' && 'text-indigo-600 dark:text-indigo-300'}`}
                onClick={() => setCurrentPage('backtest')}
              >
                <i className={`fas fa-vial`} />
                <span>Backtests</span>
              </a>

            </div>

            {/* Dark mode toggle */}
            <a className="w-8 h-8 flex justify-center items-center cursor-pointer" onClick={() => setUseDarkMode(!useDarkMode)}>
              {useDarkMode ? (
                <svg className="text-white h-6 hover:animate-pulse" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
              ) : (
              <svg className="text-black h-6 hover:animate-pulse" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
              </svg>
              )}
            </a>

            {/* Connection indicator */}
            <a className="w-8 h-8 flex justify-center items-center">
              <i className={`fas fa-${socketOpen ? 'link text-green-700' : 'unlink text-red-700'}`} />
            </a>
          </div>

        </div>
      </nav>
    </>
  );
}

export default Navbar;
