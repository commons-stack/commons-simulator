import React from 'react'
import Container from '@material-ui/core/Container'
import Typography from '@material-ui/core/Typography'
import Box from '@material-ui/core/Box'
import Link from '@material-ui/core/Link'
import Button from '@material-ui/core/Button'
import Slider from '@material-ui/core/Slider'
import Collapse from '@material-ui/core/Collapse'
import List from '@material-ui/core/List'
import ListSubheader from '@material-ui/core/ListSubheader'
import ListItem from '@material-ui/core/ListItem'
import ListItemText from '@material-ui/core/ListItemText'
import ListItemAvatar from '@material-ui/core/ListItemAvatar'
import Avatar from '@material-ui/core/Avatar'
import ImageIcon from '@material-ui/icons/Image'
import BallotIcon from '@material-ui/icons/Ballot'

import ExpandLess from '@material-ui/icons/ExpandLess'
import ExpandMore from '@material-ui/icons/ExpandMore'

import { communityAction, hatchAction, abcAction, convictionAction } from './actions'

export const HomePage = () => (
  <Main>
    <Title>Can you build a sustainable Commons?</Title>
    <Subtitle>Give it a try!</Subtitle>
    <Button color="primary" variant="contained" href="/#/step1">Next</Button>
  </Main>
)

const marks = marks => marks.map(m => ({value: m, label: m}))

// Step 1
export const CommunityPage = () => (
  <Main>
    <Title>Define your Community</Title>
    <Params onSubmit={communityAction}>
      <SliderField
        label="Number of participants"
        defaultValue={30}
        step={5}
        min={5}
        max={150}
      />
      <SliderField
        label="Number of proposals"
        icon={BallotIcon}
        defaultValue={3}
        step={1}
        min={1}
        max={10}
      />
      {/* TODO: Participants factor (how many participants per hatcher) */}
      <SliderField
        label="Initial sentiment"
        defaultValue={3}
        step={1}
        min={1}
        max={10}
        advanced
      />
      <SliderField
        label="Sentiment decay"
        defaultValue={3}
        step={1}
        min={1}
        max={10}
        advanced
      />
    </Params>
    <Typography>Some graph here</Typography>
    <Next to="2" />
  </Main>
)

// Step 2
export const HatchPage = () => (
  <Main>
    <Title>Define your Hatch</Title>
    <Params onSubmit={hatchAction}>
      <SliderField
        label="Theta"
        defaultValue={0.4}
        step={0.01}
        min={0}
        max={1}
      />
      <SliderField
        label="Vesting (in weeks)"
        defaultValue={52}
        step={1}
        min={0}
        max={260}
      />
      <SliderField
        label="Hatch price"
        defaultValue={0.1}
        step={0.1}
        min={0.1}
        max={1}
        advanced
      />
    </Params>
    <Typography>Some graph here</Typography>
    <Next to="3" />
  </Main>
)

// Step 3
export const ABCPage = () => (
  <Main>
    <Title>Define your Augmented Bonding Curve</Title>
    <Params onSubmit={abcAction}>
      <SliderField
        label="Curvature"
        defaultValue={6}
        step={1}
        min={1}
        max={10}
      />
      <SliderField
        label="Exit tribute"
        defaultValue={0.2}
        step={0.05}
        min={0}
        max={1}
      />
    </Params>
    <Next to="4" />
  </Main>
)

// Step 4
export const ConvictionPage = () => (
  <Main>
    <Title>Define your Conviction Voting</Title>
    <Params onSubmit={convictionAction}>
      <SliderField
        label="Alpha (in the future: Time to reach 80% voting power)"
        name="alpha"
        defaultValue={0.9}
        step={0.05}
        min={0.5}
        max={1}
      />
      <SliderField
        label="Max Proposal Amount that can be spent in one proposal"
        name="beta"
        defaultValue={0.2}
        step={0.05}
        min={0.1}
        max={1}
      />
      <SliderField
        label="Rho"
        name="rho"
        defaultValue={0.02}
        step={0.01}
        min={0.01}
        max={0.1}
        advanced
      />
    </Params>
    <Next to="5" />
  </Main>
)

// Step 5
export const CadCADPage = () => (
  <Main>
    <Title>Simulation</Title>
    This simulation uses <Link href="https://cadcad.org">CadCAD</Link>.
  </Main>
)

const Main = ({ children }) => (
  <Container maxWidth="sm">
    <Box my={4}>
      {children}
    </Box>
  </Container>
)

const Title = ({ children }) => (
    <Typography variant="h2" component="h2" gutterBottom>{children}</Typography>
)

const Subtitle = ({ children }) => (
    <Typography variant="h3" component="h3" gutterBottom>{children}</Typography>
)

const SliderField = ({...props}) => (
  <Slider {...props} valueLabelDisplay="auto" marks={marks([props.min, props.defaultValue, props.max])} />
)

const Params = ({ onSubmit, children }) => {
  const [open, setOpen] = React.useState(false)
  const ref = React.useRef(null)

  const handleClick = () => {
    setOpen(!open)
  }

  const handleSubmit = e => {
    e.preventDefault()
    const data = new FormData(ref.current)
    console.log(new URLSearchParams(data).toString())
    onSubmit(data)
  }
  return (
    <form ref={ref} onSubmit={handleSubmit}>
      <List
        subheader={
          <ListSubheader>
            Parameters
          </ListSubheader>
        }
      >
        {children.filter(({props}) => !props.advanced).map(item =>
          <ListItem>
            <ListItemAvatar>
              <Avatar>
                <ImageIcon />
              </Avatar>
            </ListItemAvatar>
            <ListItemText
              primary={<Typography gutterBottom>{item.props.label}</Typography>}
              secondary={item}
            />
          </ListItem>

        )}
        <ListItem button onClick={handleClick}>
          <ListItemText primary={<ListSubheader disableGutters>Advanced</ListSubheader>} />
          {open ? <ExpandLess /> : <ExpandMore />}
        </ListItem>
        <Collapse in={open} timeout="auto">
          <List component="div" disablePadding>
            {children.filter(({props}) => props.advanced).map(item =>
              <ListItem>
                <ListItemAvatar>
                  <Avatar>
                    <ImageIcon />
                  </Avatar>
                </ListItemAvatar>
                <ListItemText
                  primary={<Typography gutterBottom>{item.props.label}</Typography>}
                  secondary={item}
                />
              </ListItem>
            )}
          </List>
        </Collapse>
      </List>
      <Run />
    </form>
  )
}

const Next = ({ to }) => (
  <Button color="primary" variant="contained" href={`/#/step${to}`}>Next</Button>
)

const Run = () => (
  <Button type="submit" color="primary" variant="contained">Run</Button>
)
