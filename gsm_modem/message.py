from gsmmodem.pdu import decodeSmsPdu


class Message:
    status = ''
    pdu_body = ''
    log_msg = None

    def __init__(self, index, status, pdu_body):
        self.set_index(index)
        self.status = status
        self.pdu_body = pdu_body
        self.message = decodeSmsPdu(pdu_body)
        print(self.message)

    def parsed_status(self):
        return self.status

    def body(self):
        return self.message['text']

    def sender(self):
        return self.message['number']

    def time(self):
        return self.message['time']

    def set_index(self, index):
        if type(index) == bytes:
            self.index = index.decode()
        else:
            self.index = index

    def __str__(self):
        return self.message['text']
