import { getCurrentLeap, getCurrentPanelId } from './selectors'
import leaps from '../../leaps'

export const SET_CURRENT_LEAP_ID = 'SET_CURRENT_LEAP_ID'
export const SET_CURRENT_PANEL_ID = 'SET_CURRENT_PANEL_ID'
export const SET_LEAP_PARAMETERS = 'SET_LEAP_PARAMETERS'
export const SET_LEAP_PARAMETER = 'SET_LEAP_PARAMETER'

export const setCurrentLeapId = leapId => ({
  type: SET_CURRENT_LEAP_ID,
  payload: {
    leapId,
  },
})

export const setCurrentPanelId = panelId => ({
  type: SET_CURRENT_PANEL_ID,
  payload: {
    panelId,
  },
})

export const setLeapParameters = parameters => ({
  type: SET_LEAP_PARAMETERS,
  payload: {
    parameters,
  },
})
export const setLeapParameter = (parameterName, parameterValue) => ({
  type: SET_LEAP_PARAMETER,
  payload: {
    parameterName,
    parameterValue,
  },
})

export const initiateLeap = leapId => dispatch => {
  dispatch(setCurrentLeapId(leapId))
  dispatch(setCurrentPanelId(0))
  const leap = leaps.find(leap => leap.id === leapId)
  dispatch(setLeapParameters(leap.defaultParameters))
}

export const changePanel = offset => (dispatch, getState) => {
  const state = getState()
  const currentLeap = getCurrentLeap(state)
  const currentPanelIndex = getCurrentPanelId(state)

  const eventualPanelIndex = currentPanelIndex + offset
  const boundedPanelId = Math.min(
    Math.max(eventualPanelIndex, 0),
    currentLeap.panels.length - 1
  )

  dispatch(setCurrentPanelId(boundedPanelId))
}
