import time
from datetime import datetime

from gsm_modem.gsm_modem import SmsAt
from messaging.keyword_handler import handle
from messaging.models import ReceivedMessage, SendMessage


class ModemLoop:
    running = True

    def __init__(self, port, baudrate=115200):
        self.sms = SmsAt(port, baudrate)

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

    def loop(self):
        sms = self.sms
        saved_check = True
        while self.running:
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
                    self.handle_message(message)
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
