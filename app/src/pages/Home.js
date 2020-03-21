import React from 'react'

import { Box, Typography, Button } from '@material-ui/core'

export default function HomePage() {
  return (
    <Box mt={5} textAlign="center">
      <Typography variant="h2" gutterBottom>
        Can you build a sustainable Commons?
      </Typography>
      <Typography variant="h3" gutterBottom>
        Give it a try!
      </Typography>
      <Button color="primary" variant="contained" href="/#/story">
        Start
      </Button>
    </Box>
  )
}
