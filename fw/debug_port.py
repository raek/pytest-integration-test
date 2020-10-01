import logging
from queue import Queue
import time
import threading

import serial

from fw.stream import Dispatcher, Listener


dp_logger = logging.getLogger(__name__ + ".DebugPort")


class DebugPort:
    """Line based communication using a serial port"""
    def __init__(self, device, baudrate):
        self._logger = logging.getLogger(__name__ + "." + self.__class__.__name__)
        self._logger.debug("Init DebugPort")
        # Workaround for incompatibility between Linux DTR handling and Arduino usage of DTR for reset
        import os
        os.system(f"stty -F {device} -hupcl")
        self._serial = serial.Serial()
        self._serial.port = device
        self._serial.baudrate = baudrate
        self._serial.timeout = 1 # timeout for reads
        self._serial.open()
        self._incoming_line_dispatcher = Dispatcher()
        self._background_reader = _BackgroundReader(self._serial, self._incoming_line_dispatcher)

    def __enter__(self):
        self._logger.debug("enter")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._logger.debug("exit")
        self._serial.close()
        self._background_reader.stop()
        return False

    def send_line(self, line):
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


class _BackgroundReader:
    """Transfer lines from OS buffer to dispatcher

    If the OS buffer is full, then characters will be dropped.
    """
    def __init__(self, serial, incoming_line_dispatcher):
        self._logger = logging.getLogger(__name__ + "." + self.__class__.__name__)
        self._serial = serial
        self._incoming_line_dispatcher = incoming_line_dispatcher
        self._thread = threading.Thread(target=self._thread_main)
        self._thread.daemon = True
        self._thread.start()

    def _thread_main(self):
        self._logger.debug("Begin")
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
                self._logger.error("Error in _BackgroundReader thread", exc_info=e)
            else:
                # About to shut down. Error probably caused by that.
                pass
        self._logger.debug("End")

    def stop(self):
        self._thread.join()
