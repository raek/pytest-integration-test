from contextlib import contextmanager
import logging
import threading


logger = logging.getLogger(__name__)


@contextmanager
def worker_thread(worker_function, stop_function=None):
    """Run a function in the background and stop it when the context ends"""
    def thread_main():
        logger.debug("worker thread begin")
        try:
            worker_function()
        except Exception as e:
            logger.error("Error in background worker thread", exc_info=e)
        logger.debug("worker thread end")
    thread = threading.Thread(target=thread_main)
    thread.daemon = True
    thread.start()
    yield
    if stop_function is not None:
        try:
            stop_function()
        except Exception as e:
            logger.error("Error when stopping worker thread", exc_info=e)
    thread.join()
