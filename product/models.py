from django.conf import settings
from django.db import models

# Create your models here.
class MainContent(models.Model):
    title = models.CharField(max_length = 200)
    content = models.TextField()
    pub_date = models.DateTimeField('date published')
    def __str__(self):
        return self.title

class Comment(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content_list = models.ForeignKey(MainContent, on_delete=models.CASCADE)
    content = models.TextField()
    create_date = models.DateTimeField(auto_now_add=True)
    modify_date = models.DateTimeField(auto_now=True)

