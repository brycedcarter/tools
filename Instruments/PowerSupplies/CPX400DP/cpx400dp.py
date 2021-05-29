"""
Driver for interfacing with CPX400DP power supply.

Author: Bryce Carter
Date Created: 2021-05-24
"""

import serial
import logging
import os

from instruments.powersupplies import (_PowerSupply,
                                       _PowerSupplyChannel)

logger = logging.getLogger(__name__)


class CPX400DPError(Exception):
    """
    Error class for CPX400DP
    """
    pass


class CPX400DPChannel(_PowerSupplyChannel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # enable limit reporting for this channel
        self.instrument.send(f'LSE{self.index} 255')
        assert int(self.instrument.query(f'LSE{self.index}?')) == 255

    @property
    def voltage(self) -> float:
        """The current output voltage of the CPX400DP channel"""

        result = self.instrument.query(f'V{self.index}O?')
        voltage = float(result.split('V')[0])
        return voltage

    @property
    def current(self) -> float:
        """The current output current of the CPX400DP channel"""

        result = self.instrument.query(f'I{self.index}O?')
        current = float(result.split('A')[0])
        return current

    @property
    def voltage_setpoint(self) -> float:
        """The currently set max voltage of the CPX400DP channel"""

        result = self.instrument.query(f'V{self.index}?')
        voltage = float(result.split(' ')[1])
        return voltage

    @voltage_setpoint.setter
    def voltage_setpoint(self, value: float):
        """Sets the max voltage of the CPX400DP channel"""

        cmd = f'V{self.index} {value:.3f}'
        self.instrument.send(cmd)

    @property
    def current_setpoint(self) -> float:
        """The currently set max current of the CPX400DP channel"""

        result = self.instrument.query(f'I{self.index}?')
        current = float(result.split(' ')[1])
        return current

    @current_setpoint.setter
    def current_setpoint(self, value: float):
        """Set the max current of the CPX400DP channel"""

        cmd = f'I{self.index} {value:.3f}'
        self.instrument.send(cmd)

    @property
    def ovp(self) -> float:
        """The over voltage protection limit for this CPX400DP channel"""

        result = self.instrument.query(f'OVP{self.index}?')
        ovp = float(result.split(' ')[1])
        return ovp

    @ovp.setter
    def ovp(self, value: float):
        """Set the over votlage protection limit for this CPX400DP channel"""

        cmd = f'OVP{self.index} {value:.3f}'
        self.instrument.send(cmd)

    @property
    def ocp(self) -> float:
        """The over current protection limit for this CPX400DP channel"""

        result = self.instrument.query(f'OCP{self.index}?')
        ocp = float(result.split(' ')[1])
        return ocp

    @ocp.setter
    def ocp(self, value: float):
        """Set the over current protection limit for this CPX400DP channel"""

        cmd = f'OCP{self.index} {value:.3f}'
        self.instrument.send(cmd)

    @property
    def on(self) -> bool:
        """Indicates the state of the output of this CPX400DP channel"""

        result = self.instrument.query(f'OP{self.index}?')
        on = bool(int(result.split(' ')[1]))
        return on

    def output_on(self):
        """Turn the this CPX400DP channel on"""

        cmd = f'OP{self.index} 1'
        self.instrument.send(cmd)

    def output_off(self):
        """Turn the this CPX400DP channel off"""

        cmd = f'OP{self.index} 0'
        self.instrument.send(cmd)


class CPX400DP(_PowerSupply):
    def __init__(self, name, location):
        self._location = location
        assert os.path.exists(self._location)
        self.connection = None

        super().__init__(name)

        # enable events in the status byte register and in hte event status
        # register
        self.send('*SRE 255')
        assert int(self.query('*SRE?')) == 255
        self.send('*ESE 255')
        assert int(self.query('*ESE?')) == 255

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
                                        xonxoff=True,
                                        timeout=1)
        self._channels.append(CPX400DPChannel(self, 1))
        self._channels.append(CPX400DPChannel(self, 2))

    def _close(self):
        """Close the serial connection to the CPX400DP"""

        if self.connection is not None:
            self.connection.reset_input_buffer()
            self.connection.reset_output_buffer()
            self.connection.close()

    def _write(self, data: str):
        """Send data over the serial interface to the CPX400DP"""

        self.connection.write(data.encode('utf-8'))

    def _read(self) -> str:
        """
        Read from the serial connection to the CPX400DP unit a CRLF is seen.
        This will be one reponse from the CPX400DP
        """
        result = self.connection.read_until(b'\r\n').decode('utf-8')
        if result == '':
            raise TimeoutError('Did not recieve any response from CPX400DP')

        return result

    def _get_identity(self):
        """Read the power supply details and stores them as properties"""

        identity = self.query('*IDN?').split(',')
        self.manufacturer = identity[0]
        self.model_number = identity[1]
        self.serial_number = identity[2]
        self.software_verison = identity[3]

    def send(self, cmd: str):
        """Sends a command to the CPX400DP and then checks that status"""

        self._write(cmd+'\n')

        self._check_status()

    def query(self, cmd: str) -> str:
        """
        Sends a command to the CPX400DP and then waits for a response.
        Also checks the status to ensure that no errors occurred
        """

        # first check that the input buffer is empty and clear it if not
        if self.connection.in_waiting > 0:
            logger.warning('Flushing unread content from the input buffer')
            self.connection.reset_input_buffer()

        self._write(cmd+'\n')
        try:
            response = self._read()
        except TimeoutError as e:
            # Reading did not receive expected message from device.
            # Lets check the status for a better idea of the error.
            self._check_status()
            raise e

        return response

    def reset(self):
        """Reset the CPX400DP to its default state"""

        self.send('*RST')

    @property
    def ch1(self) -> CPX400DPChannel:
        """Annotating with correct type hinting"""
        return super().ch1

    @property
    def ch2(self) -> CPX400DPChannel:
        """Annotating with correct type hinting"""
        return super().ch2

    def _check_status(self):
        """
        Check the status registers and raise errors if needed
        Status registers will be cleared by reading them

        NOTE: this functionallity is not combined with the query() function
        so that query can check the status a recursion
        """
        # first check that the input buffer is empty
        if self.connection.in_waiting > 0:
            logger.warning('Flushing unread content from the input buffer')
            self.connection.reset_input_buffer()

        self._write('*STB?'+'\n')
        stb = int(self._read())
        self._process_status_byte_register(stb)

    def _clear_status(self):
        """Clear out all of the status registers"""

        self.send('*CLS')

    def _process_status_byte_register(self, stb: int):
        """
        Process the contents from the status byte register and if needed
        read from the more detailed registers
        """
        if 0 <= stb <= 255:
            if stb & 0x1:
                lsr = int(self.query('LSR1?'))
                self._process_limit_event_register(lsr, 1)
            if stb & 0x2:
                lsr = int(self.query('LSR2?'))
                self._process_limit_event_register(lsr, 2)
            if stb & 0x4:
                pass  # unused bit
            if stb & 0x8:
                pass  # unused bit
            if stb & 0x10:
                pass  # no handling needed for message available
            if stb & 0x20:
                esr = int(self.query('*ESR?'))
                logging.warning(f'EVENT STATUS: '
                                f'{self._process_event_status_register(esr)}')
            if stb & 0x40:
                pass  # do nothing for RQS/MSS
            if stb & 0x80:
                pass  # unused bit
        else:
            raise CPX400DPError(f'Unknown value for status byte register: '
                                f'{stb}')

    def _process_event_status_register(self, esr) -> str:
        """
        Process the contents of the event status register.
        Return a meaningful string representation of the status
        (or raise an exception if needed)
        """
        if 0 <= esr <= 255:
            if esr & 0x1:
                pass  # do nothing for "operation complete"
            if esr & 0x2:
                pass  # unused bit
            if esr & 0x4:
                raise CPX400DPError('Query error: '
                                    '(documentation seems incomplete)')
            if esr & 0x8:
                raise CPX400DPError('Verify timeout error')
            if esr & 0x10:
                eer = int(self.query('EER?'))
                self._process_execution_error(eer)
            if esr & 0x20:
                raise CPX400DPError('Command parsing error')
            if esr & 0x40:
                pass  # unused bit
            if esr & 0x80:
                pass  # do nothing for "power on event"
        else:
            raise CPX400DPError(f'Unknown value for limit event register: '
                                f'{esr}')

    def _process_limit_event_register(self, lsr: int, ch: int):
        """
        Process the contents from the limit event status register.
        Return a string representation of the status
        """
        if 0 <= lsr <= 255:
            if lsr & 0x1:
                logger.warning(f'CH{ch} LIMIT - '
                               f'output entered voltage limit mode')
            if lsr & 0x2:
                logger.warning(f'CH{ch} LIMIT - '
                               f'output entered current limit mode')
            if lsr & 0x4:
                logger.warning(f'CH{ch} LIMIT - '
                               f'output over voltage trip occured')
            if lsr & 0x8:
                logger.warning(f'CH{ch} LIMIT - '
                               f'output over current trip occured')
            if lsr & 0x10:
                logger.warning(f'CH{ch} LIMIT - '
                               f'output entered power limit mode '
                               f'(unregulated)')
            if lsr & 0x20:
                pass  # unused bit
            if lsr & 0x40:
                logger.warning(f'CH{ch} LIMIT - '
                               f'trip occured (frontpanel reset required)')
            if lsr & 0x80:
                pass  # unused bit
        else:
            raise CPX400DPError(f'Unknown value for limit event register: '
                                f'{lsr}')

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
                    100: '100: Range error. Input value invlaid',
                    101: '101: Corrupted setup date',
                    102: '102: Missing setup data',
                    103: '103: No second output',
                    104: '104: Command not valid with output on',
                    200: '200: Read only, interface is locked'
                    }
        raise CPX400DPError(messages[eer])
