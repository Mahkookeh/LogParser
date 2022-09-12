from django.shortcuts import render
from django.db import connection
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseBadRequest, JsonResponse
from django.http.multipartparser import MultiPartParser
from django.core.exceptions import SuspiciousOperation
from rest_framework import viewsets, mixins, status, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination
from rest_framework_csv.renderers import CSVRenderer
from .models import Data, Players, Logs, LogsWithData
from .serializers import DataSerializer, PlayersSerializer, LogsSerializer, LogsWithDataSerializer
from django.core.paginator import Paginator
import operator
import itertools
from django.utils.dateparse import parse_duration
import csv
import io
from .revisedlogparsehelper import log_parser_helper
from drf_yasg.utils import swagger_auto_schema
import json


''' Default Index View ''' 
def index(request):
    return HttpResponse("Hello, world. You're at the LogParserWebApp index.")


''' Data list API View
#   Supports API routes
#       GET - Gets list of log data (TODO: Fill in columns)
#       POST - Takes 'LogUrl' as a query parameter and retrieves data for that log
''' 
class DataViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = DataSerializer
    queryset = Data.objects.all()

    ''' POST Request for specific log data
    # Takes in data from request body:
    #   'LogUrl' - URL of log to retrieve data for
    '''
    def create(self, request):
        if 'LogUrl' in request.data:
            url = request.data['LogUrl']
            queryset = Data.objects.filter(LogUrl=url).first()
            if queryset:
                serializers = self.get_serializer(queryset)
                return(Response(serializers.data))
            else:
                return HttpResponse(content=f"Log with url ({url}) not found.", status=204)
        else:
            return HttpResponseBadRequest("Missing Log Url")


''' Logs list API View
#   Supports API routes
#       GET - Gets list of logs (LogId,  TODO: Fill in columns)
#       POST - Takes 'LogUrl' as a query parameter and retrieves data for that log
''' 
class LogsViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = LogsSerializer
    queryset = Logs.objects.all()    

    ''' POST Request for specific log
    # Takes in data from request body:
    #   'LogUrl' - URL of log to retrieve data for
    '''
    def create(self, request):
        if 'LogUrl' in request.data:
            url = request.data['LogUrl']
            queryset = Logs.objects.filter(LogUrl=url).first()
            if queryset:
                serializers = self.get_serializer(queryset)
                return(Response(serializers.data))
            else:
                return HttpResponse(content=f"Log with url ({url}) not found.", status=204)
        else:
            return HttpResponseBadRequest("Missing Log Url")


''' Player list API View
#   Supports API routes
#       GET - Gets list of players (PlayerId, Groups, Characters)
#       POST - Takes 'PlayerId' as a query parameter and retrieves data for that player
''' 
class PlayersViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = PlayersSerializer
    queryset = Players.objects.all()

    ''' POST Request for specific player
    # Takes in data from request body:
    #   'PlayerId' - PlayerId of player to retrieve data for
    '''
    def create(self, request):
        if 'PlayerId' in request.data:
            player_id = request.data['PlayerId']
            queryset = Players.objects.filter(PlayerId=player_id).first()
            if queryset:
                serializers = self.get_serializer(queryset)
                return(Response(serializers.data))
            else:
                return HttpResponse(content=f"Player with PlayerId ({player_id}) not found.", status=204)
        else:
            return HttpResponseBadRequest("Missing PlayerId")


# Leaderboard API View
''' Logs with Data list API View
#   Supports API routes
#       GET - Gets list of all logs  (PlayerId, Groups, Characters)
#       POST - Takes 'PlayerId' as a query parameter and retrieves data for that player
''' 
class LogsWithDataView(APIView):
    # Set renderer class to include CSV support
    renderer_classes = [CSVRenderer]
    # Create custom renderer context getter to set order of resulting columns
    def get_renderer_context(self):
        context = super().get_renderer_context()
        context['header'] = (
                self.request.GET['fields'].split(',')
                if 'fields' in self.request.GET else None)
        return context
        
    ''' POST Request to upload data from dps reports
    # Takes in data from request body:
    #   'urlList.txt' - File containing list of all urls to parse
    #   'phases.json' - File containing configuration of phases to parse each log for 
    '''
    # @swagger_auto_schema(operation_description='Upload file...',)
    def post(self, request, format=None):
        parser_classes = (MultiPartParser,)
        files_list = request.data.getlist('file')
        url_list = None
        phases = None
        for file in files_list:
            # Check for file containing list of urls to parse
            if file.name == 'urlList.txt':
                # Convert InMemoryUploadedFile to string
                # Convert string to IOStream
                # Convert IOStream to CSV reader
                decoded_file = file.read().decode()
                io_string = io.StringIO(decoded_file)
                reader = csv.reader(io_string)
                url_list = [x[0] for x in list(reader)]
                if len(url_list) > 50:
                    return HttpResponseBadRequest("List of may contain at most 50 urls.")
            # Check for phase configuration file
            if file.name == 'phaseConfig.json':
                # Convert InMemoryUploadedFile to string
                # Convert phases json file to dictionary
                decoded_file = file.read().decode()
                phase_config = json.loads(decoded_file)
        # Try parse urls with given phase config 
        with connection.cursor() as cursor:
            try:
                results = log_parser_helper(connection, cursor, url_list, phase_config)
            except Exception as e:
                raise SuspiciousOperation('Failed to do something: %s' % str(e))
    
        return JsonResponse(results)

    ''' Get Request for Logs with Data (leaderboard)
    # Takes in query params:
    #   'group' - What group to query the leaderboard for
    #   'InHousePlayers - Minimum number of group members allowed in queried logs
    '''
    def get(self, request, format=None):
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
        serialized_logs = [LogsWithData(**{'Boss' : m[0], 'Duration' : m[1], 'Mode' : m[2], 'Phase' : m[3], 'PlayerId' : m[4], 'Character' : m[5], 'Class' : m[6], 'TargetDps' : m[7], 'PercentTargetDps' : m[8], 'PowerDps' : m[9], 'CondiDps' : m[10], 'LogUrl' : m[11], 'InHousePlayers' : m[12], 'TotalPlayers' : m[13]}) for m in leaderboard_list]
        serializer = LogsWithDataSerializer(serialized_logs, many=True)
        return Response(serializer.data)
