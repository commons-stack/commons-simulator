import React from 'react'
import { useSelector, useDispatch } from 'react-redux'

import { Box, Grid, Button, Typography } from '@material-ui/core'

import Panel from './Panel'
import {
  getCurrentPanelId,
  getPanelNavigationBounds,
} from '../redux/story/selectors'
import { changePanel } from '../redux/story/actions'

export default function StoryStrip({ story }) {
  const dispatch = useDispatch()
  const currentPanelId = useSelector(getCurrentPanelId)
  const navigationBounds = useSelector(getPanelNavigationBounds)

  const currentPanel = story.panels[currentPanelId]
  const currentSectionNumber = currentPanel.section + 1
  const totalSections = story.sections.length
  const currentSection = story.sections[currentPanel.section]

  function onPrevious() {
    dispatch(changePanel(-1))
  }
  function onNext() {
    dispatch(changePanel(1))
  }

  return (
    <Box mt={5} textAlign="center">
      <Typography variant="h5" gutterBottom>
        {story.title}
      </Typography>
      <Typography variant="h4" gutterBottom>
        {currentSectionNumber}/{totalSections} {currentSection}
      </Typography>

      <Box
        width="100%"
        display="flex"
        justifyContent="center"
        alignItems="center"
      >
        <Panel story={story} panelData={currentPanel} />
      </Box>

      <Box mt={2}>
        <Grid container spacing={1} justify="center">
          {navigationBounds[0] && (
            <Grid item>
              <Button
                variant="contained"
                color="secondary"
                onClick={onPrevious}
              >
                Previous
              </Button>
            </Grid>
          )}
          {navigationBounds[1] && (
            <Grid item>
              <Button
                variant="contained"
                color="primary"
                onClick={onNext}
              >
                Next
              </Button>
            </Grid>
          )}
        </Grid>
      </Box>
    </Box>
  )
}
