import slash


@slash.tag("initialize")
def test_boot(power_cycled, command_runner):
    print(command_runner.run_command("version"))


@slash.tag("features")
def test_calculate(command_runner):
    print(x)
    assert command_runner.run_command("calculate") == ["42"]


@slash.tag("features")
def test_calculate2(command_runner):
    assert command_runner.run_command("calculate") == ["42"]


@slash.tag("features")
def test_calculate3(command_runner):
    assert command_runner.run_command("calculate") == ["42"]


@slash.tag("xfail")
def test_unexpected_restart(debug_port):
    with debug_port.listen() as lines:
        debug_port.toggle_dtr()
        lines.skip_until("Loading blocks...")
