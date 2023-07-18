import time

from aiosmtpd.controller import Controller

SMTP_SERVER = "127.0.0.1"
SMTP_PORT = 2525


class CustomHandler:
    async def handle_DATA(self, server, session, envelope):  # pylint: disable=C0103
        del server, session, envelope
        return "250 OK"


class SmtpServer:
    def __init__(self, hostname=SMTP_SERVER, port=SMTP_PORT):
        self.hostname = hostname
        self.port = port
        self.smtpd = Controller(CustomHandler(), hostname=hostname, port=port)

    def start(self):
        print(time.asctime(), f"SMTP: Server starts - {self.smtpd.hostname}:{self.smtpd.port}")
        self.smtpd.start()

    def stop(self):
        print(time.asctime(), f"SMTPS: Server stops - {self.smtpd.hostname}:{self.smtpd.port}")
        self.smtpd.stop()
