from utils.SignalSlots import Signal

# 1 argument: connection
connection_signal = Signal()

# 1 argument: connection
disconnection_signal = Signal()

# 2 arguments: connection, user
user_authorized_signal = Signal()

# 2 arguments: connection, user
user_unauthorized_signal = Signal()

