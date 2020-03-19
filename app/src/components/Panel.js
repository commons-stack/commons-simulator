import React from 'react'

import { Box, Typography } from '@material-ui/core'

export default function Panel({ leap, panelData }) {
  return (
    <Box>
      {panelData.illustration &&
      <img src={`assets/leaps/${leap.id}/${panelData.illustration}`}/>
      }
      {panelData.bubbleText &&
      <Typography>{panelData.bubbleText}</Typography>
      }
    </Box>
  )
}
