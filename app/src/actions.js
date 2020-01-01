const serverURI = 'http://localhost:5000'

const generalAction = action => body => fetch(action, {
  method: 'POST',
  body
})

export const communityAction = generalAction(`${serverURI}/community`)

export const hatchAction = generalAction(`${serverURI}/hatch`)

export const abcAction = generalAction(`${serverURI}/abc`)

export const convictionAction = generalAction(`${serverURI}/conviction`)
