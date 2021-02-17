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
        """
        Handle received message
        :param Message message: Message object
        :return:
        """
        try:
            body = message.body()
        except UnicodeEncodeError as e:
            body = str(e)

        msg_log = ReceivedMessage(text=body,
                                  smsc=message.message['smsc'],
                                  sender=message.sender(),
                                  time=message.time().replace(tzinfo=None))
        message.log_msg = msg_log
        try:
            msg_log.save()
        except:
            self.sms.delete_message(message.index)
            self.sms.write('ATZ')  # Soft reset the modem
            message.time()
            file = 'invalid_message_%s.txt' % \
                   message.message['time'].strftime('%Y-%m-%d %H%M%S')
            fp = open(file, 'wb')
            fp.write(message.body().encode(errors='backslashreplace'))
            fp.close()
            try:
                msg_log.text = file
                msg_log.save()
            except UnicodeEncodeError:
                pass
            return

        try:
            response_text = handle(message)
            if response_text:
                print('Send response message %s to %s' % (response_text, message.sender()[1:]))
                self.sms.send(response_text, message.sender())
                msg_log.response_text = response_text
                msg_log.save()
            self.sms.delete_message(message.index)
        except ValueError as e:
            print('Error sending response to received message: %s' % e)

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
                data_temp = sms.read()
                try:
                    data = data_temp.decode('ascii').strip()
                except UnicodeDecodeError:
                    print('Unable to decode: ', data_temp)
                    continue

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
