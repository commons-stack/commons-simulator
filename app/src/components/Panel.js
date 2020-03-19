import React from 'react';

import { Box, Typography } from '@material-ui/core'

export default function Panel({ panelData }) {
  return (
    <Box>
      <Typography>{panelData.bubbleText}</Typography>
    </Box>
  )
}
