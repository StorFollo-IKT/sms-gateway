from django.db import models


class Keyword(models.Model):
    handlers = (('http_get', 'HTTP GET'), ('http_post', 'HTTP POST'))

    keyword = models.CharField(max_length=50, unique=True)
    handler = models.CharField(max_length=50, choices=handlers, default='http_get')
    handler_argument = models.CharField(max_length=100)

    def __str__(self):
        return self.keyword


class SendMessage(models.Model):
    text = models.CharField(max_length=500)
    recipient = models.CharField(max_length=12)
    added = models.DateTimeField(auto_now_add=True)
    sent = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return '%s %s' % (self.recipient, self.added)


class ReceivedMessage(models.Model):
    text = models.TextField()
    smsc = models.CharField(max_length=12)
    sender = models.CharField(max_length=12)
    time = models.DateTimeField()
    keyword = models.ForeignKey(Keyword, on_delete=models.SET_NULL,
                                blank=True, null=True)

    response_text = models.TextField(blank=True)

    def __str__(self):
        return '%s %s' % (self.time, self.sender)
