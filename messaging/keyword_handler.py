import re
import requests

from .models import Keyword

keyword_parser = re.compile(r'([^\s]+)(?:\s(.+))?')


def handle(message):
    parsed = keyword_parser.search(message.body().strip())
    try:
        keyword_obj = Keyword.objects.get(keyword=parsed.group(1))
    except Keyword.DoesNotExist:
        print('Keyword "%s" from message "%s" does not exist'
              % (parsed.group(1), message.body()))
        return
    if message.log_msg:
        message.log_msg.keyword = keyword_obj
        message.log_msg.save()
    if keyword_obj.handler == 'http_get':
        try:
            get = requests.get(keyword_obj.handler_argument)
            return get.text
        except requests.exceptions.ConnectionError:
            return
    elif keyword_obj.handler == 'http_post':
        try:
            r = requests.post(keyword_obj.handler_argument,
                              data={'message': message.body(),
                                    'keyword': parsed.group(1),
                                    'argument': parsed.group(2),
                                    'sender': message.sender()}
                              )
            if not r.status_code == requests.codes.ok:
                raise ValueError('Invalid HTTP response')

            print('HTTP text: ', r.text)
            return r.text
        except requests.exceptions.ConnectionError:
            return
    else:
        raise ValueError('Invalid handler')
