import React from 'react'
import { HashRouter as Router, Route, Switch, Redirect } from 'react-router-dom'
import { Provider } from 'react-redux'
import { HomePage, CommunityPage, HatchPage, ABCPage, ConvictionPage, CadCADPage } from './pages'
import { NavBar } from './components'
import { store } from './store'

function App() {
  return (
    <Provider store={store}>
      <Router>
        <NavBar />
        <Switch>
          <Route path="/" exact component={HomePage} />
          <Route path="/step1" component={CommunityPage} />
          <Route path="/step2" component={HatchPage} />
          <Route path="/step3" component={ABCPage} />
          <Route path="/step4" component={ConvictionPage} />
          <Route path="/step5" component={CadCADPage} />
          <Route render={() => <Redirect to="/" />} />
        </Switch>
      </Router>
    </Provider>
  );
}

export default App
