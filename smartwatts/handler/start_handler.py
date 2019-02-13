from smartwatts.message import OKMessage, StartMessage, ErrorMessage
from smartwatts.handler import Handler


class StartHandler(Handler):
    """
    Initialize the received state
    """

    def handle(self, msg, state):
        """
        Allow to initialize the state of the actor, then reply to the control
        socket.

        :param smartwatts.StartMessage msg: Message that initialize the actor
        :param smartwatts.State state: State of the actor
        :rtype smartwatts.State: the new state of the actor
        """
        if state.initialized:
            state.socket_interface.send_control(
                ErrorMessage('Actor already initialized'))
            return state

        if not isinstance(msg, StartMessage):
            return state

        state = self.initialization(state)

        state.initialized = True
        state.socket_interface.send_control(OKMessage())

        return state

    def initialization(self, state):
        """
        Abstract method that initialize the actor after receiving a start msg

        :param smartwatts.State state: State of the actor
        :rtype smartwatts.State: the new state of the actor
        """
        return state
