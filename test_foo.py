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
    password = "hunter2"
    with debug_port.listen() as lines:
        debug_port.toggle_dtr()
        lines.skip_until("Booting...")
        lines.skip_until("Loading blocks...")
        lines.skip_until("Starting user space")
        lines.skip_until("Enter secret password")
        debug_port.send_line(password)
        lines.expect_next(password)
        lines.expect_next("Logged in")
        lines.expect_next("Enter command")


@pytest.fixture
def command_runner(debug_port):
    from command_runner import CommandRunner
    cr = CommandRunner(debug_port)
    assert cr.run_command("ping") == ["pong"]
    return cr


@pytest.mark.initialize
def test_boot(power_cycled, command_runner):
    print(command_runner.run_command("version"))


@pytest.mark.features
def test_calculate(command_runner):
    assert command_runner.run("calculate") == ["42"]
