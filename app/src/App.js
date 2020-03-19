import React from 'react'
import { HashRouter as Router, Route, Switch, Redirect } from 'react-router-dom'
import { Provider } from 'react-redux'

import HomePage from './pages/Home'
import LeapPage from './pages/Leap'
import NavBar from './components/NavBar'

import store from './redux/store'

function App() {
  return (
    <Provider store={store}>
      <Router>
        <NavBar />
        <Switch>
          <Route path="/" exact component={HomePage} />
          <Route path="/leap" component={LeapPage} />
          <Route path="*" render={() => <Redirect to="/" />} />
        </Switch>
      </Router>
    </Provider>
  );
}

export default App
