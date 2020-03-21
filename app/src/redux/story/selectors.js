import { createSelector } from 'reselect'
import { selectProperty } from '../helpers'
import storys from '../../stories'

export const getCurrentStoryId = selectProperty(['story', 'currentStoryId'])
export const getCurrentStory = createSelector(getCurrentStoryId, currentStoryId =>
  storys.find(story => story.id === currentStoryId)
)
export const getCurrentPanelId = selectProperty(['story', 'currentPanelId'])
export const getPanelNavigationBounds = createSelector(
  getCurrentStory,
  getCurrentPanelId,
  (currentStory, currentPanelId) => [
    currentPanelId !== 0,
    currentPanelId !== currentStory.panels.length - 1,
  ]
)

export const getStoryParameterSelector = parameterName =>
  selectProperty(['story', 'storyParameters', parameterName])
