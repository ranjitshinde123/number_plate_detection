from django.contrib import admin
from .models import *
# Register your models here.
@admin.register(Record)
class Recordadmin(admin.ModelAdmin):
    list_display = ['id','username','email','mobile','password']

@admin.register(upload)
class uploadadmin(admin.ModelAdmin):
    list_display = ['id','file']