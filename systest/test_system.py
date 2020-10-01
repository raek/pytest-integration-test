import pytest


@pytest.mark.initialize
def test_boot(power_cycled, command_runner):
    print(command_runner.run_command("version"))


@pytest.mark.features
def test_calculate(command_runner):
    assert command_runner.run_command("calculate") == ["42"]

@pytest.mark.xfail
def test_unexpected_restart(debug_port):
    with debug_port.listen() as lines:
        debug_port.toggle_dtr()
        lines.skip_until("Loading blocks...")
