import React from 'react';
import { Box, Slider } from '@material-ui/core';

export const Community = () => {
  return (
    <Box m={2} pt={2}>
      <Slider
        label="Number of participants"
        name="participants"
        defaultValue={30}
        step={5}
        min={5}
        max={150}
        valueLabelDisplay="auto"
        marks
      />
    </Box>
  )
}

