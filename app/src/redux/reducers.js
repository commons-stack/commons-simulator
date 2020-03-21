import { combineReducers } from 'redux'
import storyReducer from './story/reducer'

export default combineReducers({
  story: storyReducer,
})
