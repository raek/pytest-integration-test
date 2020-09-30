from contextlib import contextmanager
import logging
import time


_IMAGINED_STATE_FILE_PATH = "charging_cable.txt"


class ChargingCable:
    """Controls an imaginary charging cable"""
    def __init__(self):
        self._logger = logging.getLogger(__name__ + "." + self.__class__.__name__)
        self._last_state = None  # "None" means unknown, and is distinct from False and True

    @contextmanager
    def temporarily_disconnected(self):
        self.disconnect()
        yield
        self.connect()

    def connect(self):
        self._logger.debug("connect")
        if self._last_state != True:
            self._logger.info("Connecting charger cable...")
            self._set_relay(True)
            self._logger.info("Done.")
        self._last_state = True

    def disconnect(self):
        self._logger.debug("disconnect")
        if self._last_state != False:
            self._logger.info("Disconnecting charger cable...")
            self._set_relay(False)
            self._logger.info("Done.")
        self._last_state = False

    def _set_relay(self, state):
        time.sleep(1)
        with open(_IMAGINED_STATE_FILE_PATH, "wt") as f:
            content = "connected" if state else "disconnected"
            f.write(content)
        self._logger.info("*relay says click*")
        time.sleep(1)
