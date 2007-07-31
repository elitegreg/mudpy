import socket

def connected_error_code(dispatcher):
  if not dispatcher.connected:
    #check if connect was successful
    error = dispatcher.socket.getsockopt(socket.SOL_SOCKET,
                                         socket.SO_ERROR)
    return error

