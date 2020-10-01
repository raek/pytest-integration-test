from contextlib import ExitStack, suppress, contextmanager
import logging
import threading

from fw.worker_thread import worker_thread
from fw.stream import EndOfStreamError


PASSWORD = "hunter2"


def bootup(debug_port, lines):
    """Follow the DUT through the boot process

    This function assumes that a boot was just triggered before running this
    function. When this function returns the DUT is ready for being used by
    CommandRunner.
    """
    lines.skip_until("Booting...")
    lines.skip_until("Loading blocks...")
    lines.skip_until("Starting user space")
    authenticate(debug_port, lines)
    lines.expect_next("Enter command")


def authenticate(debug_port, lines):
    lines.skip_until("Enter secret password")
    debug_port.send(PASSWORD)
    lines.expect_next(PASSWORD)
    lines.expect_next("Logged in")


class RestartDetector(ExitStack):
    def __init__(self, debug_port):
        super().__init__()
        self._debug_port = debug_port
        self._lock = threading.Lock()
        self._restart_found = False
        self._restarts_allowed = False
        self.enter_context(worker_thread(self._worker_function, stop_function=debug_port.close))

    def _worker_function(self, signal_thread_ready):
        logger = logging.getLogger(__name__ + "." + self.__class__.__name__)
        with suppress(EndOfStreamError), \
             self._debug_port.listen() as lines:
            signal_thread_ready()
            while True:
                line = lines.next()
                if line == "Booting...":
                    with self._lock:
                        if self._restarts_allowed:
                            logger.info("Found allowed restart")
                        else:
                            logger.error("Found unexpected restart")
                            self._restart_found = True

    def check_restart_found_and_clear(self):
        with self._lock:
            status = self._restart_found
            self._restart_found = False
            return status

    @contextmanager
    def allow_restarts(self):
        with self._lock:
            old = self._restarts_allowed
            self._restarts_allowed = True
        try:
            yield
        finally:
            with self._lock:
                self._restarts_allowed = old
