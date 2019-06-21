from django.core.management.base import BaseCommand
from gsm_modem.modem_loop import ModemLoop


class Command(BaseCommand):
    help = 'Start modem loop'
    sms = None

    def add_arguments(self, parser):
        parser.add_argument('port', nargs='+', type=str)

    def handle(self, *args, **options):
        modem = ModemLoop(options['port'][0], 115200)
        try:
            modem.loop()
        except KeyboardInterrupt:
            modem.running = False
