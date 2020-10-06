import slash


@slash.fixture(scope="session")
def debug_port():
    """Line-based access to the main debug serial port"""
    from fw.serial_port import SerialPort
    with SerialPort("/dev/ttyUSB0", 115200) as dp:
        yield dp


@slash.fixture(scope="session", autouse=True)
def charging_cable():
    """Control the charger cable

    When tests are not running the charging cable should be left connected, so
    that the battery does not drain.
    """
    from fw.cable_control import ChargingCable
    cc = ChargingCable()
    yield cc
    cc.connect()


@slash.fixture
def power_cycled(debug_port, charging_cable, restart_detector):
    """Make sure DUT is freshly restarted at beginning of test"""
    from fw.bootup import bootup
    with restart_detector.allow_restarts(), \
         debug_port.listen() as lines:
        with charging_cable.temporarily_disconnected():
            debug_port.toggle_dtr()
        bootup(debug_port, lines)


@slash.fixture
def command_runner(debug_port):
    """Run commands on the DUT"""
    from fw.command_runner import CommandRunner
    cr = CommandRunner(debug_port)
    assert cr.run_command("ping") == ["pong"]
    return cr


@slash.fixture(scope="session", autouse=True)
def restart_detector(debug_port):
    from fw.bootup import RestartDetector
    with RestartDetector(debug_port) as rd:
        yield rd
        assert not rd.check_restart_found_and_clear(), "Restart was detected during test"
