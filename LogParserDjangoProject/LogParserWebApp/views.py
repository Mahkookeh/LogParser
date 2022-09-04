from django.shortcuts import render
from django.db import connection
from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination
from .models import Data, Players, Logs, LogsWithData
from .serializers import DataSerializer, PlayersSerializer, LogsSerializer, LogsWithDataSerializer
from django.core.paginator import Paginator
import operator
import itertools
from django.utils.dateparse import parse_duration

# Create your views here.
# TODO:
# CRUD for data, logs, players
# create data, logs, players
# remove data, logs, players
# update data, logs, players
# update player group
# remove player group
# update player characters
# remove player characters

def index(request):
    return HttpResponse("Hello, world. You're at the LogParserWebApp index.")

class DataViewSet(viewsets.ModelViewSet):
    serializer_class = DataSerializer
    queryset = Data.objects.all()


class LogsViewSet(viewsets.ModelViewSet):
    serializer_class = LogsSerializer
    queryset = Logs.objects.all()


class PlayersViewSet(viewsets.ModelViewSet):
    serializer_class = PlayersSerializer
    queryset = Players.objects.all()

class LogsWithDataView(APIView):

    def get(self, request):
        # Query Parameters
        group = self.request.query_params.get('group')
        if not group:
            group = 'Boba'

        inhouseplayers = self.request.query_params.get('inhouseplayers')
        if not inhouseplayers:
            inhouseplayers = '5'

        # Connect to database and call query
        with connection.cursor() as cursor:
            cursor.execute("""SELECT "Boss", "Duration", "Mode", "Phase", "PlayerId", "Character", "Class", "TargetDps", "PercentTargetDps", "PowerDps", "CondiDps", "LogUrl", inhouseplayers, "TotalPlayers" FROM (
                SELECT * FROM
                    (SELECT "LogUrl", "PlayerId", "Phase", count(unnestedgroup) as InHousePlayers FROM (
                            SELECT * FROM (
                                SELECT "LogUrl", "PlayerId", "Boss" , "Phase", unnest("Players") as unnestedPlayer
                                FROM public."Data" NATURAL JOIN public."Logs"
                            ) unnestedPlayersTable 
                            LEFT JOIN (
                                SELECT "PlayerId" as tempPlayer , unnest("Groups") as unnestedGroup FROM public."Players") unnestedGroupsTable 
                            ON unnestedPlayer = tempPlayer
                            WHERE unnestedGroup = %s
                            ORDER BY "LogUrl" ASC, unnestedPlayersTable."PlayerId" ASC) unnestedPlayersAndGroupsTable
                        GROUP BY "LogUrl", unnestedPlayersAndGroupsTable."PlayerId", "Phase") aggregatedInHousePlayersAll
                    NATURAL JOIN (
                        SELECT "PlayerId" , unnest("Groups") as unnestedGroup FROM public."Players") playerGroupsTable
                    WHERE unnestedGroup = %s) aggregatedInHousePlayersAll

            NATURAL JOIN (
                
                SELECT max("LogUrl") as LogUrl, "LogId", "PlayerId", "Phase", max("EliteInsightVersion") as EliteInsightVersion FROM 
                public."Data" NATURAL JOIN public."Logs"
                GROUP BY "LogId", "PlayerId", "Phase") organizedEliteInsightVersionTable
                
            NATURAL JOIN (
                SELECT * FROM public."Data" NATURAL JOIN public."Logs" 
            ) allLogsWithDataTable

            WHERE "LogUrl" = logurl AND inhouseplayers >=  %s
            ORDER BY "LogId", "PlayerId", "Phase" """, (group, group, inhouseplayers))

            leaderboard_list = cursor.fetchall()

        # Serialize result data
        serialized_logs = [LogsWithData(**{'Boss' : m[0], 'Duration' : m[1], 'Mode' : m[2], 'Phase' : m[3], 'PlayerId' : m[4], 'Character' : m[5], 'class_field' : m[6], 'TargetDps' : m[7], 'PercentTargetDps' : m[8], 'PowerDps' : m[9], 'CondiDps' : m[10], 'LogUrl' : m[11], 'InHousePlayers' : m[12], 'TotalPlayers' : m[13]}) for m in leaderboard_list]
        serializer = LogsWithDataSerializer(serialized_logs, many=True)

        return Response(serializer.data)
