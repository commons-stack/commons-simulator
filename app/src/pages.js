import React from 'react'
import Container from '@material-ui/core/Container'
import Typography from '@material-ui/core/Typography'
import Box from '@material-ui/core/Box'
import Link from '@material-ui/core/Link'
import Button from '@material-ui/core/Button'
import Radio from '@material-ui/core/Radio'
import RadioGroup from '@material-ui/core/RadioGroup'
import FormControlLabel from '@material-ui/core/FormControlLabel';
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

import ExpandLess from '@material-ui/icons/ExpandLess'
import ExpandMore from '@material-ui/icons/ExpandMore'

import { communityAction, hatchAction, abcAction, convictionAction } from './actions'
import ForceGraph from './graphs'
import {filterChanged} from './handlers'
import { serverURI } from './config'

export var graph


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
    <Header>
      <Title>Define your Community</Title>
      <Typography variant="h4">Set up your community</Typography>
    </Header>
    <Content>
       <Split
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
            <input type="hidden" name="beta" value="0.2" />
            <input type="hidden" name="rho" value="0.02" />
            <input type="hidden" name="theta" value="0.35" />
            <input type="hidden" name="sale_price" value="0.1" />
          </Params>
         }
         secondary={
          <Grid 
           container 
           direction="row"
           alignItems="center"
           style={{ position:"relative", top: "50%" }}
           justify="center">
             <div>
               On this page, configure your community.<br/>
               How many participants does it have?<br/>
               How many proposals are there?<br/>
               <br/>
               <br/>
               There are also some advanced parameters. 
           </div>
           </Grid>
         }
         />
          <NetworkGraph results={results} next={2} />
        </Content>
        </div>
  )
}

// Step 2
export const HatchPage = () => {
  const [results, setResults] = React.useState(false)
  return (
    <Split
      title={
        <Title>Define your Hatch</Title>
      }
      primary={
        <Content>
          <Params onSubmit={hatchAction(setResults)}>
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
              advanced="true"
            />
          </Params>
          <Results results={results} next={3} />
        </Content>
      }
      secondary={
        <LoremIpsum />
      }
    />
  )
}

// Step 3
export const ABCPage = () => {
  const [results, setResults] = React.useState(false)
  return (
    <Split
      title={
        <Title>Define your Augmented Bonding Curve</Title>
      }
      primary={
        <Content>
          <Params onSubmit={abcAction(setResults)}>
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
            <input type="hidden" name="initial_supply" value="10000" />
            <input type="hidden" name="initial_price" value="0.3" />
            <input type="hidden" name="theta" value="0.35" />
          </Params>
          <Results results={results} next={4} />
        </Content>
      }
      secondary={
        <LoremIpsum />
      }
    />
  )
}

// Step 4
export const ConvictionPage = () => {
  const [results, setResults] = React.useState(false)
  return (
    <Split
      title={
        <Title>Define your Conviction Voting</Title>
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
          <Results results={results} next={5} />
        </Content>
      }
      secondary={
        <LoremIpsum />
      }
    />
  )
}

// Step 5
export const CadCADPage = () => (
  <Split
    title={<Title>Simulation</Title>}
    primary={<>This simulation uses <Link href="https://cadcad.org">CadCAD</Link>.</>}
  />
)

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

const Split = ({ title, primary, secondary }) =>
  <Container>
    <Grid container spacing={5}>
      <Grid item xs={12}>
        {title}
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
    console.log(results);
    return (
      <Content>
       <Split
         primary={
          <div>
            <Typography variant="h4" gutterBottom>Results</Typography>
            <RadioGroup defaultValue="support" aria-label="filter" name="filter" onChange={filterChanged}>
                <FormControlLabel value="support" control={<Radio />} label="Support" />
                <FormControlLabel value="influence" control={<Radio />} label="Influence" />
                <FormControlLabel value="conflict" control={<Radio />} label="Conflict" />
            </RadioGroup>
            <ForceGraph network={results.network} width={600} height={600} />
          </div>
         }
         secondary={
          <Grid 
           container 
           direction="row"
           alignItems="center"
           style={{ position:"relative", top: "50%" }}
           justify="center">
             <div>
                This graph shows the relationship between participants and proposals.
             </div>
           </Grid>
         }
         />
       <Split
         primary={
              <Next to={next} />
         }
         />
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

const LoremIpsum = () =>
  <Content>
    <Typography variant="h4" gutterBottom>
      The standard Lorem Ipsum passage, used since the 1500s
    </Typography>
    <Typography gutterBottom>
      "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."
    </Typography>
    <Typography variant="h4" gutterBottom>
      Section 1.10.32 of "de Finibus Bonorum et Malorum", written by Cicero in 45 BC
    </Typography>
    <Typography gutterBottom>
      "Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo. Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia consequuntur magni dolores eos qui ratione voluptatem sequi nesciunt. Neque porro quisquam est, qui dolorem ipsum quia dolor sit amet, consectetur, adipisci velit, sed quia non numquam eius modi tempora incidunt ut labore et dolore magnam aliquam quaerat voluptatem. Ut enim ad minima veniam, quis nostrum exercitationem ullam corporis suscipit laboriosam, nisi ut aliquid ex ea commodi consequatur? Quis autem vel eum iure reprehenderit qui in ea voluptate velit esse quam nihil molestiae consequatur, vel illum qui dolorem eum fugiat quo voluptas nulla pariatur?"
    </Typography>
    <Typography variant="h4" gutterBottom>
      1914 translation by H. Rackham
    </Typography>
    <Typography gutterBottom>
      "But I must explain to you how all this mistaken idea of denouncing pleasure and praising pain was born and I will give you a complete account of the system, and expound the actual teachings of the great explorer of the truth, the master-builder of human happiness. No one rejects, dislikes, or avoids pleasure itself, because it is pleasure, but because those who do not know how to pursue pleasure rationally encounter consequences that are extremely painful. Nor again is there anyone who loves or pursues or desires to obtain pain of itself, because it is pain, but because occasionally circumstances occur in which toil and pain can procure him some great pleasure. To take a trivial example, which of us ever undertakes laborious physical exercise, except to obtain some advantage from it? But who has any right to find fault with a man who chooses to enjoy a pleasure that has no annoying consequences, or one who avoids a pain that produces no resultant pleasure?"
    </Typography>
    <Typography variant="h4" gutterBottom>
      Section 1.10.33 of "de Finibus Bonorum et Malorum", written by Cicero in 45 BC
    </Typography>
    <Typography>
      "At vero eos et accusamus et iusto odio dignissimos ducimus qui blanditiis praesentium voluptatum deleniti atque corrupti quos dolores et quas molestias excepturi sint occaecati cupiditate non provident, similique sunt in culpa qui officia deserunt mollitia animi, id est laborum et dolorum fuga. Et harum quidem rerum facilis est et expedita distinctio. Nam libero tempore, cum soluta nobis est eligendi optio cumque nihil impedit quo minus id quod maxime placeat facere possimus, omnis voluptas assumenda est, omnis dolor repellendus. Temporibus autem quibusdam et aut officiis debitis aut rerum necessitatibus saepe eveniet ut et voluptates repudiandae sint et molestiae non recusandae. Itaque earum rerum hic tenetur a sapiente delectus, ut aut reiciendis voluptatibus maiores alias consequatur aut perferendis doloribus asperiores repellat."
    </Typography>
    <Typography variant="h4" gutterBottom>
      1914 translation by H. Rackham
    </Typography>
    <Typography gutterBottom>
      "On the other hand, we denounce with righteous indignation and dislike men who are so beguiled and demoralized by the charms of pleasure of the moment, so blinded by desire, that they cannot foresee the pain and trouble that are bound to ensue; and equal blame belongs to those who fail in their duty through weakness of will, which is the same as saying through shrinking from toil and pain. These cases are perfectly simple and easy to distinguish. In a free hour, when our power of choice is untrammelled and when nothing prevents our being able to do what we like best, every pleasure is to be welcomed and every pain avoided. But in certain circumstances and owing to the claims of duty or the obligations of business it will frequently occur that pleasures have to be repudiated and annoyances accepted. The wise man therefore always holds in these matters to this principle of selection: he rejects pleasures to secure other greater pleasures, or else he endures pains to avoid worse pains."
    </Typography>
  </Content>
