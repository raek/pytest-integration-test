from contextlib import contextmanager
import logging
import threading


logger = logging.getLogger(__name__)


@contextmanager
def worker_thread(worker_function, stop_function=None):
    """Run a function in the background and stop it when the context ends

    The worker function receives a single argument: a 'signal_thread_ready'
    callback function. The context is not entered until it has been called.
    A worker function that does not need synchronization like this should
    call it as its first statement.

    This context wrapper ensure that the worker function is running and ready
    when the context is entered and that it has returned when the context is
    exited.
    """
    thread_ready = threading.Event()
    def thread_main():
        logger.debug("worker thread begin")
        try:
            worker_function(thread_ready.set)
        except Exception as e:
            logger.error("Error in background worker thread", exc_info=e)
        logger.debug("worker thread end")
    thread = threading.Thread(target=thread_main)
    thread.daemon = True
    thread.start()
    thread_ready.wait()
    try:
        yield
    finally:
        if stop_function is not None:
            try:
                stop_function()
            except Exception as e:
                logger.error("Error when stopping worker thread", exc_info=e)
        thread.join()
