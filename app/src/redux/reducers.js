import { combineReducers } from 'redux';
import leapReducer from './leap/reducer';

export default combineReducers({
  leap: leapReducer,
});