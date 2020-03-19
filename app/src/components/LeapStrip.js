import React from 'react'
import { useSelector, useDispatch } from 'react-redux'

import { Box, Button, Typography } from '@material-ui/core'

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
  const currentSectionNumber = currentPanel.section + 1
  const totalSections = leap.sections.length
  const currentSection = leap.sections[currentPanel.section]

  function onPrevious() {
    dispatch(changePanel(-1))
  }
  function onNext() {
    dispatch(changePanel(1))
  }

  return (
    <Box mt={5} textAlign="center">
      <Typography variant="h5" gutterBottom>
        {leap.title}
      </Typography>
      <Typography variant="h4" gutterBottom>
        {currentSectionNumber}/{totalSections} {currentSection}
      </Typography>
      <Panel leap={leap} panelData={currentPanel} />
      {navigationBounds[0] && <Button variant="contained" color="secondary" onClick={onPrevious}>Previous</Button>}
      {navigationBounds[1] && <Button variant="contained" color="primary" onClick={onNext}>Next</Button>}
    </Box>
  )
}
