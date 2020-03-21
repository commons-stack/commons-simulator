import React from 'react'

import { Box, Typography, Button } from '@material-ui/core'
import { useDispatch } from 'react-redux'

import { initiateStory } from '../redux/story/actions'
import stories from '../stories'

export default function StorySelector() {
  const dispatch = useDispatch()

  return (
    <Box textAlign="center">
      <Typography variant="h2">Choose your story</Typography>
      <Box
        display="flex"
        flexDirection="column"
        width={200}
        margin="auto"
        alignItems="center"
      >
        {stories.map(story => (
          <Button
            key={story.id}
            onClick={() => dispatch(initiateStory(story.id))}
            color="primary"
            variant="contained"
          >
            {story.title}
          </Button>
        ))}
      </Box>
    </Box>
  )
}
