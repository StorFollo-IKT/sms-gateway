# from datetime import datetime
from pprint import pprint

from django.core.management.base import BaseCommand  # , CommandError
# from django.utils import timezone

from messaging.models import Keyword, SendMessage, ReceivedMessage
from gsm_modem.gsm_modem import SmsAt
import time
from datetime import datetime
from messaging.keyword_handler import handle


class Command(BaseCommand):
    help = 'Start modem loop'
    sms = None

    def add_arguments(self, parser):
        parser.add_argument('port', nargs='+', type=str)

    def handle_message(self, message):
        msg_log = ReceivedMessage(text=message.body(),
                                  smsc=message.message['smsc'],
                                  sender=message.sender(),
                                  time=message.time().replace(tzinfo=None))
        message.log_msg = msg_log
        msg_log.save()
        try:
            response_text = handle(message)
            if response_text:
                print('Response: ', response_text)
                self.sms.send(response_text, message.sender())
                msg_log.response_text = response_text
                msg_log.save()
            self.sms.delete_message(message.index)
        except ValueError as e:
            print(e)

    def handle(self, *args, **options):
        self.sms = SmsAt(options['port'][0], 115200)
        sms = self.sms

        try:
            saved_check = True
            while True:
                if saved_check:
                    print('Check saved messages')
                    capacity = sms.capacity()
                    print('%d message(s) saved' % capacity['used'])
                    if capacity['used'] > 0:
                        messages = sms.get_messages_pdu()
                        for message in messages:
                            self.handle_message(message)

                    saved_check = False

                if sms.ser.in_waiting > 0:
                    time.sleep(1)
                    data = sms.read().decode('ascii').strip()
                    if data[0:5] == '+CMTI':
                        info = sms.CMTI_REGEX.match(data)
                        print('Message received')
                        message = sms.get_messages_pdu(info.group(2).encode())
                        print(message)
                        if not message:
                            print('Empty message')
                            continue
                        try:
                            response_text = handle(message)
                            if response_text:
                                sms.send(response_text, message.sender()[1:])
                                print('Send response message %s to %s' % (response_text, message.sender()[1:]))
                        except ValueError as e:
                            print('Error sending response to received message: %s' % e)
                            pass
                    elif data[0:4] == 'RING':
                        print('Rejecting call')
                        # sms.ser.write(b'ATH\r')
                        # print(sms.ser.readline())
                        sms.write('ATH', verify=True)
                    else:
                        print(data)
                else:  # Process send queue
                    messages = SendMessage.objects.filter(sent=None)
                    if messages.count() >= 1:
                        print('%d messages in send queue' % messages.count())
                        for message_db in messages:
                            try:
                                print('Send messsage %s to %s' % (message_db.text, message_db.recipient))
                                sms.send(message_db.text, message_db.recipient)
                                print('Send DB message %s to %s' % (message_db.text, message_db.recipient))
                                message_db.sent = datetime.now()
                                message_db.save()
                                print(message_db)
                            except ValueError as e:
                                print('Error sending message from queue: %s' % e)
                        saved_check = True

        except KeyboardInterrupt:
            pass
