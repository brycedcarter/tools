r"""
Parent classes for all insturment connections

Author: Bryce Carter
Date Created: 2021-05-24
"""

from abc import ABC, abstractmethod

class Instrument():
    def __init__(self, name):
        self.name = name
        self._open()
        self._get_identity()

    def __del__(self):
        self._close()

    def __repr__(self):
        cls = self.__class__
        name = f'Name: {self.name}'
        location = f'Location: {self._location}'
        hw_identity = f'HW: {self.manufacturer} {self.model_number} {self.serial_number}'
        sw_identity = f'SW: {self.software_verison}'
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
        Abstract mehod for reading data from the instrument
        Designed to read just a single response from the instrument
        """
        pass
    
    @abstractmethod
    def _get_identity(self):
        """
        Abstract method for collection the identifiying information from the instrument
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
        """
        pass

    @abstractmethod
    def _close(self):
        """
        Close connection to the instrument
        """
        pass

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
        Abstract method for resetting the istrument to its default settings
        """
        pass
