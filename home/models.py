from django.db import models

# Create your models here.
class Record(models.Model):
    username=models.CharField(max_length=50)
    email=models.EmailField(max_length=50)
    mobile=models.CharField(max_length=50)
    password=models.CharField(max_length=50)

class upload(models.Model):
    file=models.FileField()