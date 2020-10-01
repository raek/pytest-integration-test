from contextlib import contextmanager
import logging
from queue import Queue


class Dispatcher():
    """Allow multiple listeners to independently consume a stream of values

    This class acts as the producer in a producer-consumer pattern, but also
    manages the life cycles of new consumers.

    Each listener has its own "current value" in the stream. This is achieved
    by having each listener consume stream values by popping them off a queue.
    The queue represents the future values for that listener, and each
    listener has its own queue.
    """
    def __init__(self):
        self._listener_queues = {}

    def dispatch(self, value):
        """Distribute value to each listener

        This method is called by the producer."""
        for queue in self._listener_queues.values():
            queue.put(value)


    def add_listener(self, listener):
        """Register a new listener

        Dispatched values will appear in the returned queue, starting from the
        time of registration. Previously dispatched values will not be seen by
        this listener.
        """
        queue = Queue()
        self._listener_queues[listener] = queue
        return queue

    def remove_listener(self, listener):
        """Stop receiving values

        Values dispached in the future will not be seen by this listener.
        Previously dispatched values that has not been consumed by the
        listener remains in the listener's queue.
        """
        del self._listener_queues[listener]


class ListenerError(Exception):
    pass


class Listener():
    """Context manager that subscribes to a stream of values from a dispatcher

    This class acts as the consumer in a producer-consumer pattern.

    Within the context the methods of this class can be used to consume values
    from the stream.
    """
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
        """Return the next value in the stream and advance the current position"""
        line = self._next()
        self._logger.debug("next: " + line)
        return line

    def expect_next(self, expected_line):
        """Consume the next value in the stream and check that it matches the given value"""
        self._logger.debug("expect_next: " + expected_line)
        actual_line = self._next()
        if actual_line != expected_line:
            raise ListenerError(f'Expected "{expected_line}", got "{actual_line}"')

    def skip_until(self, expected_line):
        """Consume values in the stream until one that matches the given value is found"""
        self._logger.debug("skip_until: " + expected_line)
        skipped = 0
        while True:
            line = self._next()
            if line == expected_line:
                self._logger.debug(f"skipped {skipped} lines")
                return
            else:
                skipped += 1
