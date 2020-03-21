import React, { useEffect } from 'react'
import {useDispatch, useSelector} from 'react-redux'


import LeapStrip from '../components/LeapStrip'
import Loader from '../components/Loader'

import { initiateLeap } from '../redux/leap/actions';
import { getCurrentLeap } from '../redux/leap/selectors'

import leaps from '../leaps'

export default function LeapPage() {
  const leap = useSelector(getCurrentLeap)
  const dispatch = useDispatch()

  useEffect(() => {
    if(!leap) {
      dispatch(initiateLeap(leaps[0].id))
    }
  }, [leap])

  if (leap) {
    return <LeapStrip leap={leap} />
  } else {
    return <Loader />
  }
}
