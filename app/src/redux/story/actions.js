import { getCurrentStory, getCurrentPanelId } from './selectors'
import stories from '../../stories'

export const SET_CURRENT_STORY_ID = 'SET_CURRENT_STORY_ID'
export const SET_CURRENT_PANEL_ID = 'SET_CURRENT_PANEL_ID'
export const SET_STORY_PARAMETERS = 'SET_STORY_PARAMETERS'
export const SET_STORY_PARAMETER = 'SET_STORY_PARAMETER'

export const setCurrentStoryId = storyId => ({
  type: SET_CURRENT_STORY_ID,
  payload: {
    storyId,
  },
})

export const setCurrentPanelId = panelId => ({
  type: SET_CURRENT_PANEL_ID,
  payload: {
    panelId,
  },
})

export const setStoryParameters = parameters => ({
  type: SET_STORY_PARAMETERS,
  payload: {
    parameters,
  },
})
export const setStoryParameter = (parameterName, parameterValue) => ({
  type: SET_STORY_PARAMETER,
  payload: {
    parameterName,
    parameterValue,
  },
})

export const initiateStory = storyId => dispatch => {
  dispatch(setCurrentStoryId(storyId))
  dispatch(setCurrentPanelId(0))
  const story = stories.find(story => story.id === storyId)
  dispatch(setStoryParameters(story.defaultParameters))
}

export const changePanel = offset => (dispatch, getState) => {
  const state = getState()
  const currentStory = getCurrentStory(state)
  const currentPanelIndex = getCurrentPanelId(state)

  const eventualPanelIndex = currentPanelIndex + offset
  const boundedPanelId = Math.min(
    Math.max(eventualPanelIndex, 0),
    currentStory.panels.length - 1
  )

  dispatch(setCurrentPanelId(boundedPanelId))
}
