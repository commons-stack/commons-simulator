import { createSelector } from 'reselect'
import { selectProperty } from '../helpers'
import leaps from '../../leaps'

export const getCurrentLeapId = selectProperty(['leap', 'currentLeapId'])
export const getCurrentLeap = createSelector(getCurrentLeapId, currentLeapId =>
  leaps.find(leap => leap.id === currentLeapId)
)
export const getCurrentPanelId = selectProperty(['leap', 'currentPanelId'])
export const getPanelNavigationBounds = createSelector(
  getCurrentLeap,
  getCurrentPanelId,
  (currentLeap, currentPanelId) => [
    currentPanelId !== 0,
    currentPanelId !== currentLeap.panels.length - 1,
  ]
)

export const getLeapParameterSelector = parameterName =>
  selectProperty(['leap', 'leapParameters', parameterName])
