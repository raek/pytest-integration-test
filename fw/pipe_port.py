from contextlib import ExitStack

from fw.stream import Dispatcher, Listener


def pipe_port_pair():
    """Return a pair of ports connected to each other

    The ports are context managers.
    """
    a_dispatcher = Dispatcher()
    b_dispatcher = Dispatcher()
    a_port = _PipePort(own_dispatcher=a_dispatcher, other_dispatcher=b_dispatcher)
    b_port = _PipePort(own_dispatcher=b_dispatcher, other_dispatcher=a_dispatcher)
    return a_port, b_port


class _PipePort(ExitStack):
    def __init__(self, own_dispatcher, other_dispatcher):
        super().__init__()
        self._own_dispatcher = own_dispatcher
        self._other_dispatcher = other_dispatcher
        self.callback(self._own_dispatcher.close)
        self.callback(self._own_dispatcher.close)

    def send(self, value):
        self._other_dispatcher.dispatch(value)

    def listen(self):
        return Listener(self._own_dispatcher)
