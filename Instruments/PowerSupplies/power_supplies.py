
r"""
Parent classes for all power supplies connections

Author: Bryce Carter
Date Created: 2021-05-24
"""

from abc import ABC, abstractmethod
from Instruments.instruments import Instrument

class PowerSupplyChannel(ABC):
    """
    A class to control a single channel of a power supply
    """
    def __init__(self, instrument: Instrument, index: int):
        self.instrument = instrument
        self.index = index
    
    @property 
    @abstractmethod
    def voltage(self) -> float:
        """
        The currently set voltage of the supply
        """
        pass

    @voltage.setter
    @abstractmethod
    def voltage(self, value: float):
        """
        Set the output voltage of the supply
        """
        pass



class PowerSupply(Instrument):
    """
    A class to interface with power supplies
    """

    def __init__(self, name):
        self._channels=[]
        super().__init__(name)

    @property 
    def channel_count(self):
        """
        Get the number of channels present on this power supply
        """
        return len(self.channels)
    
    @property
    def ch1(self):
        """
        Access to first channel on power supply
        """
        if len(self._channels) >= 1:
            return self._channels[0]
        else:
            raise AttributeError(f'{self.name} does not have a "ch1"')
    
    @property
    def ch2(self):
        """
        Access to second channel on power supply
        """
        if len(self._channels) >= 2:
            return self._channels[1]
        else:
            raise AttributeError(f'{self.name} does not have a "ch2"')

    @property
    def ch3(self):
        """
        Access to third channel on power supply
        """
        if len(self._channels) >= 3:
            return self._channels[2]
        else:
            raise AttributeError(f'{self.name} does not have a "ch3"')
    
    @property
    def ch4(self):
        """
        Access to fourth channel on power supply
        """
        if len(self._channels) >= 4:
            return self._channels[3]
        else:
            raise AttributeError(f'{self.name} does not have a "ch4"')
