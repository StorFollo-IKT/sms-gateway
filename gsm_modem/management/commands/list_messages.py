from pprint import pprint

from django.core.management.base import BaseCommand

from gsm_modem.gsm_modem import SmsAt


class Command(BaseCommand):
    help = 'List saved messages'

    def add_arguments(self, parser):
        parser.add_argument('port', nargs='+', type=str)

    def handle(self, *args, **options):
        sms = SmsAt(options['port'][0], 115200)
        pprint(sms.get_messages_pdu())
