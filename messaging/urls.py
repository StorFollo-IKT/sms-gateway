from django.urls import path, re_path
from .views import send_message

app_name = 'messaging'

urlpatterns = [
    path('send/<str:recipient>/<str:message>', send_message, name='send'),
]
