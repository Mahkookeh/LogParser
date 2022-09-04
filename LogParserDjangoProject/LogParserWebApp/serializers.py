from rest_framework import serializers

from .models import Data, Players, Logs, LogsWithData



class DataSerializer(serializers.ModelSerializer):
    class Meta:
        model = Data
        fields = '__all__'

class PlayersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Players
        fields = '__all__'

class LogsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Logs
        fields = '__all__'

class LogsWithDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogsWithData
        fields = '__all__'