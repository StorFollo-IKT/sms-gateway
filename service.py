import os
import sys
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sms_gateway.settings")
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from SMWinservice import SMWinservice
import django

django.setup()
from django.conf import settings
from gsm_modem.modem_loop import ModemLoop
# TODO: Write exceptions to event log?


class GsmModemGatewayService(SMWinservice):
    _svc_name_ = "GsmModemGatewayService"
    _svc_display_name_ = "GSM modem gateway"
    _svc_description_ = "Use a GSM modem to send and receive SMS"
    modem = None

    def main(self):
        # call_command('modem', 'COM20')
        # print('Running')
        self.modem.loop()

    def start(self):
        self.modem = ModemLoop(settings.GSM_MODEM_PORT,
                               settings.GSM_MODEM_BAUD_RATE)
        self.modem.running = True

    def stop(self):
        self.modem.running = False


if __name__ == '__main__':
    GsmModemGatewayService.parse_command_line()
