class Port:
    """Bidirection communication of values (usually lines of text)

    Classes that implement this interface provide shared access to a
    bidirectional communications channel of "value" (which can be any python
    object, but usuallt strings representing lines of text). Emphasis is on
    multiple consumers.

    Output from all the clients is interleaved: all of them can call 'send'
    at any time. Output access is not limited.

    Each client that want to receive input needs to get its own listener. When
    one client receivec one value, it does not "steal" it from the others. All
    clients will see all values (as long as their listener context is active).
    """

    def send(self, value):
        """Send a value"""
        raise NotImplementedError()

    def listen(self):
        """Returns a Listener context manager"""
        raise NotImplementedError()
