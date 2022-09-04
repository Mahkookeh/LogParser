from django.contrib import admin
from .models import Data, Logs, Players, LogsWithData

# Register your models here.
admin.site.register(Data)
admin.site.register(Logs)
admin.site.register(Players)
admin.site.register(LogsWithData)