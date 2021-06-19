"""
Parent classes for all instrument connections

Author: Bryce Carter
Date Created: 2021-05-24
"""

from abc import ABC, abstractmethod
from threading import RLock


class _Instrument(ABC):
    _open_instruments = set()

    def __init__(self, name):
        self.name = name
        self._atomic_lock = RLock()
        self._open()
        self._get_identity()

    def __del__(self):
        self._close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._close()

    def __str__(self):
        cls = self.__class__
        name = f'Name: {self.name}'
        location = f'Location: {self._location}'
        hw_identity = (f'HW: {self.manufacturer} '
                       f'{self.model_number} '
                       f'{self.serial_number}')
        sw_identity = f'SW: {self.software_version}'
        return f'{cls}\n{name}\n{location}\n{hw_identity}\n{sw_identity}'

    @abstractmethod
    def _write(self, data: str):
        """
        Abstract method for writing data to the instrument
        """
        pass

    @abstractmethod
    def _read(self) -> str:
        """
        Abstract method for reading data from the instrument
        Designed to read just a single response from the instrument
        """
        pass

    @abstractmethod
    def _get_identity(self):
        """
        Abstract method for collection the identifying information
        This method is responsible for populating the following properties:
            self.manufacturer
            self.model_number
            self.serial_number
            self.software_version
        """
        pass

    @abstractmethod
    def _open(self):
        """
        Open connection to the Instrument
        Also, store a reference to the instrument in _open_instruments to
        allow blocking exits before successful closing of the all instruments
        """
        _Instrument._open_instruments.add(self)

    @abstractmethod
    def _close(self):
        """
        Close connection to the instrument
        Also, remove the reference to this instance from _open_instruments to
        unblock the exiting of the program
        """
        if self in _Instrument._open_instruments:
            _Instrument._open_instruments.remove(self)

    def close(self):
        """
        Public method for closing the connection to this instrument
        """
        self._close()

    @abstractmethod
    def send(self, cmd: str):
        """
        Abstract method for sending commands to the instrument
        """
        pass

    @abstractmethod
    def query(self, cmd: str) -> str:
        """
        Abstract method for running a query that is expected to return a result
        """
        pass

    @abstractmethod
    def reset(self):
        """
        Abstract method for resetting the instrument to its default settings
        """
        pass
