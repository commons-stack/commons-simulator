import { get, isArray } from 'lodash'

export function selectProperty(path, defaultValue = null) {
  let stringPath = path
  if (isArray(stringPath)) {
    stringPath = stringPath.join('.')
  }
  return state => get(state, stringPath, defaultValue)
}
