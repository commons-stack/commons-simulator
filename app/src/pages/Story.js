import React, { useEffect } from 'react'
import {useDispatch, useSelector} from 'react-redux'


import StoryStrip from '../components/StoryStrip'
import Loader from '../components/Loader'

import { initiateStory } from '../redux/story/actions';
import { getCurrentStory } from '../redux/story/selectors'

import stories from '../stories'

export default function StoryPage() {
  const story = useSelector(getCurrentStory)
  const dispatch = useDispatch()

  useEffect(() => {
    if(!story) {
      dispatch(initiateStory(stories[0].id))
    }
  }, [story])

  if (story) {
    return <StoryStrip story={story} />
  } else {
    return <Loader />
  }
}
