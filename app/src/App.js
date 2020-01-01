import React from 'react'
import { HashRouter as Router, Route, Switch, Redirect } from 'react-router-dom'
import { HomePage, CommunityPage, HatchPage, ABCPage, ConvictionPage, CadCADPage } from './pages'


function App() {
  return (
    <Router>
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
  );
}

export default App
