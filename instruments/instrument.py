"""
Parent classes for all instrument connections

Author: Bryce Carter
Date Created: 2021-05-24
"""

import weakref
from abc import ABC, abstractmethod
from threading import RLock


class _Instrument(ABC):
    """
    Abstract base class representing an instrument such as a power supply or a
    scope
    """
    _open_instruments = weakref.WeakSet()
    _location = 'UNKNOWN'
    manufacturer = 'UNKNOWN'
    model_number = 'UNKNOWN'
    serial_number = 'UNKNOWN'
    software_version = 'UNKNOWN'

    def __init__(self, name):
        self.name = name
        self._atomic_lock = RLock()
        self._open_concrete()
        self._get_identity()

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def __str__(self):
        cls = self.__class__
        name = f'Name: {self.name}'
        location = f'Location: {self._location}'
        hw_identity = (f'HW: {self.manufacturer} '
                       f'{self.model_number} '
                       f'{self.serial_number}')
        sw_identity = f'SW: {self.software_version}'
        return f'{cls}\n{name}\n{location}\n{hw_identity}\n{sw_identity}'

    def _open_concrete(self):
        """
        Concrete opener for instrument connections

        This exists to allow instrument to be registered in the class-global
        register of "opened instruments" so that they can be safely shut down

        Do not override this method in a subclass. Instead, implement _open()
        """
        _Instrument._open_instruments.add(self)
        self._open()

    @abstractmethod
    def _write(self, data: str):
        """
        Abstract method for writing data to the instrument
        """

    @abstractmethod
    def _read(self) -> str:
        """
        Abstract method for reading data from the instrument
        Designed to read just a single response from the instrument
        """

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

    @abstractmethod
    def _open(self):
        """
        Abstract method for opening the connection to the instrument
        """

    @abstractmethod
    def _close(self):
        """
        Abstract method for closing the connection to the instrument
        """

    @abstractmethod
    def send(self, cmd: str):
        """
        Abstract method for sending commands to the instrument
        """

    @abstractmethod
    def query(self, cmd: str) -> str:
        """
        Abstract method for running a query that is expected to return a result
        """

    @abstractmethod
    def reset(self):
        """
        Abstract method for resetting the instrument to its default settings
        """

    def close(self):
        """
        Public method for closing the connection to this instrument
        Also, remove the reference to this instance from _open_instruments to
        unblock the exiting of the program

        All efforts to close the connection (even those from within this class)
        should call this method directly rather than calling _close()

        Do not override this method in a subclass. Instead, implement _close()
        """
        self._close()
        if self in _Instrument._open_instruments:
            _Instrument._open_instruments.remove(self)
