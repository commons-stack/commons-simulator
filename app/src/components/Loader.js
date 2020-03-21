import React from 'react'

import {
  Box,
  CircularProgress,
} from '@material-ui/core'


export default function Loader() {
  return (
    <Box display="flex" justifyContent="center" alignItems="center">
      <CircularProgress />
    </Box>
  )
}
