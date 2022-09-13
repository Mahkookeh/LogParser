from rest_framework import serializers

from .models import Data, Player, Log, LogsWithData


# Serializer for log data table
class DataSerializer(serializers.ModelSerializer):
    class Meta:
        model = Data
        fields = '__all__'

# Serializer for player table
class PlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        fields = '__all__'

    def validate_groups(self, Groups):
        print(Groups)
        print(self.instance)
        print(self.instance.Groups)
        existing_groups = []
        if self.instance and self.instance.Groups:
            # Patch or Put request
            existing_groups = self.instance.Groups
        return existing_groups + Groups

# Serializer for groups list belonging to player (not actual table)
class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        fields = ("Groups",)  

    def validate_Groups(self, Groups):
        existing_groups = []
        if self.instance and self.instance.Groups:
            # Patch or Put request
            existing_groups = self.instance.Groups
        return list(set([group.capitalize() for group in existing_groups + Groups]))

# Serializer for logs table
class LogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Log
        fields = '__all__'

# Serializer for logs with data (not actual table)
class LogsWithDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogsWithData
        fields = '__all__'