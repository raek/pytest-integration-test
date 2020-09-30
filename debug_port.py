import logging
from queue import Queue
import time
import threading

import serial


dp_logger = logging.getLogger(__name__ + ".DebugPort")


class DebugPort():
    """Line based communication using a serial port"""
    def __init__(self, device, baudrate):
        self._logger = logging.getLogger(__name__ + "." + self.__class__.__name__)
        self._logger.debug("Init DebugPort")
        self._serial = serial.Serial()
        self._serial.port = device
        self._serial.baudrate = baudrate
        self._serial.timeout = 1 # timeout for reads
        self._serial.open()
        self._dispatcher = _LineDispatcher()
        self._background_reader = _BackgroundReader(self._serial, self._dispatcher)

    def __enter__(self):
        self._logger.debug("enter")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._logger.debug("exit")
        self._serial.close()
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
        return _LineListener(self._dispatcher)


class _BackgroundReader():
    """Transfer lines from OS buffer to dispatcher
    
    If the OS buffer is full, then characters will be dropped.
    """
    def __init__(self, serial, dispatcher):
        self._logger = logging.getLogger(__name__ + "." + self.__class__.__name__)
        self._serial = serial
        self._dispatcher = dispatcher
        self._thread = threading.Thread(target=self._thread_main)
        self._thread.daemon = True
        self._thread.start()

    def _thread_main(self):
        self._logger.debug("Begin")
        try:
            while True:
                byteline = self._serial.readline().strip()
                if byteline:
                    line = byteline.decode("utf8")
                    self._logger.info("<== " + line)
                    self._dispatcher.dispatch(line)
        except Exception as e:
            self._logger.error("Error in _BackgroundReader thread", exc_info=e)
        self._logger.debug("End")


class _LineDispatcher():
    """Allow multiple consumers of lines"""
    def __init__(self):
        self._listener_queues = {}

    def dispatch(self, line):
        """Distribute line to each listener"""
        for queue in self._listener_queues.values():
            queue.put(line)

    def add_listener(self, listener):
        """Register a new listener
        
        Lines will appear in the return queue.
        """
        queue = Queue()
        self._listener_queues[listener] = queue
        return queue

    def remove_listener(self, listener):
        """Stop receiving lines"""
        del self._listener_queues[listener]


class LineError(Exception):
    pass


class _LineListener():
    """Context manager that receives lines during its scope"""
    def __init__(self, dispatcher):
        self._logger = logging.getLogger(__name__ + "." + self.__class__.__name__)
        self._dispatcher = dispatcher
        self._queue = None

    def __enter__(self):
        self._logger.debug("enter")
        self._queue = self._dispatcher.add_listener(self)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._logger.debug("exit")
        self._dispatcher.remove_listener(self)
        self._queue = None
        return False

    def _next(self):
        assert self._queue is not None, "Listener not registered"
        return self._queue.get()

    def next(self):
        line = self._next()
        self._logger.debug("next: " + line)
        return line

    def expect_next(self, expected_line):
        self._logger.debug("expect_next: " + expected_line)
        actual_line = self._next()
        if actual_line != expected_line:
            raise LineError(f'Expected line "{expected_line}", got "{actual_line}"')

    def skip_until(self, expected_line):
        self._logger.debug("skip_until: " + expected_line)
        skipped = 0
        while True:
            line = self._next()
            if line == expected_line:
                self._logger.debug(f"skipped {skipped} lines")
                return
            else:
                skipped += 1
