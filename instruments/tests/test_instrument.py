"""
Filename: test_instrument.py

Unit tests for the Instrument class and its methods

Author: Bryce Carter
Date Created: 2021-06-20
"""

import pdb
import gc
import unittest
from threading import RLock
from unittest.mock import patch, call

from instruments import _Instrument


class TestInstruments(unittest.TestCase):
    instrument_name = 'Test Instrument'


    @patch("instruments._Instrument.__abstractmethods__", set())
    def test_init(self):
        instrument = _Instrument(self.instrument_name)

        self.assertEqual(instrument.name, self.instrument_name)
        self.assertIsInstance(instrument._atomic_lock, RLock().__class__)
        self.assertIn(instrument, _Instrument._open_instruments)
        del instrument

    @patch("instruments._Instrument.__abstractmethods__", set())
    def test_string(self):
        expected_string = (f'{_Instrument}\n'
                           f'Name: Test Instrument\n'
                           f'Location: UNKNOWN\n'
                           f'HW: UNKNOWN UNKNOWN UNKNOWN\n'
                           f'SW: UNKNOWN')
        instrument = _Instrument(self.instrument_name)

        self.assertEqual(str(instrument), expected_string)
        del instrument

    @patch("instruments._Instrument.__abstractmethods__", set())
    def test_context_management(self):
        # check that open_concrete and close is called correctly
        with patch('instruments._Instrument.close') as close_method:
            with patch('instruments._Instrument._open_concrete') \
                    as open_method:
                with _Instrument(self.instrument_name) as instrument:
                    pass
                del instrument
                close_method.assert_has_calls([call(), call()])
                open_method.assert_called_once()

        # check that the abstract _open and _close are called correctly
        with patch('instruments._Instrument._close') as close_method:
            with patch('instruments._Instrument._open') \
                    as open_method:
                with _Instrument(self.instrument_name) as instrument:
                    pass
                del instrument
                close_method.assert_has_calls([call(), call()])
                open_method.assert_called_once()

    @patch("instruments._Instrument.__abstractmethods__", set())
    def test_open_instruments(self):
        # make sure context manager removes reference
        with _Instrument(self.instrument_name) as instrument1:
            self.assertSetEqual(set([instrument1]),
                                _Instrument._open_instruments)
        self.assertSetEqual(set(), _Instrument._open_instruments)

        # make gc removes reference
        instrument1._open_concrete()
        self.assertSetEqual(set([instrument1]),
                            _Instrument._open_instruments)
        del instrument1
        self.assertSetEqual(set(), _Instrument._open_instruments)
