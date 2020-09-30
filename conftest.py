import pytest


@pytest.fixture
def debug_port():
    """Line-based access to the main debug port"""
    from debug_port import DebugPort
    with DebugPort("/dev/ttyUSB0", 115200) as dp:
        yield dp


@pytest.fixture
def power_cycled(debug_port):
    """Make sure DUT is freshly restarted at beginning of test"""
    from bootup import bootup
    with debug_port.listen() as lines:
        debug_port.toggle_dtr()
        bootup(debug_port, lines)


@pytest.fixture
def command_runner(debug_port):
    """Run commands on the DUT"""
    from command_runner import CommandRunner
    cr = CommandRunner(debug_port)
    assert cr.run_command("ping") == ["pong"]
    return cr
