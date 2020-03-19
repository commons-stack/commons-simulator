import React from 'react';

import { Box, Typography, Button } from '@material-ui/core'
import { useDispatch } from 'react-redux'

import { initiateLeap } from '../redux/leap/actions';
import leaps from '../leaps';

export default function LeapSelector() {
  const dispatch = useDispatch();

  return (
    <Box textAlign="center">
      <Typography variant="h2">Choose your leap</Typography>
      <Box display="flex" flexDirection="column">
        {leaps.map(leap =>
          <Button
            key={leap.id}
            onClick={() => dispatch(initiateLeap(leap.id))}
          >
            {leap.title}
          </Button>
        )}
      </Box>
    </Box>
  )
}
