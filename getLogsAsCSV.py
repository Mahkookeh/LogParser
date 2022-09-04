
import psycopg2
from datetime import datetime, timezone, timedelta
import yaml
import operator


config = yaml.safe_load(open("config.yml"))

# Current list of files
included_players_file = config["files"]["includedPlayers"]
url_list_file = config["files"]["urlList"]
log_results_file = config["files"]["logResults"]
debug_logging_file = config["files"]["debugLogging"]
accepted_boss_list_file = config["files"]["acceptedBossList"]

current_time = datetime.now().strftime("%Y%m%d_%H%M%S")


def write_to_file(output_file, header, table_list):
    # Create output file and add header line
    with open(output_file, 'w') as f:
        f.write(header)

    for line in table_list:
        with open(output_file, 'a') as f:
            f.write(f"{','.join(list(map(str, line)))}\n")


# Connect to the postgres database
def connect_database():
    conn = psycopg2.connect(database=config["databaseCredentials"]["database"],
                            host=config["databaseCredentials"]["host"],
                            user=config["databaseCredentials"]["user"],
                            password=config["databaseCredentials"]["password"],
                            port=config["databaseCredentials"]["port"])
    cursor = conn.cursor()
    cursor.execute("""SELECT table_name FROM information_schema.tables
           WHERE table_schema = 'public'""")
    return conn, cursor



def get_players_table(conn, cursor):
    player_dict = dict()
    cursor.execute("""SELECT * FROM "Players" """)
    player_list = cursor.fetchall()

    for player, groups, characters in player_list:
        player_dict.setdefault(player, []).extend([groups, characters])
    return player_dict

def get_logs_table_by_log_id(conn, cursor):
    log_dict = dict()
    cursor.execute("""SELECT * FROM "Logs" """)
    log_list = cursor.fetchall()

    for logurl, logid, boss, mode, duration, timestart, timeend, players, totalplayers, eliteinsightversion in log_list:
        log_dict.setdefault(logid, []).extend([[logurl, boss, mode, duration, timestart, timeend, players, totalplayers, eliteinsightversion]])
    return log_dict

def get_logs_table_by_log_url(conn, cursor):
    log_dict = dict()
    cursor.execute("""SELECT * FROM "Logs" """)
    log_list = cursor.fetchall()

    for logurl, logid, boss, mode, duration, timestart, timeend, players, totalplayers, eliteinsightversion in log_list:
        log_dict.setdefault(logurl, []).extend([logid, boss, mode, duration, timestart, timeend, players, totalplayers, eliteinsightversion])
    return log_dict

def get_data_table_by_log_url(conn, cursor):
    data_dict = dict()
    cursor.execute("""SELECT * FROM "Data" """)
    data_list = cursor.fetchall()

    for logurl, logid, playerid, character, gw2class, phase, targetdps, percenttargetdps, powerdps, condidps in data_list:
        data_dict.setdefault((logurl, playerid, phase), []).extend([[logurl, logid, playerid, character, gw2class, phase, targetdps, percenttargetdps, powerdps, condidps]])
    return data_dict

def get_data_table_by_log_id(conn, cursor):
    data_dict = dict()
    cursor.execute("""SELECT * FROM "Data" """)
    data_list = cursor.fetchall()

    for logurl, logid, playerid, character, gw2class, phase, targetdps, percenttargetdps, powerdps, condidps in data_list:
        data_dict.setdefault((logid, playerid, phase), []).extend([[logurl, playerid, character, gw2class, phase, targetdps, percenttargetdps, powerdps, condidps]])
    return data_dict



def get_custom_leaderboard_table_by_log_url(conn, cursor):

    cursor.execute("""SELECT "LogId", "Boss", "Duration", "Mode", "Phase", "PlayerId", "Character", "Class", "TargetDps", "PercentTargetDps", "PowerDps", "CondiDps", "LogUrl", "inhouseplayers", "TotalPlayers" FROM(
        SELECT * FROM 
        (SELECT * FROM (SELECT "LogId", "PlayerId", "Phase", max("EliteInsightVersion") as "EliteInsightVersion"  FROM public."Data" NATURAL JOIN public."Logs"
        Group by "LogId", "PlayerId", "Phase") x LEFT JOIN (SELECT "PlayerId" as tempPlayer , unnest("Groups") as unnestedGroup FROM public."Players") y
        ON "PlayerId" = tempPlayer
        WHERE unnestedGroup = 'Boba') t NATURAL JOIN (SELECT * FROM public."Data" NATURAL JOIN public."Logs") m ORDER BY "TargetDps" DESC) FilteredData
        NATURAL JOIN 
        (SELECT "LogUrl", "PlayerId", "Phase", count(unnestedgroup) as InHousePlayers FROM (
        SELECT * FROM (
        SELECT "LogUrl", "PlayerId", "Boss" , "Phase", unnest("Players") as unnestedPlayer
        FROM public."Data" NATURAL JOIN public."Logs" where "Boss" = 'Sabetha the Saboteur'
        ) t LEFT JOIN (SELECT "PlayerId" as tempPlayer , unnest("Groups") as unnestedGroup FROM public."Players") j 
        ON unnestedPlayer = tempPlayer
        WHERE unnestedGroup = 'Boba'
        ORDER BY "LogUrl" ASC, t."PlayerId" ASC) q
        GROUP BY "LogUrl", q."PlayerId", "Phase") InHouseData where inhouseplayers >= %s""", ('5'))


    leaderboard_dict = dict()
    leaderboard_list = cursor.fetchall()

    for logid, boss, duration, mode, phase, playerid, character, gw2class, targetdps, percenttargetdps, powerdps, condidps, logurl, inhouseplayers, totalplayers in data_list:
        leaderboard_dict.setdefault((logurl, playerid, phase), []).extend([[logid, boss, duration, mode, phase, playerid, character, gw2class, targetdps, percenttargetdps, powerdps, condidps, inhouseplayers, totalplayers]])
    return leaderboard_dict




def get_custom_leaderboard_table(conn, cursor):

    cursor.execute("""SELECT "LogId", "Boss", "Duration", "Mode", "Phase", "PlayerId", "Character", "Class", "TargetDps", "PercentTargetDps", "PowerDps", "CondiDps", "LogUrl", "inhouseplayers", "TotalPlayers", "EliteInsightVersion" FROM(
        SELECT * FROM 
        (SELECT * FROM (SELECT "LogId", "PlayerId", "Phase", max("EliteInsightVersion") as "EliteInsightVersion"  FROM public."Data" NATURAL JOIN public."Logs"
        Group by "LogId", "PlayerId", "Phase") x LEFT JOIN (SELECT "PlayerId" as tempPlayer , unnest("Groups") as unnestedGroup FROM public."Players") y
        ON "PlayerId" = tempPlayer
        WHERE unnestedGroup = 'Boba') t NATURAL JOIN (SELECT * FROM public."Data" NATURAL JOIN public."Logs") m ORDER BY "TargetDps" DESC) FilteredData
        NATURAL JOIN 
        (SELECT "LogUrl", "PlayerId", "Phase", count(unnestedgroup) as InHousePlayers FROM (
        SELECT * FROM (
        SELECT "LogUrl", "PlayerId", "Boss" , "Phase", unnest("Players") as unnestedPlayer
        FROM public."Data" NATURAL JOIN public."Logs"
        ) t LEFT JOIN (SELECT "PlayerId" as tempPlayer , unnest("Groups") as unnestedGroup FROM public."Players") j 
        ON unnestedPlayer = tempPlayer
        WHERE unnestedGroup = 'Boba'
        ORDER BY "LogUrl" ASC, t."PlayerId" ASC) q
        GROUP BY "LogUrl", q."PlayerId", "Phase") InHouseData where inhouseplayers >= %s""", ('5'))


    leaderboard_dict_by_id = dict()
    leaderboard_dict_by_url = dict()
    leaderboard_list = cursor.fetchall()

    for logid, boss, duration, mode, phase, playerid, character, gw2class, targetdps, percenttargetdps, powerdps, condidps, logurl, inhouseplayers, totalplayers, eliteinsightversion in leaderboard_list:
        leaderboard_dict_by_id.setdefault((logid, playerid, phase), []).extend([[boss, duration, mode, phase, playerid, character, gw2class, targetdps, percenttargetdps, powerdps, condidps, logurl, inhouseplayers, totalplayers, eliteinsightversion]])
        leaderboard_dict_by_url.setdefault((logurl, playerid, phase), []).extend([[logid, boss, duration, mode, phase, playerid, character, gw2class, targetdps, percenttargetdps, powerdps, condidps, inhouseplayers, totalplayers, eliteinsightversion]])

    return leaderboard_dict_by_id, leaderboard_dict_by_url

conn, cursor = connect_database()
players_table = get_players_table(conn, cursor)
log_id_table = get_logs_table_by_log_id(conn, cursor)
log_url_table = get_logs_table_by_log_url(conn, cursor)
data_log_id_table = get_data_table_by_log_id(conn, cursor)
data_log_url_table = get_data_table_by_log_url(conn, cursor)
custom_log_id_table, custom_log_url_table = get_custom_leaderboard_table(conn, cursor)

print(len(custom_log_url_table))

max_custom_log_id_table = []
for k, v in custom_log_id_table.items():
    max_custom_log_id_table.append(sorted(v, key=operator.itemgetter(14, 11), reverse=True)[0][:-1])
# print(max_custom_log_id_table)
# print(len(max_custom_log_id_table))



output_file = "test.csv"
header = "Boss, Duration, Mode, Phase, Player Id, Character, Class, "\
            "Target DPS, % Target DPS, Power DPS, Condi DPS, "\
            "Log Url, In-House Players, Total Players\n"
write_to_file(output_file, header, max_custom_log_id_table)