import { serverURI } from './config'

const generalAction = action => setter => body => fetch(action, {
  method: 'POST',
  body
}).then(async result => result.ok && setter(await result.json()))

export const communityAction = setter => generalAction(`${serverURI}/community`)(setter)

export const hatchAction = setter => generalAction(`${serverURI}/hatch`)(setter)

export const abcAction = setter => generalAction(`${serverURI}/abc`)(setter)

export const convictionAction = setter => generalAction(`${serverURI}/conviction`)(setter)

export const cadCADAction = setter => generalAction(`${serverURI}/cadcad`)(setter)
