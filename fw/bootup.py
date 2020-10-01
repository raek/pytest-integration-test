PASSWORD = "hunter2"


def bootup(debug_port, lines):
    """Follow the DUT through the boot process

    This function assumes that a boot was just triggered before running this
    function. When this function returns the DUT is ready for being used by
    CommandRunner.
    """
    lines.skip_until("Booting...")
    lines.skip_until("Loading blocks...")
    lines.skip_until("Starting user space")
    authenticate(debug_port, lines)
    lines.expect_next("Enter command")


def authenticate(debug_port, lines):
    lines.skip_until("Enter secret password")
    debug_port.send(PASSWORD)
    lines.expect_next(PASSWORD)
    lines.expect_next("Logged in")
