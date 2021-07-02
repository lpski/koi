// craco.config.js
const CracoAlias = require("craco-alias");

module.exports = {
    style: {
      postcss: {
        plugins: [
          require('tailwindcss'),
          require('autoprefixer'),
        ],
      },
    },
    plugins: [
      {
         plugin: CracoAlias,
         options: {
            source: "tsconfig",
            baseUrl: ".",
            /* tsConfigPath should point to the file where "baseUrl" and "paths" 
            are specified*/
            tsConfigPath: "./tsconfig.paths.json"
         }
      }
   ]
  }