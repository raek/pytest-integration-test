import pytest


@pytest.mark.initialize
def test_boot(power_cycled, command_runner):
    print(command_runner.run_command("version"))


@pytest.mark.features
def test_calculate(command_runner):
    assert command_runner.run_command("calculate") == ["42"]
