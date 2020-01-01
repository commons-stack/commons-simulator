import React from 'react'
import { MuiThemeProvider, createMuiTheme } from '@material-ui/core/styles'
import 'typeface-ibm-plex-sans'

const primary = '#189518'
const secondary = '#67DE69'

const theme = createMuiTheme({
  palette: {
    type: 'dark',
    primary: {
      main: primary,
    },
    secondary: {
      main: secondary,
    },
  },
  typography: {
    fontFamily: '"IBM Plex Sans", Arial',
    useNextVariants: true,
  },
})

const ThemeProvider = ({ children }) => (
  <MuiThemeProvider theme={theme}>{children}</MuiThemeProvider>
)

export default ThemeProvider
