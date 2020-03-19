import * as actions from './actions'

const initialState = {
  currentLeapId: null,
  currentPanelId: null,
  leapParameters: null,
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
    case actions.SET_LEAP_PARAMETERS: {
      const { parameters } = action.payload
      return {
        ...state,
        leapParameters: parameters,
      }
    }
    case actions.SET_LEAP_PARAMETER: {
      const { parameterName, parameterValue } = action.payload
      return {
        ...state,
        leapParameters: {
          ...state.leapParameters,
          [parameterName]: parameterValue,
        },
      }
    }
    default:
      return state
  }
}
