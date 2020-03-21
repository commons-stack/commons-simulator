import React from 'react'
import { Box, Slider } from '@material-ui/core'
import { useSelector, useDispatch } from 'react-redux'

import { getStoryParameterSelector } from '../../redux/story/selectors'
import { setStoryParameter } from '../../redux/story/actions'

export const Participants = () => {
  const participants = useSelector(getStoryParameterSelector('participants'))
  const dispatch = useDispatch()

  return (
    <Box m={2} pt={2}>
      <Slider
        label="Number of participants"
        name="participants"
        value={participants}
        onChange={(_, value) =>
          dispatch(setStoryParameter('participants', value))
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
