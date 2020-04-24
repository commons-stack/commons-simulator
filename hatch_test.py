from hatch import *
import unittest
from datetime import datetime, timedelta

class TestHatch(unittest.TestCase):
    def test_vesting_curve(self):
        self.assertEqual(vesting_curve(90, 90, 90), 0)  # At Day 90, the cliff has just ended and the vesting curve has begun at 0
        self.assertEqual(vesting_curve(180, 90, 90), 0.5)  # At Day 180, the cliff has ended and we are in the vesting curve, whose half-life is 90 as well, so at 180 we should get 0.5.
        self.assertEqual(vesting_curve(270, 90, 90), 0.75)  # At Day 270, 2 half lives of the vesting curve have passed - 0.75 of tokens should be unlocked.
        self.assertLess(vesting_curve(89, 90, 90), 0)  # At Day 270, 2 half lives of the vesting curve have passed - 0.75 of tokens should be unlocked.
    def test_convert_80p_to_halflife(self):
        self.assertEqual(convert_80p_to_cliff_and_halflife(90), (41.64807836875666, 20.82403918437833))

class TestSystem(unittest.TestCase):
    def test_system(self):
        # 100,000 DAI invested for 1,000,000 tokens.
        desired_token_price = 0.1
        hatcher_contributions = [25000, 25000, 50000]
        token_supply_initial = sum(hatcher_contributions) / desired_token_price
        token_batches = contributions_to_token_batches(hatcher_contributions, token_supply_initial, 90)

        # Because of hatch_tribute, the collateral_pool is 0.7e6. This causes the token's post-hatch price to be 0.14.
        o = Commons(sum(hatcher_contributions), token_supply_initial, hatch_tribute=0.3)
        self.assertEqual(o._collateral_pool, 70000)
        self.assertEqual(o._funding_pool, 30000)
        self.assertEqual(o._token_supply, token_supply_initial)

        self.assertEqual(o.token_price(), 0.14)
        print(o.deposit(100))
        print(o.token_price())
        print(o._collateral_pool)