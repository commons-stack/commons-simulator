import { createStore, applyMiddleware, combineReducers } from 'redux'
import thunkMiddleware from 'redux-thunk'
import { createLogger } from 'redux-logger'

function parameters(state = {}, { type, values }) {
  switch (type) {
    case 'UPDATE_PARAMETERS':
      const {
        alpha,
        exit_tribute: exitTribute,
        hatch_price: hatchPrice,
        theta,
        vesting,
        kappa,
        invariant,
        beta,
        rho,
        initial_supply: initialSupply,
        initial_funds: initialFunds,
        initial_reserve: initialReserve,
        starting_price: startingPrice,
        initial_sentiment: initialSentiment,
      } = values
      const parameters = JSON.parse(JSON.stringify({
        alpha,
        exitTribute,
        hatchPrice,
        theta,
        vesting,
        kappa,
        invariant,
        beta,
        rho,
        initialSupply,
        initialFunds,
        initialReserve,
        startingPrice,
        initialSentiment,
      }))
      console.log(values)
      return {
        ...state,
        ...parameters,
      }
    default:
      return state
  }
}

const rootReducer = combineReducers({
  parameters,
})

const loggerMiddleware = createLogger()

export const store = createStore(
  rootReducer,
  applyMiddleware(thunkMiddleware, loggerMiddleware)
)
