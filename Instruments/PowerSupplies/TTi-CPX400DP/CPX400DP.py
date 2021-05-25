r"""
Author: Bryce Carter
Date Created: 2021-05-24
"""

import serial


class instrument():
    def __init__(self, name):
        self.name = name


class power_supply():
    def __init__(self, name):
        super().__init__(name)


class cpx400dp(power_supply):
    def __init__(self, name):
        super().__init__(name)
