from . import lib as ev

def sleep(amount=0):
    if amount > 0:
        ev.Timer(float(amount)).start()
    else: # use zero value to give other greenlets a chance to run
        ev.Idle().start()
