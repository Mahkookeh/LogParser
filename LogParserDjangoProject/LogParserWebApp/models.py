# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from django.contrib.postgres.fields import ArrayField



class Data(models.Model):
    LogUrl = models.TextField(db_column='LogUrl', primary_key=True)  
    LogId = models.TextField(db_column='LogId', blank=True, null=True)  
    PlayerId = models.TextField(db_column='PlayerId')  
    Character = models.TextField(db_column='Character', blank=True, null=True)  
    Class = models.TextField(db_column='Class', blank=True, null=True)   
    Phase = models.TextField(db_column='Phase')  
    TargetDps = models.IntegerField(db_column='TargetDps', blank=True, null=True)  
    PercentTargetDps = models.TextField(db_column='PercentTargetDps', blank=True, null=True)  
    PowerDps = models.IntegerField(db_column='PowerDps', blank=True, null=True)  
    CondiDps = models.IntegerField(db_column='CondiDps', blank=True, null=True)  

    # ...
    def __str__(self):
        return self.LogUrl, self.PlayerId, self.Phase

    class Meta:
        managed = False
        db_table = 'Data'
        unique_together = (('LogUrl', 'PlayerId', 'Phase'),)


class Log(models.Model):
    LogUrl = models.TextField(db_column='LogUrl', primary_key=True)  
    LogId = models.TextField(db_column='LogId')  
    Boss = models.TextField(db_column='Boss')  
    Mode = models.TextField(db_column='Mode', blank=True, null=True)  
    Duration = models.DurationField(db_column='Duration', blank=True, null=True)  
    TimeStart = models.DateTimeField(db_column='TimeStart', blank=True, null=True)  
    TimeEnd = models.DateTimeField(db_column='TimeEnd', blank=True, null=True)  
    Players = ArrayField(models.TextField(db_column='Players', blank=True, null=True))  
    TotalPlayers = models.IntegerField(db_column='TotalPlayers', blank=True, null=True)  
    EliteInsightVersion = models.TextField(db_column='EliteInsightVersion', blank=True, null=True)  

    # ...
    def __str__(self):
        return self.LogUrl

    class Meta:
        managed = False
        db_table = 'Logs'


class Player(models.Model):
    PlayerId = models.TextField(db_column='PlayerId', primary_key=True)  
    Groups = ArrayField(models.TextField(db_column='Groups', blank=True, null=True))
    Characters = ArrayField(models.TextField(db_column='Characters', blank=True, null=True)) 

    # ...
    def __str__(self):
        return self.PlayerId

    class Meta:
        managed = False
        db_table = 'Players'


class LogsWithData(models.Model):
    Boss = models.TextField(db_column='Boss')  
    Duration = models.DurationField(db_column='Duration', blank=True, null=True)  
    Mode = models.TextField(db_column='Mode', blank=True, null=True)  
    Phase = models.TextField(db_column='Phase')  
    PlayerId = models.TextField(db_column='PlayerId')  
    Character = models.TextField(db_column='Character', blank=True, null=True)  
    Class = models.TextField(db_column='Class', blank=True, null=True)   
    TargetDps = models.IntegerField(db_column='TargetDps', blank=True, null=True)  
    PercentTargetDps = models.TextField(db_column='PercentTargetDps', blank=True, null=True)  
    PowerDps = models.IntegerField(db_column='PowerDps', blank=True, null=True)  
    CondiDps = models.IntegerField(db_column='CondiDps', blank=True, null=True)  
    LogUrl = models.TextField(db_column='LogUrl', primary_key=True)  
    InHousePlayers = models.IntegerField(db_column='InHousePlayers', blank=True, null=True)  
    TotalPlayers = models.IntegerField(db_column='TotalPlayers', blank=True, null=True)  

    # ...
    def __str__(self):
        return self.LogUrl, self.PlayerId, self.Phase

    class Meta:
        managed = False


class LogsWithDataJson(models.Model):
    Successful = ArrayField(models.TextField(blank=True, null=True), primary_key=True)
    Unsuccessful = ArrayField(models.TextField(blank=True, null=True)) 

    class Meta:
        managed = False
        unique_together = (('Successful', 'Unsuccessful'),)


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.SmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'
