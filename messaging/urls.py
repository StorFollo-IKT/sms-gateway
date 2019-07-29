from django.urls import path, re_path
from .views import send_message, send_message_post

app_name = 'messaging'

urlpatterns = [
    path('send/<str:recipient>/<str:message>', send_message, name='send'),
    path('send_post', send_message_post, name='send_post'),
]
