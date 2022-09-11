from rest_framework import serializers

from .models import Data, Players, Logs, LogsWithData


# Serializer for log data table
class DataSerializer(serializers.ModelSerializer):
    class Meta:
        model = Data
        fields = '__all__'

# Serializer for player table
class PlayersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Players
        fields = '__all__'

# Serializer for logs table
class LogsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Logs
        fields = '__all__'

# Serializer for logs with data (not actual table)
class LogsWithDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogsWithData
        fields = '__all__'