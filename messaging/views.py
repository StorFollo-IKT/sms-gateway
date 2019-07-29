from django.shortcuts import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from .models import SendMessage


# TODO: Add authentication


def send_message(request, recipient, message):
    msg = SendMessage(recipient=recipient, text=message)
    msg.save()
    return HttpResponse('Added to send queue')


@csrf_exempt
def send_message_post(request):
    data = request.POST
    msg = SendMessage(recipient=data['recipient'], text=data['message'])
    msg.save()
    return HttpResponse('Added to send queue')
