import React from 'react'

import { Box, Card, CardMedia, CardContent, Typography } from '@material-ui/core'

import { makeStyles } from '@material-ui/core/styles';

const useStyles = makeStyles(theme => ({
  panelRoot: {
    width: 400,
    height: 400,
  },
  media: {
    height: 300,
  },
}));

export default function Panel({ leap, panelData }) {
  const classes = useStyles();

  return (
    <Card className={classes.panelRoot}>
      {panelData.illustration &&
      <CardMedia
        className={classes.media}
        image={`assets/leaps/${leap.id}/${panelData.illustration}`}
      />
      }


      {panelData.component &&
      <Box p={2}>
        {panelData.component()}
      </Box>
      }


      {panelData.bubbleText &&
      <CardContent>
        <Typography variant="body2" color="textSecondary" component="p">
          {panelData.bubbleText}
        </Typography>
      </CardContent>
      }
    </Card>
  )
}
