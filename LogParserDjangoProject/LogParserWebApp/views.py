import csv
import io
import json
from .forms import NewUserForm
from .models import (
    Data, 
    Player, 
    Log, 
    LogsWithData)
from .revisedlogparsehelper import log_parser_helper
from .serializers import (
    DataSerializer, 
    PlayerSerializer, 
    LogSerializer, 
    LogsWithDataSerializer, 
    GroupSerializer, 
    LogsWithDataJsonSerializer)
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import (
    login, 
    authenticate, 
    logout)
from django.contrib.auth.forms import (
    AuthenticationForm, 
    PasswordResetForm)
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import SuspiciousOperation
from django.core.mail import (
    send_mail, 
    BadHeaderError)
from django.db import connection
from django.db.models.query_utils import Q
from django.http import (
    HttpRequest,
    HttpResponse, 
    HttpResponseBadRequest, 
    JsonResponse)
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from drf_spectacular.utils import (
    extend_schema, 
    OpenApiParameter, 
    OpenApiExample, 
    OpenApiResponse)
from rest_framework import (
    viewsets, 
    mixins, 
    status)
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_csv.renderers import CSVRenderer


def index(request: HttpRequest) -> HttpResponse:    
    ''' Default Index View ''' 
    return render (request=request, template_name="LogParserWebApp/homepage.html")


def register_request(request: HttpRequest) -> HttpResponse:
    ''' 
    Register Account Request
        Supports following API routes:
            GET - Create new user form
            POST - Generate new user with information in user form
    '''  
    if request.method == "POST":
        form = NewUserForm(request.POST)
        print(form.errors)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful." )
            return redirect("index")
        messages.error(request, "Unsuccessful registration. Invalid information.")
    form = NewUserForm()
    return render (request=request, template_name="LogParserWebApp/register.html", context={"register_form":form})


def login_request(request: HttpRequest) -> HttpResponse:
    ''' 
    Login Account Request
        Supports following API routes:
            GET - Creates new authentication form
            POST - Authenticates user with information in authentication form
    '''  
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"You are now logged in as {username}.")
                return redirect("index")
            else:
                messages.error(request,"Invalid username or password.")
        else:
            messages.error(request,"Invalid username or password.")
    form = AuthenticationForm()
    return render(request=request, template_name="LogParserWebApp/login.html", context={"login_form":form})


def logout_request(request: HttpRequest) -> HttpResponse:
    ''' 
    Logout Account Request
        Supports following API routes:
            GET - Logs out current user
    '''  
    logout(request)
    messages.info(request, "You have successfully logged out.") 
    return redirect("../login")


def password_reset_request(request: HttpRequest) -> HttpResponse:
    ''' 
    Password Reset Request
        Supports following API routes:
            GET - Creates new password reset form
            POST - Creates a password reset message containing link to reset password 
    '''  
    if request.method == "POST":
        password_reset_form = PasswordResetForm(request.POST)
        if password_reset_form.is_valid():
            data = password_reset_form.cleaned_data['email']
            associated_users = User.objects.filter(Q(email=data))
            if associated_users.exists():
                for user in associated_users:
                    subject = "Password Reset Requested"
                    email_template_name = "LogParserWebApp/password/password_reset_email.txt"
                    c = {
                    "email":user.email,
                    'domain':'127.0.0.1:8000',
                    'site_name': 'Website',
                    "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                    "user": user,
                    'token': default_token_generator.make_token(user),
                    'protocol': 'http',
                    }
                    email = render_to_string(email_template_name, c)
                    try:
                        send_mail(subject, email, 'admin@example.com' , [user.email], fail_silently=False)
                    except BadHeaderError:
                        return HttpResponse('Invalid header found.')
                    messages.success(request, 'A message with reset password instructions has been sent to your inbox.')
                    return redirect ("/password_reset/done/")
            messages.error(request, 'An invalid email has been entered.')
    password_reset_form = PasswordResetForm()
    return render(request=request, template_name="LogParserWebApp/password/password_reset.html", context={"password_reset_form":password_reset_form})


class DataViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    ''' 
    Data list API View
        Supports following API routes:
            GET - Gets list of log data (TODO: Fill in columns)
            POST - Takes 'LogUrl' as a query parameter and retrieves data for that log
    '''
    queryset = Data.objects.all()
    serializer_class = DataSerializer

    @extend_schema(
        summary='Get all log data',
        description='Get a list containing all log data',
        request=DataSerializer,
        responses={
            201: OpenApiResponse(response=DataSerializer, description='Retrieved. Resource in response.'),
            400: OpenApiResponse(description='Bad request (something invalid)')
        },
    )
    def list(self, request: HttpRequest) -> HttpResponse:
        ''' 
        GET Request for all log data
            Returns
                List of Log Data
        '''
        return super().list(request)

    @extend_schema(
        summary='Get specific log data',
        description='Get all log data specific to LogUrl.',
        operation_id='request_data',
        request={
            'application/json': {
                'schema': {
                    'LogUrl': {
                        'type': 'string',
                        }

                    },
                },
            },
        responses={
            201: OpenApiResponse(response=DataSerializer, description='Retrieved. Resource in response.'),
            400: OpenApiResponse(description='Bad request (something invalid)')
        },
        examples=[
            OpenApiExample(
                'Example',
                summary='GET Log data by LogUrl',
                description='GET all Log data, associated groups, and all character names corresponding to LogUrl dps.report/abcd',
                value={'LogUrl' : 'dps.report/abcd'}
            ),]
    )
    def create(self, request: HttpRequest) -> HttpResponse:
        ''' 
        POST Request for specific log data
            Takes in data from request body:
                'LogUrl' - URL of log to retrieve data for
        '''
        if 'LogUrl' in request.data:
            url = request.data['LogUrl']
            queryset = Data.objects.filter(LogUrl=url).all()
            if queryset:
                serializers = self.get_serializer(queryset, many=True)
                return(Response(serializers.data))
            else:
                return HttpResponse(content=f"Log with url ({url}) not found.", status=204)
        else:
            return HttpResponseBadRequest("Missing Log Url")


class LogViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    ''' 
    Logs list API View
        Supports following API routes:
            GET - Gets list of logs (LogId, LogId, Boss, Mode, Duration, TimeStart, TimeEnd, Players, TotalPlayers, EliteInsightVersion)
            POST - Takes 'LogUrl' as a query parameter and retrieves data for that log
    ''' 
    queryset = Log.objects.all()    
    serializer_class = LogSerializer

    @extend_schema(
        summary='Get all logs',
        description='Get a list containing all logs.',
        request=LogSerializer,
        responses={
            201: OpenApiResponse(response=LogSerializer, description='Retrieved. Resource in response.'),
            400: OpenApiResponse(description='Bad request (something invalid)')
        },
    )
    def list(self, request: HttpRequest) -> HttpResponse:
        ''' 
        GET Request for specific log data
            Returns
                List of Log Data
        '''    
        return super().list(request)

    @extend_schema(
        summary='Get specific log',
        description='Get specific log by LogUrl',
        operation_id='request_log',
        request={
            'application/json': {
                'schema': {
                    'LogUrl': {
                        'type': 'string',
                        }

                    },
                },
            },
        responses={
            201: OpenApiResponse(response=LogSerializer, description='Retrieved. Resource in response.'),
            400: OpenApiResponse(description='Bad request (something invalid)')
        },
        examples=[
            OpenApiExample(
                'Example',
                summary='GET Log data by LogUrl',
                description='GET Log data corresponding to LogUrl dps.report/abcd.',
                value={'LogUrl' : 'dps.report/abcd'}
            ),]
    )   
    def create(self, request: HttpRequest) -> HttpResponse:
        
        ''' 
        POST Request for specific log
            Takes in data from request body:
                'LogUrl' - URL of log to retrieve data for
        '''
        if 'LogUrl' in request.data:
            url = request.data['LogUrl']
            queryset = Log.objects.filter(LogUrl=url).first()
            if queryset:
                serializers = self.get_serializer(queryset)
                return(Response(serializers.data))
            else:
                return HttpResponse(content=f"Log with url ({url}) not found.", status=204)
        else:
            return HttpResponseBadRequest("Missing Log Url")


class PlayerViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    ''' 
    Player list API View
        Supports following API routes:
            GET - Gets list of players (PlayerId, Groups, Characters)
            POST - Takes 'PlayerId' as a query parameter and retrieves data for that player
            PATCH - Takes list of groups and adds to player's current list of groups
    ''' 
    lookup_value_regex = '[\w.]+'
    queryset = Player.objects.all()
    serializer_class = PlayerSerializer
    http_method_names = ["get", "post", "patch"]

    @extend_schema(
        summary='Get specific player data',
        description='Get specific player data by PlayerId.',
        request=PlayerSerializer,
        responses={
            201: OpenApiResponse(response=PlayerSerializer, description='Retrieved. Resource in response.'),
            400: OpenApiResponse(description='Bad request (something invalid)')
        },
    )
    def retrieve(self, request: HttpRequest) -> HttpResponse:
        ''' 
        GET Request for specific player data
            Returns
                Specific Player
        '''
        return super().retrieve(request)

    @extend_schema(
        summary='Get all players',
        description='Get a list containing all players.',
        request=PlayerSerializer,
        responses={
            201: OpenApiResponse(response=PlayerSerializer, description='Retrieved. Resource in response.'),
            400: OpenApiResponse(description='Bad request (something invalid)')
        },
    )
    def list(self, request: HttpRequest) -> HttpResponse:
        ''' 
        GET Request for list of players
            Returns
                List containing all players
        '''
        return super().list(request)

    @extend_schema(
        summary='Add group to player',
        description='Add a group to the list of groups associated with player with PlayerId.',
        operation_id='update_player_group',
        request={
            'application/json': {
                'schema': {
                    'Groups': {
                        'type': 'string',
                        }

                    },
                },
            },
        responses={
            201: OpenApiResponse(response=PlayerSerializer, description='Updated. Updated resource in response.'),
            400: OpenApiResponse(description='Bad request (something invalid)')
        },
        examples=[
            OpenApiExample(
                'Example',
                summary='Update Groups of Player by PlayerId.',
                description='Add a group to the list of groups associated with player with PlayerId player.1234',
                value={'Groups' : ['GroupName']}
            ),]
    )
    def partial_update(self, request: HttpRequest, pk: str) -> HttpResponse:
        ''' 
        PATCH Request for player
            Takes in data from request body:
                'Groups' - List of groups to add to player
        '''
        player = Player.objects.get(pk=pk)
        print(player)
        group_serializer = GroupSerializer(player, data=request.data, partial=True)
        # retrieved_player = Player.objects.filter(PlayerId=player_id).first()
        if group_serializer.is_valid():
            print("is valid")
            group_serializer.save()
            player = Player.objects.get(pk=pk)
            player_serializer = PlayerSerializer(player)
            return Response(player_serializer.data, status=status.HTTP_200_OK)
        print("not valid")
        return Response(status=status.HTTP_400_BAD_REQUEST)


# Leaderboard API View
class LogsWithDataView(APIView):
    ''' 
    Logs with Data list API View
        Supports following API routes:
            GET - Gets list of all logs  (PlayerId, Groups, Characters)
            POST - Takes 'PlayerId' as a query parameter and retrieves data for that player
    ''' 
    # Set renderer class to include CSV support
    serializer_class = LogsWithDataSerializer
    renderer_classes = [CSVRenderer]
    parser_classes = [MultiPartParser]

    # Create custom renderer context getter to set order of resulting columns
    def get_renderer_context(self):
        context = super().get_renderer_context()
        context['header'] = (
                self.request.GET['fields'].split(',')
                if 'fields' in self.request.GET else None)
        return context
        
    @extend_schema(
        summary='Upload and parse files',
        description='Upload list of files and phase configuration and parse all contained urls.',
        operation_id='upload_file',
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'Url List': {
                        'type': 'file',
                        'format': 'binary'
                        },
                    'Phase Config': {
                        'type': 'file',
                        'format': 'binary'
                        },

                    },
                },
            },
        responses={
            201: OpenApiResponse(response=LogsWithDataJsonSerializer, description='Retrieved. Resource in response.'),
            400: OpenApiResponse(description='Bad request (something invalid)')
        },
    )
    
    def post(self, request: HttpRequest, format: str = None) -> HttpResponse:
        ''' 
        POST Request to upload data from dps reports
            Takes in data from request body:
                'urlList.txt' - File containing list of all urls to parse
                'phases.json' - File containing configuration of phases to parse each log for 
        '''
        parser_classes = (MultiPartParser,)
        
        # Grab Url List file
        # Convert InMemoryUploadedFile to string
        # Convert string to IOStream
        # Convert IOStream to CSV reader
        urlListFile = request.FILES.get('Url List')
        if urlListFile is None:
            return HttpResponseBadRequest("Missing Url List")
        decoded_file = urlListFile.read().decode()
        io_string = io.StringIO(decoded_file)
        reader = csv.reader(io_string)
        url_list = [x[0] for x in list(reader)]
        if len(url_list) > 50:
            return HttpResponseBadRequest("List of may contain at most 50 urls.")

        # Grab Phase Config file
        # Convert InMemoryUploadedFile to string
        # Convert phases json file to dictionary
        phaseConfigFile = request.FILES.get('Phase Config',  None)
        if phaseConfigFile is None:
            file_location = settings.BASE_DIR / 'static/phaseConfig.json'
            with open(file_location) as json_data:
                phase_config = json.load(json_data)
        else:
            decoded_file = phaseConfigFile.read().decode()
            phase_config = json.loads(decoded_file)

        # Try parse urls with given phase config 
        with connection.cursor() as cursor:
            try:
                results = log_parser_helper(connection, cursor, url_list, phase_config)
            except Exception as e:
                raise SuspiciousOperation('Failed to do something: %s' % str(e))
    
        return JsonResponse(results)

    @extend_schema(
        summary='Get logs with data as csv',
        description='Get CSV file containing all processed logs with data (leaderboard).',
        operation_id='get_leaderboard',
        parameters=[
            OpenApiParameter(name='group', description='Name of Group  (Default: Boba)', type=str),
            OpenApiParameter(name='inhouseplayers', description='Number of In House Players to query for (Default: 5)', type=int),
        ],
        responses={
            201: OpenApiResponse(response=LogsWithDataSerializer, description='Retrieved. Resource in response.'),
            400: OpenApiResponse(description='Bad request (something invalid)')
        },
    )   
    def get(self, request: HttpRequest, format: str = None) -> HttpResponse:
        ''' 
        Get Request for Logs with Data (leaderboard)
            Takes in query params:
                'group' - What group to query the leaderboard for
                'InHousePlayers - Minimum number of group members allowed in queried logs
        '''
        # Query Parameters
        group = self.request.query_params.get('group')
        if not group:
            group = 'Boba'

        inhouseplayers = self.request.query_params.get('inhouseplayers')
        if not inhouseplayers:
            inhouseplayers = '5'
        if int(inhouseplayers) < 0 or int(inhouseplayers) > 10:
            return HttpResponseBadRequest("Invalid number of in-house players.")

        given_fields = self.request.query_params.get('fields')
        if not given_fields:
            default_fields = 'Boss,Duration,Mode,Phase,PlayerId,Character,Class,TargetDps,PercentTargetDps,PowerDps,CondiDps,LogUrl,InHousePlayers,TotalPlayers'
            context = super().get_renderer_context()
            context['header'] = (default_fields.split(','))

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
