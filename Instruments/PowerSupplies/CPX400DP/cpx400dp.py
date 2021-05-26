r"""
Author: Bryce Carter
Date Created: 2021-05-24
"""

import serial
import logging

from Instruments.PowerSupplies.power_supplies import PowerSupply, PowerSupplyChannel

logger = logging.getLogger(__name__)


class CPX400DPError(Exception):
    """
    Error class for CPX400DP
    """
    pass
        

class CPX400DPChannel(PowerSupplyChannel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def voltage(self) -> float:
        """
        The current voltage setting of the CPX400DP
        """
        result = self.instrument.query(f'V{self.index}?')
        voltage = float(result.split(' ')[1])
        return voltage
    
    @voltage.setter
    def voltage(self, value: float):
        """
        Set the output voltage of the CPX400DP
        """
        cmd = f'V{self.index} {value:.3f}' 
        self.instrument.send(cmd)


class CPX400DP(PowerSupply):
    def __init__(self, name, location):
        self._location = location
        self.connection = None
        super().__init__(name)

    def _open(self):
        """
        Open serial connection to the CPX400DP

        From CPX400DP user mannual:
            Baud=9600
            Start=1
            Stop=1
            Data=8
            Parity=None

            XOFF @ ~200 chars in 256 deep queue
            XON @ ~100 chars free
        """
        self.connection = serial.Serial(self._location,
                                       baudrate=9600,
                                       bytesize=serial.EIGHTBITS,
                                       parity=serial.PARITY_NONE,
                                       stopbits=serial.STOPBITS_ONE,
                                       xonxoff=True)
        self._channels.append(CPX400DPChannel(self,1))
        self._channels.append(CPX400DPChannel(self,2))
        

    def _close(self):
        """
        Close the serial connection to the CPX400DP
        """
        self.connection.reset_input_buffer()
        self.connection.reset_output_buffer()
        self.connection.close()

    def _write(self, data: str):
        """
        Send data over the serial interface to the CPX400DP
        """
        self.connection.write(data.encode('utf-8'))

    def _read(self) -> str:
        """
        Read from the serial connection to the CPX400DP unit a CRLF is seen.
        This will be one reponse from the CPX400DP
        """
        return self.connection.read_until(b'\r\n').decode('utf-8')

    def send(self, cmd: str):
        """
        Sends a command to the CPX400DP and then checks that status to ensure that no
        errors occurred
        """
        self._write(cmd+'\n')
        stb = int(self.query('*STB?'))
        self._process_status_byte_register(stb)

    def query(self, cmd: str) -> str:
        """
        Sends a command to the CPX400DP and then waits for a response and finally 
        checks that status to ensure that no errors occurred
        """
        # first check that the input buffer is empty
        if self.connection.in_waiting > 0:
            logger.warning('Flushing unread content from the input buffer')
            self.connection.reset_input_buffer()

        self._write(cmd+'\n')
        response = self._read()

        self._write('*STB?'+'\n')
        stb = int(self._read())
        self._process_status_byte_register(stb)
        
        return response

    def _process_status_byte_register(self, stb: int):
        """
        Process the contents from the status byte register and if needed
        read from the more detailed registers
        """
        if stb & 0x1:
            lsr = int(self.query('LSR1?'))
            logging.warning(f'CH1 LIMITS: {self._process_limit_event_register(lsr)}')
        elif stb & 0x2:
            lsr = int(self.query('LSR2?'))
            logging.warning(f'CH2 LIMITS: {self._process_limit_event_register(lsr)}')
        elif stb & 0x4:
            pass # unused bit 
        elif stb & 0x8:
            pass # unused bit 
        elif stb & 0x10:
            pass # no handling needed for message available 
        elif stb & 0x20:
            esr = int(self.query('*ESR?'))
            logging.warning(f'EVENT STATUS: {self._process_event_status_register(esr)}')

    def _process_event_status_register(self, esr) -> str:
        """
        Process the contents of the event status register and return a 
        meaningful string representation of the status (or raise an exception if needed)
        """
        if esr & 0x1:
            return 'operation complete'
        elif esr & 0x2:
            pass # unused bit
        elif esr & 0x4:
            raise CPX400DPError('Query error: (documentation seems incomplete)')
        elif esr & 0x8:
            raise CPX400DPError('Verify timeout error')
        elif esr & 0x10:
            eer = int(self.query('EER?'))
            self._process_execution_error(eer)
        elif esr & 0x20:
            raise CPX400DPError('Command parsing error') 
        elif esr & 0x40:
            pass # unused bit
        elif esr & 0x80:
            return 'power on event'
        raise CPX400DPError(f'Unknown value for limit event register: {lsr}')

    def _process_limit_event_register(self, lsr: int) -> str:
        """
        Process the contents from the limit event status register and return 
        a string representation of the status
        """
        if lsr & 0x1:
            return 'output entered voltage limit mode'
        elif lsr & 0x2:
            return 'output entered current limit mode'
        elif lsr & 0x4:
            return 'output over voltage trip occured'
        elif lsr & 0x8:
            return 'output over current trip occured'
        elif lsr & 0x10:
            return 'outputnt entered power limit mode (unregulated)'
        elif lsr & 0x20:
            pass # unused bit 
        elif lsr & 0x40:
            return 'trip occured (frontpanel reset required)'
        elif lsr & 0x80:
            pass # unused bit 
        raise CPX400DPError(f'Unknown value for limit event register: {lsr}')

    def _process_execution_error(self, eer: int):
        """
        Raise the correct exception based on the contents of the EER register
        """
        messages = {0: '0: No error encountered',
                    1: '1: Internal hardware error',
                    2: '2: Internal hardware error',
                    3: '3: Internal hardware error',
                    4: '4: Internal hardware error',
                    5: '5: Internal hardware error',
                    6: '6: Internal hardware error',
                    7: '7: Internal hardware error',
                    8: '8:Internal hardware error',
                    9: '9: Internal hardware error',
                    100: '100: Range error. The numeric value sent is not allowed',
                    101: '101: Corrupted setup date',
                    102: '102: Missing setup data',
                    103: '103: No second output',
                    104: '104: Command not valid with output on',
                    200: '200: Read only, interface is locked'
                   }
        
        raise CPX400DPError(messages[eer])
