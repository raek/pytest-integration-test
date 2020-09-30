import pytest


def pytest_configure(config):
    config.addinivalue_line("usefixtures", "charging_cable")
    config.addinivalue_line("markers", "initialize")
    config.addinivalue_line("markers", "features")


@pytest.fixture
def debug_port():
    """Line-based access to the main debug port"""
    from fw.debug_port import DebugPort
    with DebugPort("/dev/ttyUSB0", 115200) as dp:
        yield dp


@pytest.fixture(scope="session")
def charging_cable():
    """Control the charger cable

    When tests are not running the charging cable should be left connected, so
    that the battery does not drain.
    """
    from fw.cable_control import ChargingCable
    cc = ChargingCable()
    yield cc
    cc.connect()


@pytest.fixture
def power_cycled(debug_port, charging_cable):
    """Make sure DUT is freshly restarted at beginning of test"""
    from fw.bootup import bootup
    with debug_port.listen() as lines:
        with charging_cable.temporarily_disconnected():
            debug_port.toggle_dtr()
        bootup(debug_port, lines)


@pytest.fixture
def command_runner(debug_port):
    """Run commands on the DUT"""
    from fw.command_runner import CommandRunner
    cr = CommandRunner(debug_port)
    assert cr.run_command("ping") == ["pong"]
    return cr
