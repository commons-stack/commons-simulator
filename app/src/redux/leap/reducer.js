import * as actions from './actions'

const initialState = {
  currentLeapId: null,
  currentPanelId: null,
}

export default function(state = initialState, action) {
  switch (action.type) {
    case actions.SET_CURRENT_LEAP_ID: {
      const { leapId } = action.payload

      return {
        ...state,
        currentLeapId: leapId,
      }
    }
    case actions.SET_CURRENT_PANEL_ID: {
      const { panelId } = action.payload
      return {
        ...state,
        currentPanelId: panelId,
      }
    }
    default:
      return state
  }
}
