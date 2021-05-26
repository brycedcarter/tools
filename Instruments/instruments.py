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

    def __del__(self):
        self._close()
    
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



