class CommandError(Exception):
    pass

class CommandRunner:
    def __init__(self, debug_port):
        self._debug_port = debug_port

    def run_command(self, command):
        """Send a command, collect its output lines and check that it succeeded.

        Returns a list of lines
        """
        ok, lines = self.try_run_command(command)
        if ok:
            return lines
        else:
            raise CommandError("Error running command: " + command)

    def try_run_command(self, command):
        """Send a command and return whether it succeeded and the lines output by the command.

        Returns a (bool, lines) pair.
        """
        with self._debug_port.listen() as lines:
            # Send command
            self._debug_port.send(command)
            # Expect command echo
            lines.expect_next(command)
            # Read lines until end (OK or ERROR)
            result = []
            ok = None
            while True:
                line = lines.next()
                if line == "OK":
                    ok = True
                    break
                elif line == "ERROR":
                    ok = False
                    break
                else:
                    result.append(line)
            # Expect next prompt
            lines.expect_next("Enter command")
            return ok, result
