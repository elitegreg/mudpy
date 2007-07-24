import socket

def connected_error_code(dispatcher):
  if not self.connected:
    #check if connect was successful
    error = self.socket.getsockopt(socket.SOL_SOCKET,
                                   socket.SO_ERROR)
    return error

