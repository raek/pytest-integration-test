from contextlib import contextmanager
import logging
from queue import Queue, Empty


from fw.timeout import TimeoutCalculator


DEFAULT_TIMEOUT_SECONDS = 60
END_OF_STREAM = object()  # Unique sentinel value


class StreamError(Exception):
    pass


class EndOfStreamError(StreamError):
    pass


class MatchError(StreamError):
    pass


class TimeoutError(StreamError):
    pass


class Dispatcher:
    """Allow multiple listeners to independently consume a stream of values

    This class acts as the producer in a producer-consumer pattern, but also
    manages the life cycles of new consumers.

    Each listener has its own "current value" in the stream. This is achieved
    by having each listener consume stream values by popping them off a queue.
    The queue represents the future values for that listener, and each
    listener has its own queue.

    The stream can also be closed. This causes listener methods to raise an
    EndOfStreamError if they attempt to read values past the end.
    """
    def __init__(self):
        self._is_closed = False
        self._listener_queues = {}

    def dispatch(self, value):
        """Distribute value to each listener

        This method is called by the producer."""
        assert not self._is_closed, "Dispatcher is closed"
        for queue in self._listener_queues.values():
            queue.put(value)

    def close(self):
        """Tell listeneres stream has ended

        This also inhibits new calls to 'dispatch'. It is safe to close the
        dispatcher multiple times.

        A listener will raise an EndOfStreamError if it attempts to read any
        values past any values already existing in its queue.
        """
        if self._is_closed:
            return
        for queue in self._listener_queues.values():
            queue.put(END_OF_STREAM)
        self._is_closed = True

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


class Listener:
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

    def _next(self, timeout_seconds):
        assert self._queue is not None, "Listener not registered"
        try:
            return self._queue.get(timeout=timeout_seconds)
        except Empty:  # "Empty" is the exception type used for get() timeouts
            raise TimeoutError() from None  # Don't chain the new exception with the old one

    def next(self, timeout_seconds=DEFAULT_TIMEOUT_SECONDS):
        """Return the next value in the stream and advance the current position"""
        line = self._next(timeout_seconds)
        self._logger.debug("next: " + line)
        return line

    def expect_next(self, expected_line, timeout_seconds=DEFAULT_TIMEOUT_SECONDS):
        """Consume the next value in the stream and check that it matches the given value"""
        self._logger.debug("expect_next: " + expected_line)
        actual_line = self._next(timeout_seconds)
        if actual_line != expected_line:
            raise MatchError(f'Expected "{expected_line}", got "{actual_line}"')

    def skip_until(self, expected_line, timeout_seconds=DEFAULT_TIMEOUT_SECONDS):
        """Consume values in the stream until one that matches the given value is found"""
        self._logger.debug("skip_until: " + expected_line)
        skipped = 0
        tc = TimeoutCalculator(timeout_seconds)
        while True:
            line = self._next(tc.time_left_now())
            if line == expected_line:
                self._logger.debug(f"skipped {skipped} lines")
                return
            else:
                skipped += 1
