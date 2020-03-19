import React from 'react'
import { useSelector } from 'react-redux'

import { getCurrentLeap } from '../redux/leap/selectors'

import LeapStrip from '../components/LeapStrip'
import LeapSelector from '../components/LeapSelector'

export default function LeapPage() {
  const leap = useSelector(getCurrentLeap)

  if (leap) {
    return <LeapStrip leap={leap} />
  } else {
    return <LeapSelector />
  }
}
