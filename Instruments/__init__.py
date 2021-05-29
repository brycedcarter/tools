"""
A package for interfacing with various types of lab instruments
"""
from .instrument import _Instrument
from .powersupplies.cpx400dp.cpx400dp import CPX400DP, CPX400DPError
