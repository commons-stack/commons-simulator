import { serverURI } from './config'

const generalAction = action => (setter, dispatch) => body => fetch(action, {
  method: 'POST',
  body
}).then(async result => {
  if (result.ok) {
    const values = await result.json()
    dispatch({ type: 'UPDATE_PARAMETERS', values })
    setter(values)
  }
})

export const communityAction = (setter, dispatch) => generalAction(`${serverURI}/community`)(setter, dispatch)

export const hatchAction = (setter, dispatch) => generalAction(`${serverURI}/hatch`)(setter, dispatch)

export const abcAction = (setter, dispatch) => generalAction(`${serverURI}/abc`)(setter, dispatch)

export const convictionAction = (setter, dispatch) => generalAction(`${serverURI}/conviction`)(setter, dispatch)

export const cadCADAction = (setter, dispatch) => generalAction(`${serverURI}/cadcad`)(setter, dispatch)
