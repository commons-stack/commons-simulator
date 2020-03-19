import { getCurrentLeap, getCurrentPanelId } from './selectors';

export const SET_CURRENT_LEAP_ID = 'SET_CURRENT_LEAP_ID';
export const SET_CURRENT_PANEL_ID = 'SET_CURRENT_PANEL_ID';

export const setCurrentLeapId = (leapId) => ({
  type: SET_CURRENT_LEAP_ID,
  payload: {
    leapId,
  }
});

export const setCurrentPanelId = (panelId) => ({
  type: SET_CURRENT_PANEL_ID,
  payload: {
    panelId,
  }
});

export const initiateLeap = (leapId) => (dispatch) => {
  dispatch(setCurrentLeapId(leapId))
  dispatch(setCurrentPanelId(0))
}

export const changePanel = (offset) => (dispatch, getState) => {
  const state = getState();
  const currentLeap = getCurrentLeap(state);
  const currentPanelIndex = getCurrentPanelId(state);

  const eventualPanelIndex = currentPanelIndex + offset;
  const boundedPanelId = Math.min(Math.max(eventualPanelIndex, 0), currentLeap.panels.length - 1);

  dispatch(setCurrentPanelId(boundedPanelId))
}