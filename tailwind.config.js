module.exports = {
  purge: ['./src/**/*.{js,jsx,ts,tsx}', './public/index.html'],
  darkMode: 'class', // or 'media' or 'class'
  theme: {
    extend: {
      colors: {
        'off-white': '#f5f0f0',
        'egg-shell': '#e7ddd2',
        'lime': '#bef264',
        'off-gray': '#413f3f',
        'off-black': '#090202'
      }
    },
  },
  variants: {
    extend: {
      animation: ['hover']
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
  ],
}
