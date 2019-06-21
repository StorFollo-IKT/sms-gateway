from django.contrib import admin
from .models import Keyword, SendMessage, ReceivedMessage


class KeywordAdmin(admin.ModelAdmin):
    list_display = ('keyword', 'handler', 'handler_argument')


admin.site.register(Keyword, KeywordAdmin)


class MessageAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'added', 'sent')


admin.site.register(SendMessage, MessageAdmin)
admin.site.register(ReceivedMessage)
