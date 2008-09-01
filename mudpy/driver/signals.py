from utils.SignalSlots import Signal

# 2 arguments: connection, user
user_authorized_signal = Signal()

# 2 arguments: connection, user
user_unauthorized_signal = Signal()

# 2 arguments: connection, dict of player properties
new_user_signal = Signal()

