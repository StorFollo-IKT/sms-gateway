import serial  # pyserial: http://pyserial.sourceforge.net
# from gsmmodem import pdu
from gsmmodem.pdu import encodeSmsSubmitPdu, decodeSmsPdu
import time
# Used for parsing new SMS message indications
import re

try:
    from message import Message
except ModuleNotFoundError:
    from .message import Message


def reverse_octets(string):
    output_string = ''
    for pos in range(0, len(string), 2):
        output_string += string[pos+1] + string[pos]

    return output_string


class SmsAt:
    pdu_mode = False

    def __init__(self, port, baudrate=9600):
        # return
        self.ser = serial.Serial(port=port, baudrate=baudrate, bytesize=serial.EIGHTBITS,
                                 parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=5)
        self.ser.write(b'\x1a')  # CTRL+Z ASCII 26
        self.write('ATZ')
        # self.read_loop()
        time.sleep(1)
        # print(self.read())
        self.write('ATE0')
        # self.ser.write(b'ATE0\r')
        time.sleep(1)
        # result = self.read_loop()
        result = self.read().decode('ASCII')
        if result.find('ERROR') > -1:
            raise ValueError('Error in response: ' + result)

        self.CMTI_REGEX = re.compile(r'^\+CMTI:\s*"([^"]+)",\s*(\d+)$')
        self.CMGRL_REGEX = re.compile(r'\+CMG[R|L]: ([0-9]+),([0-9]?).+\s([0-9A-Z]+)')

    def read(self):
        bytes_to_read = self.ser.in_waiting
        print('%d bytes to read' % bytes_to_read)
        return self.ser.read(bytes_to_read)

    def read_time(self, size=None):
        before = time.time()
        if size:
            data = self.ser.read(size)
        else:
            data = self.read()
        after = time.time()
        print('Read %d bytes in %d seconds' % (len(data), after-before))
        return data

    def read_loop(self):
        data = ''
        blank_count = 0
        while True:
            line = self.ser.readline()
            try:
                data += line.decode('ASCII')
            except UnicodeDecodeError:
                raise ValueError('Unable to decode, check baud rate')

            if line.find(b'OK') > -1 or line.find(b'ERROR') > -1:
                break
            if line == b'':
                print('Blank line %d' % blank_count)
                blank_count += 1
            if blank_count > 2:
                print('%d blank lines, send ctrl+z' % blank_count)
                self.ser.write(b'\x1a')  # CTRL+Z ASCII 26
                try:
                    self.write(b'AT', verify=True)
                except ValueError:
                    self.write(b'AT', verify=True)
                # self.write(b'AT')
                line = self.ser.readline()
                if line == b'':
                    raise ValueError('modem unresponsive')

        return data

    def write(self, data, verify=False):
        if not type(data) == bytes:
            data = data.encode()

        data += b'\r'

        print('Write: ', data)
        written_bytes = self.ser.write(data)
        if verify:
            # response = self.ser.readline()
            # response = response.decode('ASCII').strip()
            response = self.read_loop().strip()
            if response == 'ERROR':
                raise ValueError('Modem returned error')
            elif not response == 'OK':
                print('Unknown response from modem: ', response)
        return written_bytes

    def capacity(self):
        self.ser.write(b'AT+CPMS?\r')
        capacity_string = self.read_loop()
        capacity = re.search(r'"([A-Z]+)",([0-9]+),([0-9]+)', capacity_string)
        if not capacity:
            raise ValueError('Unable to get capacity, string is: ', capacity_string)
        if int(capacity.group(2)) == int(capacity.group(3)):
            raise ValueError('Message storage %s full: %s messages saved' % (capacity.group(1), capacity.group(2)))
        else:
            print('%s of %s messages stored' % (capacity.group(2), capacity.group(3)))
            return {'free': int(capacity.group(3)) - int(capacity.group(2)),
                    'used': int(capacity.group(2)),
                    'capacity': int(capacity.group(3))
                    }

    def delete_message(self, index):
        if index == 'all':
            self.write('AT+CMGD=0,4', verify=True)
            # time.sleep(5)
        else:
            self.write('AT+CMGD=' + index, verify=True)
            # time.sleep(0.5)

        # result = self.ser.readline().decode('ASCII')
        # if result.find('ERROR') > -1:
        #    raise ValueError('Deletion failed: ' + result)

    def get_messages_pdu(self, message_id=None, delete=True):
        """

        :param message_id: Message id to read
        :param delete: Delete message after reading (only valid when message id is specified)
        :return: Message objects
        """
        # http://www.gsm-modem.de/sms-pdu-mode.html

        self.set_pdu_mode(enabled=True)

        if not message_id:  # Read all messages
            self.ser.write(b'AT+CMGL=4\r')
        else:  # Read specified message
            # self.ser.write(b'AT+CMGR=' + message_id + b'\r')
            print('Get message', message_id, ':')
            self.write(b'AT+CMGR=' + message_id)
        messages_raw = self.read_loop()
        # print('CMGR find:', messages_raw.find('CMGR'))
        """if messages_raw.find('CMGR') > -1:
            self.set_pdu_mode(enabled=True)
            # return self.get_messages_pdu(message_id, delete)"""
        print(messages_raw)

        # messages = re.findall(r'\+CMG[L|R](.+)\s([0-9A-Z]+)', messages_raw)
        messages = self.CMGRL_REGEX.findall(messages_raw)
        print(messages)
        if not messages:
            return None
        parsed_messages = []
        for message in messages:
            msg = Message(message[0], message[1], message[2])
            if message_id:
                msg.set_index(message_id)
                if delete:
                    self.delete_message(msg.index)
                return msg
            else:
                parsed_messages.append(msg)
        return parsed_messages

    def get_messages(self):
        if self.pdu_mode:
            self.set_pdu_mode(enabled=False)

        self.ser.write(b'AT+CMGL="ALL"\r')
        print(self.read())

    def set_pdu_mode(self, enabled=True):
        if enabled:
            print('Enable PDU mode')
            self.write('AT+CMGF=0', verify=True)
            self.pdu_mode = True
        else:
            self.write('AT+CMGF=1', verify=True)
            self.pdu_mode = False

    def send(self, message, number):
        if not self.pdu_mode:
            self.set_pdu_mode(enabled=True)
        pdu_messages = encodeSmsSubmitPdu(number, message, requestStatusReport=False)
        part = 1
        for pdu in pdu_messages:
            print('Part %d' % part)
            self.write('AT+CMGS={0}'.format(pdu.tpduLength))

            before = time.time()

            lines = self.ser.read(4)
            #lines = self.read_time(4)
            #lines = self.read_loop()
            #lines = self.ser.readline()
            #lines += self.ser.readline()
            # print('CMGS response: ', lines)

                # print('Ready for data, waited %d seconds for %d bytes' % (time.time()-before, len(lines)))
            if not lines.strip() == b'>':
                print('Invalid response: ', lines)
                lines += self.ser.readline()
                print(lines)
                return
            elif not lines:
            # if b'> ' not in lines:
                # lines = self.ser.read(4)
                print('Not ready, try again')
                print('CMGS response: ', lines)
                lines = self.read_time(4)
                if b'> ' in lines:
                    print('Ready for data try 2, waited %d seconds for %d bytes' % (time.time() - before, len(lines)))
                    pass
                else:
                    # reset modem?
                    # AF+CFUN=1
                    # self.write('AT', verify=True)
                    raise ValueError('Data prompt not received in %d seconds: %s' % (time.time()-before, lines))

            data_bytes = self.ser.write(str(pdu).encode())

            # time.sleep(10)

            # print('ctrl+z')
            self.ser.write(b'\x1a')  # CTRL+Z ASCII 26

            # lines = self.ser.read(19)
            # lines = self.read_time(19)
            before = time.time()
            lines = self.read_loop()
            print('Data sent, waited %d seconds for %d bytes' % (time.time() - before, len(lines)))

            if not lines:
                # print('No data, sleep 1 second')
                print('No data, retry read')
                # time.sleep(1)
                #lines = self.ser.read(19)
                lines = self.read_time(19)
                if not lines:
                    raise ValueError('No data received in two attempts')

            if 'OK' not in lines:
                print(lines)
                raise ValueError('OK not found in response part %d' % part)
            else:
                matches = re.search(r'CMGS: ([0-9]+)', str(lines))
                if matches:
                    print('Message part %d sent with id %s' % (part, matches.group(1)))
                else:
                    print('CMGS not found: ', lines)

            part += 1

        # return self.read()

