from contextlib import contextmanager, suppress

import pytest

from fw.command_runner import CommandRunner
from fw.pipe_port import pipe_port_pair
from fw.stream import EndOfStreamError, TimeoutError
from fw.worker_thread import worker_thread


TEST_TIMEOUT_SECONDS = 1  # Should be instant in unit tests


@pytest.fixture
def fake_command_interpreter():
    external_port, internal_port = pipe_port_pair()
    def worker_function():
        emulate_command_interpreter(internal_port)
    with external_port, internal_port, worker_thread(worker_function):
        yield external_port


def emulate_command_interpreter(port):
    with suppress(EndOfStreamError, TimeoutError), \
         port.listen() as lines:
        while True:
            command = lines.next(timeout_seconds=TEST_TIMEOUT_SECONDS)
            port.send(command)
            if command == "ping":
                port.send("pong")
                port.send("OK")
            else:
                port.send("ERROR")
            port.send("Enter command")


def test_successful_try_run_command(fake_command_interpreter):
    cr = CommandRunner(fake_command_interpreter)
    ok, lines = cr.try_run_command("ping", timeout_seconds=TEST_TIMEOUT_SECONDS)
    assert ok
    assert lines == ["pong"]


def test_failing_try_run_command(fake_command_interpreter):
    cr = CommandRunner(fake_command_interpreter)
    ok, lines = cr.try_run_command("xyz", timeout_seconds=TEST_TIMEOUT_SECONDS)
    assert not ok
