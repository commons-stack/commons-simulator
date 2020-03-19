import React, { useMemo } from 'react'
import { Box, Slider } from '@material-ui/core'
import { useSelector, useDispatch } from 'react-redux'

import { getLeapParameterSelector } from '../../redux/leap/selectors'
import { setLeapParameter } from '../../redux/leap/actions'

export const Participants = () => {
  const participants = useSelector(getLeapParameterSelector('participants'))
  const dispatch = useDispatch()

  return (
    <Box m={2} pt={2}>
      <Slider
        label="Number of participants"
        name="participants"
        value={participants}
        onChange={(_, value) =>
          dispatch(setLeapParameter('participants', value))
        }
        step={5}
        min={5}
        max={150}
        valueLabelDisplay="auto"
        marks
      />
    </Box>
  )
}
