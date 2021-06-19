"""
Interfaces for managing connections to instruments

Author: Bryce Carter
Date Created: 2021-06-17
"""

import serial
from abc import ABC, abstractmethod
from threading import RLock
from instruments import atomic_operation


class Connection(ABC):
    """
    Base class for representing all type of connections to instruments

    connections are intended to be thread safe by holding locks while
    performing IO operations

    Also, any internal data structures used to store information about the
    connection should be implemented in a thread safe fashion
    """

    def __init__(self):
        self._atomic_lock = RLock()

    @abstractmethod
    def close():
        """Abstract method for closing the connection"""

    @abstractmethod
    def is_open(self) -> bool:
        """Abstract method to determine if the connection is open or not"""

    @abstractmethod
    def flush(self) -> (int, int):
        """
        Abstract method to flush all IO buffers for the connection

        Returns:
            in, out - number of input and output bytes (or messages)
                    that were flushed
        """
        """Abstract method to flush all IO buffers for the connection"""

    @abstractmethod
    def send(self, data: str) -> None:
        """
        Abstract method for sending data over the connection

        Arguments:
            data: should be a string containing only the message to be sent
                  including any terminating characters or extra formatting

        Returns:
            None
        """

    @abstractmethod
    def receive(self) -> str:
        """
        Abstract method for sending data over the connection

        Arguments:
            None

        Returns:
            string containing the response from the instrument. No formatting
            is performed besides conversion to a string
        """


class SerialConnection(Connection):
    """
    Thread safe connection using a serial link such as RS232 or TTL UART
    """

    def __init__(self, device_path: str, settings: dict = None):
        """
        Initialize the serial connection.

        Arguments:
            device_path - Path to the serial device that should be opened
            settings - A dict containing any of the following keys (any
                       missing keys will use the defaults shown here):
                        'baudrate': 9600,
                        'bytesize': 8,
                        'parity': 'N',
                        'stopbits': 1,
                        'xonxoff': False,
                        'dsrdtr': False,
                        'rtscts': False,
                        'timeout': None,
                        'write_timeout': None,
                        'inter_byte_timeout': None
                        'line_termination': b'\\r\\n'
        """
        super().__init__()
        self._serial = serial.Serial(device_path)

        if settings is not None:
            self.update_settings(settings)

    def update_settings(self, settings: dict):
        """Update the settings for the serial connection with a dict"""
        if settings.get('line_termination') is not None:
            self._line_term = settings.pop('line_termination')
        else:
            self._line_term = b'\r\n'

        self._serial.apply_settings(settings)

    def close(self):
        """Closes the serial connection"""
        self._serial.reset_input_buffer()
        self._serial.reset_output_buffer()
        self._serial.close()

    @property
    def is_open(self) -> bool:
        """Method to determine if the serial connection is open or not"""
        return self._serial.is_open

    def flush(self) -> (int, int):
        """
        Flush the input and output buffers of the serial connection

        Returns:
            in, out - number of input and output bytes that were flushed
        """
        in_bytes = self._serial.in_waiting
        out_bytes = self._serial.out_waiting
        self._serial.reset_input_buffer()
        self._serial.reset_output_buffer()
        return in_bytes, out_bytes

    @atomic_operation
    def get_settings(self) -> dict:
        """Update the settings for the serial connection with a dict"""
        return self._serial.get_settings()

    @atomic_operation
    def send(self, data: str) -> None:
        """
        Send data over the serial connection

        Arguments:
            data: should be a string containing only the message to be sent
                  including any terminating characters or extra formatting

        Returns:
            None
        """
        msg = data.encode('utf-8')
        self._serial.write(msg)

    @atomic_operation
    def receive(self) -> str:
        """
        Receive data from the the serial connection

        Arguments:
            None

        Returns:
            string containing the response from the instrument. No formatting
            is performed besides conversion to a string
        """

        result = self._serial.read_until(self._line_term).decode('utf-8')
        return result
