from decimal import Decimal, getcontext
from typing import Union
from unittest import TestCase


class BTCAmount:
    EXCHANGE = 10 ** 8

    def __init__(self, amount: Union[float, str, int]):
        # Set decimal package config
        getcontext().prec = 8
        if isinstance(amount, str):
            try:
                # case: string involving int
                self.sat_amount = int(amount)
            except ValueError:
                # case: string involving float
                self.sat_amount = int(Decimal(amount) * BTCAmount.EXCHANGE)
        elif isinstance(amount, float) or isinstance(amount, str):
            # amount is considered to be in "satoshi"
            self.sat_amount = int(Decimal(amount) * BTCAmount.EXCHANGE)
        elif isinstance(amount, int):
            # amount is considered to be in "btc"
            self.sat_amount = amount
        else:
            raise Exception("Not allowed amount type: {}".format(type(amount)))

    def __add__(self, other):
        return BTCAmount(self.sat_amount + other.sat_amount)

    def __sub__(self, other):
        return BTCAmount(self.sat_amount - other.sat_amount)

    def __gt__(self, other):
        return self.sat_amount > other.sat_amount

    def __lt__(self, other):
        return self.sat_amount < other.sat_amount

    def __eq__(self, other):
        return self.sat_amount == other.sat_amount

    def __str__(self):
        pre_dot = self.sat_amount // BTCAmount.EXCHANGE
        sur_dot = "{}".format(str(self.sat_amount % BTCAmount.EXCHANGE).zfill(8))
        return "{}.{}".format(pre_dot, sur_dot)

    def scalar_mul(self, scalar: int):
        """ multiplication between BTCAmount and Integer"""
        return BTCAmount(self.sat_amount * scalar)

    def to_fixed_size_bytes(self, length: int, byteorder: str):
        return self.sat_amount.to_bytes(length, byteorder)

    @property
    def to_sat(self) -> int:
        return self.sat_amount

    @property
    def to_btc(self) -> str:
        pre_dot = self.sat_amount // BTCAmount.EXCHANGE
        sur_dot = "{}".format(str(self.sat_amount % BTCAmount.EXCHANGE).zfill(8))
        return "{}.{}".format(pre_dot, sur_dot)


class BTCAmountTest(TestCase):
    def test_arithmetic(self):
        dot_one: BTCAmount = BTCAmount(0.1)
        dot_three: BTCAmount = BTCAmount("0.3")

        expected = BTCAmount(0)
        actual = dot_one + dot_one + dot_one - dot_three

        self.assertEqual(expected, actual)
