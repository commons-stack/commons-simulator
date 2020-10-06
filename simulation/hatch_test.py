from hatch import *
import unittest


class HatchTest(unittest.TestCase):
    def test_vesting_curve(self):
        # At Day 90, the cliff has just ended and the vesting curve has begun at 0
        self.assertEqual(vesting_curve(90, 90, 90), 0)
        # At Day 180, the cliff has ended and we are in the vesting curve, whose half-life is 90 as well, so at 180 we should get 0.5.
        self.assertEqual(vesting_curve(180, 90, 90), 0.5)
        # At Day 270, 2 half lives of the vesting curve have passed - 0.75 of tokens should be unlocked.
        self.assertEqual(vesting_curve(270, 90, 90), 0.75)
        # At Day 270, 2 half lives of the vesting curve have passed - 0.75 of tokens should be unlocked.
        self.assertLess(vesting_curve(89, 90, 90), 0)

    def test_convert_80p_to_halflife(self):
        self.assertEqual(convert_80p_to_cliff_and_halflife(
            90), (41.64807836875666, 20.82403918437833))


class TokenBatchTest(unittest.TestCase):
    def test_bool(self):
        zero = TokenBatch(0, 0)
        vesting_only = TokenBatch(1, 0)
        nonvesting_only = TokenBatch(0, 1)
        both = TokenBatch(1, 1)
        self.assertFalse(bool(zero))
        self.assertTrue(bool(vesting_only))
        self.assertTrue(bool(nonvesting_only))
        self.assertTrue(bool(both))

        vesting_all_spent = TokenBatch(1, 1)
        vesting_all_spent.vesting_spent = 1
        vesting_all_spent.nonvesting = 0
        self.assertFalse(bool(vesting_all_spent))

    def test_add_(self):
        two = TokenBatch(2, 1)
        three = TokenBatch(3, 5)
        answer = two+three

        self.assertEqual(answer, (5, 6))

    def test_sub_(self):
        five = TokenBatch(1, 5)
        four = TokenBatch(1, 4)
        self.assertEqual(five-four, (0, 1))

    def test_unlocked_fraction(self):
        tbh = TokenBatch(10000, 0, vesting_options=VestingOptions(3, 3))
        tb = TokenBatch(10000, 0)

        self. assertEqual(tbh.unlocked_fraction(), 0)
        tbh.update_age(3)
        self.assertEqual(tbh.unlocked_fraction(), 0)
        tbh.update_age(3)
        self.assertEqual(tbh.unlocked_fraction(), 0.5)

        self.assertEqual(tb.unlocked_fraction(), 1.0)

    def test_spend_vesting_only(self):
        tbh = TokenBatch(10000, 0, vesting_options=VestingOptions(3, 3))
        with self.assertRaises(Exception):
            tbh.spend(100)

        # Now that enough time has passed, spending the vested tokens should work.
        tbh.update_age(6)
        a = tbh.spend(5000)
        self.assertEqual(a, (10000, 5000, 0))

        tbh.update_age(3)
        with self.assertRaises(Exception):
            tbh.spend(6000)

    def test_spend_nonvesting_only(self):
        tb = TokenBatch(0, 10000)
        tb.spend(100)
        self.assertEqual(tb.total, 9900)

        tb.spend(2000)
        self.assertEqual(tb.total, 7900)

        with self.assertRaises(Exception):
            tb.spend(8000)

    def test_spend_vesting_and_nonvesting(self):
        # If I have 500 vesting and 500 nonvesting tokens, I should be able to
        # spend 750 after some vesting time.
        tb = TokenBatch(500, 500, vesting_options=VestingOptions(1, 1))
        tb.update_age(3)
        self.assertEqual(tb.spendable(), 875.0)

        a = tb.spend(750)
        self.assertEqual(a, (500, 250, 0))
        self.assertEqual(tb.spendable(), 125)

        # Long after the vesting period ends, I should be able to spend all my
        # tokens and not more.
        tb.update_age(100)
        with self.assertRaises(Exception):
            tb.spend(300)

        b = tb.spend(250)
        self.assertEqual(b, (500, 500, 0))


class CommonsTest(unittest.TestCase):
    def setUp(self):
        # 100,000 DAI invested for 1,000,000 tokens.
        self.desired_token_price = 0.1
        self.hatcher_contributions = [25000, 25000, 50000]
        self.token_batches, self.token_supply_initial = create_token_batches(
            self.hatcher_contributions, self.desired_token_price, 90)

        # Because of hatch_tribute, the collateral_pool is 0.7e6. This causes the token's post-hatch price to be 0.14.
        self.commons = Commons(
            sum(self.hatcher_contributions), self.token_supply_initial, hatch_tribute=0.3)

    def test_initialization(self):
        self.assertEqual(self.commons._collateral_pool, 70000)
        self.assertEqual(self.commons._funding_pool, 30000)
        self.assertEqual(self.commons._token_supply, self.token_supply_initial)

        self.assertEqual(self.commons.token_price(), 0.14)

    def test_burn_without_exit_tribute(self):
        old_token_supply = self.commons._token_supply
        old_collateral_pool = self.commons._collateral_pool

        money_returned, realized_price = self.commons.burn(50000)

        self.assertEqual(money_returned, 6825.0)
        self.assertEqual(realized_price, 0.1365)
        self.assertEqual(self.commons._token_supply, old_token_supply-50000)
        self.assertEqual(self.commons._collateral_pool,
                         old_collateral_pool-money_returned)
