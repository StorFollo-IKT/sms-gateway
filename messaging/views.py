from django.shortcuts import render, HttpResponse
from .models import SendMessage


def send_message(recipient, message):
    msg = SendMessage(recipient=recipient, text=message)
    msg.save()
    return HttpResponse('Added to send queue')
