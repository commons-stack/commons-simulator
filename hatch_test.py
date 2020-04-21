from hatch import *
import unittest
from datetime import datetime, timedelta

class TestHatch(unittest.TestCase):
    def test_unlocked_fraction(self):
        self.assertEqual(unlocked_fraction(90, 90, 90), 0)  # At Day 90, the cliff has just ended and the vesting curve has begun at 0
        self.assertEqual(unlocked_fraction(180, 90, 90), 0.5)  # At Day 180, the cliff has ended and we are in the vesting curve, whose half-life is 90 as well, so at 180 we should get 0.5.
        self.assertEqual(unlocked_fraction(270, 90, 90), 0.75)  # At Day 270, 2 half lives of the vesting curve have passed - 0.75 of tokens should be unlocked.
        self.assertLess(unlocked_fraction(89, 90, 90), 0)  # At Day 270, 2 half lives of the vesting curve have passed - 0.75 of tokens should be unlocked.
    def test_convert_80p_to_halflife(self):
        self.assertEqual(convert_80p_to_cliff_and_halflife(90), (41.64807836875666, 20.82403918437833))

class TestSystem(unittest.TestCase):
    def test_system(self):
        # 3 contributors contribute equally to the foundation of an organization for 6 million tokens.
        token_supply_initial = 6e6
        hatcher_contributions = [3e3, 3e3, 3e3]
        token_batches = contributions_to_token_batches(hatcher_contributions, token_supply_initial, 90)

        o = Organization(sum(hatcher_contributions), token_supply_initial, funding_pool_fraction=0.3)
        self.assertEqual(o._collateral_pool, 6300)
        self.assertEqual(o._funding_pool, 2700)
        self.assertEqual(o._token_supply, token_supply_initial)

        print(o.token_price())
        print(o.deposit(100))
        print(o.token_price())
        print(o._collateral_pool)