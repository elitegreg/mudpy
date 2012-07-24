from tyderium.telnet import Interrupt

def prompt(telnetstream, msg):
    while True:
        try:
            telnetstream.sendtext(msg)
            return telnetstream.readline().rstrip()
        except Interrupt:
            telnetstream.sendtext('\n')

