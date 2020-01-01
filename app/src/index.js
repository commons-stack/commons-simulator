import React from 'react'
import ReactDOM from 'react-dom'
import CssBaseline from '@material-ui/core/CssBaseline'
import ThemeProvider from './providers/ThemeProvider'
import App from './App'
import * as serviceWorker from './serviceWorker'

ReactDOM.render(
  <ThemeProvider>
    <CssBaseline />
    <App />
  </ThemeProvider>,
  document.getElementById('root')
)

// If you want your app to work offline and load faster, you can change
// unregister() to register() below. Note this comes with some pitfalls.
// Learn more about service workers: https://bit.ly/CRA-PWA
serviceWorker.unregister()
