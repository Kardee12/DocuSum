from django.conf import settings
from django.db import models


class ChatData(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    isQuestion = models.BooleanField(default=False)
    isAI = models.BooleanField(default=False)


class Document(models.Model):
    name = models.CharField(max_length=255, default='DEFAULT')
    file = models.FileField(upload_to='documents/')

    def __str__(self):
        return self.name
