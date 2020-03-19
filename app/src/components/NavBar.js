import React from 'react'
import { makeStyles } from '@material-ui/core/styles'
import AppBar from '@material-ui/core/AppBar'
import Toolbar from '@material-ui/core/Toolbar'
import Link from '@material-ui/core/Link'
import Button from '@material-ui/core/Button'
import Container from '@material-ui/core/Container'

const useStyles = makeStyles({
  root: {
    flexGrow: 1,
  },
  flex: {
    display: 'flex',
    alignItems: 'center',
  },
  grow: {
    flexGrow: 1,
    alignSelf: 'flex-start',
  },
})

function NavBar({ children }) {
  const classes = useStyles()
  return (
    <div className={classes.root}>
      <AppBar position="static" color="default">
        <Toolbar>
          <Container className={classes.flex}>
            <div className={classes.grow}>
              <Link to="/">
                <img
                  style={{ position: 'absolute', zIndex: 1 }}
                  src="/logo.svg"
                  alt="Logo"
                />
              </Link>
            </div>
            <div className={classes.flex}>
              <Button href="https://commonsstack.org">
                About Commons Stack
              </Button>
              <Button>High scores</Button>
              <Button href="https://github.com/commons-stack/commons-simulator">
                Github
              </Button>
              <Button href="https://gitcoin.co/grants/277/commons-simulator-modeling-sustainable-funding-for">
                Support project
              </Button>
            </div>
          </Container>
        </Toolbar>
      </AppBar>
    </div>
  )
}

export default NavBar
