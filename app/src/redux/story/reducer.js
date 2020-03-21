import * as actions from './actions'

const initialState = {
  currentStoryId: null,
  currentPanelId: null,
  storyParameters: null,
}

export default function(state = initialState, action) {
  switch (action.type) {
    case actions.SET_CURRENT_STORY_ID: {
      const { storyId } = action.payload

      return {
        ...state,
        currentStoryId: storyId,
      }
    }
    case actions.SET_CURRENT_PANEL_ID: {
      const { panelId } = action.payload
      return {
        ...state,
        currentPanelId: panelId,
      }
    }
    case actions.SET_STORY_PARAMETERS: {
      const { parameters } = action.payload
      return {
        ...state,
        storyParameters: parameters,
      }
    }
    case actions.SET_STORY_PARAMETER: {
      const { parameterName, parameterValue } = action.payload
      return {
        ...state,
        storyParameters: {
          ...state.storyParameters,
          [parameterName]: parameterValue,
        },
      }
    }
    default:
      return state
  }
}
