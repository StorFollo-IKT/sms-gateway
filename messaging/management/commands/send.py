# from datetime import datetime
from pprint import pprint

from django.core.management.base import BaseCommand  # , CommandError
# from django.utils import timezone

from messaging.models import SendMessage
from gsm_modem.gsm_modem import SmsAt
import time


class Command(BaseCommand):
    help = 'Send message'

    def add_arguments(self, parser):
        parser.add_argument('recipient', nargs='+', type=int)
        parser.add_argument('message', nargs='+', type=str)

    def handle(self, *args, **options):
        msg = SendMessage(recipient=options['recipient'][0],
                          text=options['message'][0])
        msg.save()
