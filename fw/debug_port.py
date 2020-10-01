from contextlib import ExitStack
import logging
from queue import Queue
import time
import threading

import serial

from fw.interface import Port
from fw.stream import Dispatcher, Listener
from fw.worker_thread import worker_thread


class DebugPort(Port, ExitStack):
    """Line based communication using a serial port

    This class is a context manager.
    """
    def __init__(self, device, baudrate):
        super().__init__()
        self._logger = logging.getLogger(__name__ + "." + self.__class__.__name__)
        self._logger.debug("init")
        self.callback(self._logger.debug, "close")

        # Workaround for incompatibility between Linux DTR handling and
        # Arduino usage of DTR for reset
        import os
        os.system(f"stty -F {device} -hupcl")

        self._incoming_line_dispatcher = Dispatcher()

        # Open port using pyserial
        self._serial = serial.Serial()
        self._serial.port = device
        self._serial.baudrate = baudrate
        self._serial.timeout = 1  # timeout for reads
        self._serial.open()

        # Start background worker thread and make sure it and the socket are
        # torn down at exit
        self.enter_context(worker_thread(worker_function=self._receive_lines,
                                         stop_function=self._serial.close))

    def _close(self):
        self._logger.debug("close")
        self._serial.close()

    def _receive_lines(self):
        self._logger.debug("worker thread begin")
        try:
            while True:
                byteline = self._serial.readline()
                if byteline is None:
                    return
                elif byteline:
                    line = byteline.decode("utf8").strip()
                    self._logger.info("<== " + line)
                    self._incoming_line_dispatcher.dispatch(line)
        except Exception as e:
            if self._serial.is_open:
                raise e
            else:
                # About to shut down. Error probably caused by that.
                pass
        self._logger.debug("worker thread end")

    def send(self, line):
        self._logger.info("==> " + line)
        self._serial.write(line.encode("utf8") + b"\n")

    def toggle_dtr(self):
        self._logger.debug("toggle_dtr")
        self._serial.dtr = False
        time.sleep(0.1)
        self._serial.dtr = True

    def listen(self):
        self._logger.debug("listen")
        return Listener(self._incoming_line_dispatcher)
