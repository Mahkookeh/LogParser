from django.contrib import admin
from .models import Data, Log, Player, LogsWithData

# Register your models here.
admin.site.register(Data)
admin.site.register(Log)
admin.site.register(Player)
admin.site.register(LogsWithData)