import React from 'react'
import Container from '@material-ui/core/Container'
import Typography from '@material-ui/core/Typography'
import Box from '@material-ui/core/Box'
import Link from '@material-ui/core/Link'
import Button from '@material-ui/core/Button'
import Slider from '@material-ui/core/Slider'
import Collapse from '@material-ui/core/Collapse'
import List from '@material-ui/core/List'
import Grid from '@material-ui/core/Grid'
import ListSubheader from '@material-ui/core/ListSubheader'
import ListItem from '@material-ui/core/ListItem'
import ListItemText from '@material-ui/core/ListItemText'
import ListItemAvatar from '@material-ui/core/ListItemAvatar'
import Avatar from '@material-ui/core/Avatar'
import ImageIcon from '@material-ui/icons/Image'
import BallotIcon from '@material-ui/icons/Ballot'

import Tooltip from '@material-ui/core/Tooltip'
import Fab from '@material-ui/core/Fab'

import ExpandLess from '@material-ui/icons/ExpandLess'
import ExpandMore from '@material-ui/icons/ExpandMore'

import { communityAction, hatchAction, abcAction, convictionAction, cadCADAction } from './actions'
import ForceGraph from './graphs'
import { serverURI } from './config'

export const HomePage = () => (
  <Header>
    <Title>Can you build a sustainable Commons?</Title>
    <Subtitle>Give it a try!</Subtitle>
    <Button color="primary" variant="contained" href="/#/step1">Next</Button>
  </Header>
)

const marks = marks => marks.map(m => ({value: m, label: m}))

// Step 1
export const CommunityPage = () => {
  const [results, setResults] = React.useState(false)
  return (
    <div>
      <Layout
        title="You've chosen to build a commons in support of orphans in Barcelona"
        description={
          <>
           The first step in building your Commons is to collect together a flock of 'Hatchers'. Hatchers will help you kickstart the Commons. Hatchers make programming and spending decisions for your commons, so choose carefully. Stakeholders already interested in the project, such as current donors to orphanages in Barcelona, child psychologists, employees and volunteers at those orphanages, etc. are appropriate. These people will help your commons raise its initial funding. You are not looking for investors! Look for altruistic people that truly care about making an impact on the lives of children in Barcelona that have lost their parents.
          </>
         }
         primary={
          <Params onSubmit={communityAction(setResults)}>
            <SliderField
              label="Number of participants"
              name="participants"
              defaultValue={30}
              step={5}
              min={5}
              max={150}
            />
            <SliderField
              label="Number of proposals"
              name="proposals"
              icon={BallotIcon}
              defaultValue={3}
              step={1}
              min={1}
              max={10}
            />
            {/* TODO: Participants factor (how many participants per hatcher) */}
            <SliderField
              label="Initial sentiment"
              name="initial_sentiment"
              defaultValue={0.6}
              step={0.1}
              min={0}
              max={1}
              advanced="true"
            />
            <SliderField
              label="Sentiment decay"
              name="sentiment_decay"
              defaultValue={0.1}
              step={0.05}
              min={0}
              max={1}
              advanced="true"
            />
          </Params>
         }
         secondary={
          <NetworkGraph results={results} next={2} />
         }
         />
        </div>
  )
}

// Step 2
export const HatchPage = () => {
  const [results, setResults] = React.useState(false)
  return (
    <Layout
      title="So let’s see how you will define the Hatch of your future Commons!"
      description={
        <>
          The Hatchers of the Orphans of Barcelona Commons are well incentivized to raise funds, the more money they raise the more tokens they get. Because of how bonding curves work, the Hatchers will be getting tokens for a very good price! Much cheaper than anyone else will be able to get them.

          However, to get these cheap tokens, the Hatchers have to donate a percentage of their donations to kick start the funding pool, and their tokens are vested for a certain amount of time.
        </>
       }
      primary={
        <Content>
          <Params onSubmit={hatchAction(setResults)}>
            <SliderField
              label="Theta"
              name="theta"
              defaultValue={0.4}
              step={0.01}
              min={0}
              max={1}
            />
            <SliderField
              label="Vesting (in weeks)"
              name="vesting"
              defaultValue={52}
              step={1}
              min={0}
              max={260}
            />
            <SliderField
              label="Hatch price"
              name="hatch_price"
              defaultValue={0.1}
              step={0.1}
              min={0.1}
              max={1}
              advanced="true"
            />
          </Params>
        </Content>
      }
      secondary={
        <Results results={results} next={3} />
      }
    />
  )
}

// Step 3
export const ABCPage = () => {
  const [results, setResults] = React.useState(false)
  return (
    <Layout
      title="Define your Augmented Bonding Curve"
      description={
        <>
        "Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo. Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia consequuntur magni dolores eos qui ratione voluptatem sequi nesciunt. Neque porro quisquam est, qui dolorem ipsum quia dolor sit amet, consectetur, adipisci velit, sed quia non numquam eius modi tempora incidunt ut labore et dolore magnam aliquam quaerat voluptatem. Ut enim ad minima veniam, quis nostrum exercitationem ullam corporis suscipit laboriosam, nisi ut aliquid ex ea commodi consequatur? Quis autem vel eum iure reprehenderit qui in ea voluptate velit esse quam nihil molestiae consequatur, vel illum qui dolorem eum fugiat quo voluptas nulla pariatur?"
        </>
      }
      primary={
        <Content>
          <Params onSubmit={abcAction(setResults)}>
            <SliderField
              label="Curvature"
              name="kappa"
              defaultValue={6}
              step={1}
              min={1}
              max={10}
            />
            <SliderField
              label="Exit tribute"
              name="exit_tribute"
              defaultValue={0.2}
              step={0.05}
              min={0}
              max={1}
            />
            <input type="hidden" name="initial_supply" value="10000" />
            <input type="hidden" name="hatch_price" value="0.1" />
            <input type="hidden" name="theta" value="0.35" />
          </Params>
        </Content>
      }
      secondary={
        <Results results={results} next={4} />
      }
    />
  )
}

// Step 4
export const ConvictionPage = () => {
  const [results, setResults] = React.useState(false)
  return (
    <Layout
      title="Define your Conviction Voting"
      description={
        <>
        "Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo. Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia consequuntur magni dolores eos qui ratione voluptatem sequi nesciunt. Neque porro quisquam est, qui dolorem ipsum quia dolor sit amet, consectetur, adipisci velit, sed quia non numquam eius modi tempora incidunt ut labore et dolore magnam aliquam quaerat voluptatem. Ut enim ad minima veniam, quis nostrum exercitationem ullam corporis suscipit laboriosam, nisi ut aliquid ex ea commodi consequatur? Quis autem vel eum iure reprehenderit qui in ea voluptate velit esse quam nihil molestiae consequatur, vel illum qui dolorem eum fugiat quo voluptas nulla pariatur?"
        </>
      }
      primary={
        <Content>
          <Params onSubmit={convictionAction(setResults)}>
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
              advanced="true"
            />
          </Params>
        </Content>
      }
      secondary={
        <Results results={results} next={5} />
      }
    />
  )
}

// Step 5
export const CadCADPage = () => {
  const [results, setResults] = React.useState(false)
  const ref = React.useRef(null)
  const handleSubmit = e => {
    e.preventDefault()
    const data = new FormData(ref.current)
    console.log(new URLSearchParams(data).toString())
    cadCADAction(setResults)(data)
  }
  return (
    <Layout
      title={<Title>Simulation</Title>}
      primary={
        <>
          This simulation uses <Link href="https://cadcad.org">CadCAD</Link>.
          <form ref={ref} onSubmit={handleSubmit}>
            <input type="hidden" name="alpha" value="0.9" />
            <input type="hidden" name="exit_tribute" value="0.2" />
            <input type="hidden" name="kappa" value="6" />
            <input type="hidden" name="invariant" value="15.384615384615385" />
            <input type="hidden" name="beta" value="0.2" />
            <input type="hidden" name="rho" value="0.02" />
            <input type="hidden" name="initial_supply" value="619405.175420327" />
            <input type="hidden" name="initial_funds" value="350" />
            <input type="hidden" name="initial_reserve" value="650" />
            <input type="hidden" name="starting_price" value="0.065" />
            <input type="hidden" name="initial_sentiment" value="0.6" />
            <Run />
          </form>
        </>
      }
      secondary={<Results results={results} />}
    />
  )
}

const Header = ({children}) => (
  <div
     style={{
       textAlign: "center", marginTop: "50px"

     }}
  >
  {children}
  </div>
)

const Content = ({ children }) => (
  <Grid container spacing={2}>
    {React.Children.map(children, child => (
      <Grid item sm={12}>
        <Box>
          {child}
        </Box>
      </Grid>
    ))}
  </Grid>
)

const Layout = ({ title, description, primary, secondary }) =>
  <Container>
    <Grid container spacing={5}>
      <Grid item xs={12}>
        <Header><Title>{title}</Title></Header>
        <Typography>{description}</Typography>
      </Grid>
      <Grid item xs={12} md={6}>
      {primary}
      </Grid>
      <Grid item xs={12} md={6}>
      {secondary}
      </Grid>
    </Grid>
  </Container>

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
        {children.filter(({props}) => !props.advanced && props.type !== 'hidden').map(item =>
          <ListItem key={item.props.name}>
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
        {children.filter(({props}) => !props.advanced && props.type === 'hidden')}
        <ListItem button onClick={handleClick} key="advanced">
          <ListItemText primary={<ListSubheader disableGutters>Advanced</ListSubheader>} />
          {open ? <ExpandLess /> : <ExpandMore />}
        </ListItem>
        <Collapse in={open} timeout="auto">
          <List component="div" disablePadding>
            {children.filter(({props}) => props.advanced).map(item =>
              <ListItem key={item.props.name}>
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

const NetworkGraph = ({ results, next }) => {
    if (!results) {
      return ""
    }
    return (
      <Content>
        <Typography variant="h4" gutterBottom>Results{' '}
        <Tooltip title={
          <>
            This graph shows the relationship between participants and proposals.<br/><br/>

            Blue nodes represent participants, green nodes proposals. Their size is proportional to their holdings resp. the funds requested.<br/><br/>

            Clicking on a node will show its relationship with other nodes. The selection choices at the top determine what will be shown:
            <ul>
              <li>Support: On click, all the proposals supported by the participant resp. all participants supporting a proposal will be highlighted</li>
              <li>Influence: On click, all other participants influeced by the selected one are shown</li>
              <li>Conflict: On click, all other proposals with which this proposal has a conflict are highlighted</li>
            </ul>
          </>
        }>
          <Fab size="small" color="primary">?</Fab>
        </Tooltip>
        </Typography>
        <ForceGraph network={results.network} width={600} height={600} />
        <Next to={next} />
      </Content>
    )
}

const Results = ({ results, next }) =>
   results &&
    <div css={`margin-top: 20px`}>
      <Typography variant="h4" gutterBottom>Results</Typography>
      {results.results && results.results.map((uri, i) => <img key={i} src={`${serverURI}/${uri}`} alt="" width="100%" />)}
      <Next to={next} />
    </div>

const Next = ({ to }) => (
  <Button color="primary" variant="contained" href={`/#/step${to}`}>Next</Button>
)

const Run = () => (
  <Button type="submit" color="primary" variant="contained">Run</Button>
)
