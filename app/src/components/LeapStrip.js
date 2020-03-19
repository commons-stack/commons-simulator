import React from 'react'
import { useSelector, useDispatch } from 'react-redux'

import { Box, Button } from '@material-ui/core'

import Panel from './Panel'
import {
  getCurrentPanelId,
  getPanelNavigationBounds,
} from '../redux/leap/selectors'
import { changePanel } from '../redux/leap/actions'

export default function LeapStrip({ leap }) {
  const dispatch = useDispatch()
  const currentPanelId = useSelector(getCurrentPanelId)
  const navigationBounds = useSelector(getPanelNavigationBounds)

  const currentPanel = leap.panels[currentPanelId]

  function onPrevious() {
    dispatch(changePanel(-1))
  }
  function onNext() {
    dispatch(changePanel(1))
  }

  return (
    <Box mt={5} textAlign="center">
      <Panel panelData={currentPanel} />
      {navigationBounds[0] && <Button onClick={onPrevious}>Previous</Button>}
      {navigationBounds[1] && <Button onClick={onNext}>Next</Button>}
    </Box>
  )
}
