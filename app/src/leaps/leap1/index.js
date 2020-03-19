import { Community } from './Community'

export const leap = {
  id: 'leap1',
  title: 'Leap 1',
  sections: ['Define your community', 'Define your hatch'],
  panels: [
    {
      illustration: 'arseny-togulev-BtLanXbBfO0-unsplash.jpg',
      bubbleText:
        'You don’t land in a different time-space so much as you appear in it, the sensation of gravity slowly returning to each of your trillions of cells.',
      section: 0,
    },
    {
      illustration: 'florian-olivo-KV0MS5u2big-unsplash.jpg',
      bubbleText:
        'Despite never being in the 21st century before, strangely enough, the smell is instantly familiar.',
      section: 0,
    },
    {
      component: Community,
      bubbleText:
        'In your first 30 minutes of conversation with the RadicalxChange (RxC) community, you brainstorm the needs of this community in order for them to thrive and save the future of humanity with their novel economic tools.',
      section: 1,
    },
  ],
}
