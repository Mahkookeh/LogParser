import gc
import json
import logging
import pytz
import uuid
from bs4 import (
    BeautifulSoup, 
    SoupStrainer)
from datetime import (
    datetime, 
    timedelta)
from typing import Tuple
from urllib.request import (
    Request, 
    urlopen)


# Generate random uuid4 as a log id
def generate_log_id():
    return str(uuid.uuid4())


# Add log to Logs table
def add_log_to_table(conn, cursor, log_url: str, log_id: str, boss_name: str, mode: str, duration: str, time_start_timestamp: datetime, time_end_timestamp: datetime, players_list: "list[str]", total_player_count: int, elite_insights_version: str) -> str:
    log_id = check_log_equality(cursor, log_id, boss_name, duration, time_start_timestamp, time_end_timestamp, players_list)
    cursor.execute("""INSERT INTO "Logs" ("LogUrl", "LogId", "Boss", "Mode", "Duration", "TimeStart", "TimeEnd", "Players", "TotalPlayers", "EliteInsightVersion") VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT ("LogUrl") WHERE ("LogUrl" = %s) DO NOTHING""", (log_url, log_id, boss_name, mode, duration, time_start_timestamp, time_end_timestamp, players_list, total_player_count, elite_insights_version, log_url))
    conn.commit() 
    return log_id


# Add player to Players table
def add_player_to_table(conn, cursor, player_id: str, player_character: str) -> None:
    group_name = ''
    cursor.execute("""INSERT INTO "Players" ("PlayerId", "Groups", "Characters") VALUES (%s, ARRAY [%s], ARRAY [%s]) ON CONFLICT ("PlayerId") DO UPDATE SET "Groups" = CASE WHEN %s = ANY("Players"."Groups") THEN "Players"."Groups" ELSE array_append("Players"."Groups", %s) END, "Characters" = CASE WHEN %s = ANY("Players"."Characters") THEN "Players"."Characters" ELSE array_append("Players"."Characters", %s) END""", (player_id, group_name, player_character, group_name, group_name, player_character, player_character))
    conn.commit() 


# Add player to Players table
def add_data_to_table(conn, cursor, log_url: str, log_id: str, player_id: str, player_character: str, player_class: str, current_phase: str, player_target_dps: int, player_percent_target_dps: str, player_power_dps: int, player_condi_dps: int) -> None:
    cursor.execute("""INSERT INTO "Data" ("LogUrl", "LogId", "PlayerId", "Character", "Class", "Phase", "TargetDps", "PercentTargetDps", "PowerDps", "CondiDps") VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT ("LogUrl", "PlayerId", "Phase") WHERE ("LogUrl" = %s, "PlayerId" = %s, "Phase" = %s) DO NOTHING""", (log_url, log_id, player_id, player_character, player_class, current_phase, player_target_dps, player_percent_target_dps, player_power_dps, player_condi_dps, log_url, player_id, current_phase))
    conn.commit() 


# Check if two logs are the same fight
def check_log_equality(cursor, log_id: str, boss_name: str, duration: str, time_start_timestamp: datetime, time_end_timestamp: datetime, players_list: "list[str]") -> str:    
    duration_datetime = datetime.strptime(duration, "%Mm %Ss %fms")
    duration_timedelta = timedelta(minutes=duration_datetime.minute,
                                seconds=duration_datetime.second,
                                microseconds=duration_datetime.microsecond)
    duration_minus5 = duration_timedelta - timedelta(seconds=5)
    duration_plus5 = duration_timedelta + timedelta(seconds=5)
    time_start_minus5 = time_start_timestamp - timedelta(seconds=5)
    time_start_plus5 = time_start_timestamp + timedelta(seconds=5)
    time_end_minus5 = time_end_timestamp - timedelta(seconds=5)
    time_end_plus5 = time_end_timestamp + timedelta(seconds=5)

    cursor.execute("""SELECT "LogId", "LogUrl",  "Players" FROM "Logs" where "Logs"."Boss" = %s AND "Logs"."Duration" BETWEEN %s::interval AND %s::interval AND "Logs"."TimeStart" BETWEEN %s AND %s AND "Logs"."TimeEnd" BETWEEN %s AND %s""", (boss_name, duration_minus5, duration_plus5, time_start_minus5, time_start_plus5, time_end_minus5, time_end_plus5))
    log_equality_list = cursor.fetchall()

    new_log_id = log_id
    for log_equality_value in log_equality_list:
        print(log_equality_value)
        logging.info(log_equality_value)
        log_equality_id, log_equality_url, log_equality_players = log_equality_value
        if set(players_list) == set(log_equality_players):
            print(f"Found a duplicate log {log_equality_url} with id {log_equality_id}")
            logging.info(f"Found a duplicate log {log_equality_url} with id {log_equality_id}")
            new_log_id = log_equality_id
            break

    return new_log_id


# Grab log data value from script in URL html
def get_scripts_from_url(URL: str) -> dict:
    page_source = None
    try:
        # Connect to the website
        request = Request(URL)
        request.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36')
        with urlopen(request) as url:
            page_source = url.read()
    except Exception as ex:
        print("Failed to load website.")
        return None

    only_script_tags = SoupStrainer('script')
    soup = BeautifulSoup(page_source, "html.parser", parse_only=only_script_tags)

    logDataDict = None
    scripts = soup.find_all('script')

    # Iterate through each script tag and find the script that contains the _logData variable
    for s in scripts:
        if '_logData = ' in s.text:
            script = s.text  
            script = script.split('_logData = ')[1]
            script = script.split(';')[0]

            jsonStr = script
            logDataDict = json.loads(jsonStr)
            del jsonStr
            gc.collect()
        s.decompose()
    soup.decompose()

    return logDataDict


# Extract useful data from dictioanry before destroying it
def extract_useful_data_from_dict(logDataDict: dict) -> Tuple[bool, datetime, datetime, str, str, str, "list[str]", "list[dict]", "list[dict]", "list[dict]"]:
    # Success
    success = logDataDict['success']

    # TimeStart
    time_start = logDataDict['encounterStart']
    # TimeEnd
    time_end = logDataDict['encounterEnd']

    # Duration
    duration = logDataDict['encounterDuration']

    # EliteInsightsVersion
    elite_insights_version = logDataDict['parser']
    
    # Boss Name
    boss_name = logDataDict['fightName']

    # List of instance buffs (emboldened)
    instance_buffs = logDataDict.get('instance_buffs')
    # Unknown patch changed instance_buffs -> instanceBuffs (most likely Elite Insights Version 2.46.1.2)
    if not instance_buffs:
        instance_buffs = logDataDict.get('instanceBuffs')

    # List of dictionaries containing player data
    player_dict = logDataDict['players']

    # List of dictionaries containing phase data
    phases = logDataDict['phases']

    # DPS numbers 
    target_dmg_distributions_taken = logDataDict['targets'][0]['details']['dmgDistributionsTaken']

    return success, time_start, time_end, duration, elite_insights_version, boss_name, instance_buffs, player_dict, phases, target_dmg_distributions_taken


# Parse log and upload data to database
def parse_and_upload_data_for_url(conn, cursor, URL: str, phase_config: "list[str]", log_count: int) -> bool:
    log_count += 1
    print("log %d" % log_count)
    logging.info("log %d" % log_count)
    log_url = URL.strip()

    # Initialize a log id
    log_id = generate_log_id()

    # Grab data dictionary from url
    logDataDict = get_scripts_from_url(URL)
    if not logDataDict:
        print("Failed to create log data dictionary.")
        return False

    # Fill important vars with data from dictionary and delete dictionary
    success, time_start, time_end, duration, elite_insights_version, boss_name, instance_buffs, player_dict, phases, target_dmg_distributions_taken = extract_useful_data_from_dict(logDataDict)
    del logDataDict
    gc.collect()

    # Success
    if not success:
        print("Not a successful log.")
        return False

    # TimeStart
    time_start_timestamp = datetime.strptime(time_start, "%Y-%m-%d %H:%M:%S %z")
    time_start_timestamp = time_start_timestamp.astimezone(pytz.utc)
    
    # TimeEnd
    time_end_timestamp = datetime.strptime(time_end, "%Y-%m-%d %H:%M:%S %z")
    time_end_timestamp = time_end_timestamp.astimezone(pytz.utc)

    # Check mode
    mode = "Normal"
    # Check CM
    cm_flag = boss_name.endswith(" CM")
    if cm_flag:
        mode = "CM"
        boss_name = boss_name[:-len(" CM")]
    else:
        # Check emboldened        
        if instance_buffs:
            for buff in instance_buffs:
                if isinstance(buff, list):
                    if buff[0] == 68087:
                        mode = f"EM{buff[1]}"

    # Parse player data and remove NPCs
    players = [(player['acc'], player['profession'], player['name']) for player in player_dict if player['profession'] != 'NPC']
    del player_dict
    gc.collect()
    for player in players:
        add_player_to_table(conn, cursor, player[0], player[2])

    # Create list of player ids involved in the log
    players_list = [player[0] for player in players]
    total_player_count = len(players_list)
    log_id = add_log_to_table(conn, cursor, log_url, log_id, boss_name, mode, duration, time_start_timestamp, time_end_timestamp, players_list, total_player_count, elite_insights_version)

    desired_phases = phase_config[boss_name] if boss_name in phase_config else ['Full Fight']


    # Iterate through each phase and add data to tables for each player
    for phase_idx in range(len(phases)):
        current_phase = phases[phase_idx]
        current_phase_name = current_phase['name']
        phase_duration = phases[phase_idx]['duration'] / 1000
        if current_phase_name in desired_phases:
            all_player_stats = []
            num_extraneous_players = 0
            for player_idx in range(len(players)):
                player_stats = []
                player_id, player_class, player_character = players[player_idx]

                player_target_dmg = current_phase['dpsStatsTargets'][player_idx][0][0]
                player_target_dps = round(player_target_dmg / phase_duration)
                target_total_dmg_taken = target_dmg_distributions_taken[phase_idx]['contributedDamage']
                ## TODO resolve Divided By Zero errors, until then, this will catch them
                if target_total_dmg_taken == 0:
                    player_percent_target_dps_value = 0
                if target_total_dmg_taken != 0:            
                    player_percent_target_dps_value = player_target_dmg / target_total_dmg_taken
                player_percent_target_dps = str(round(player_percent_target_dps_value*100, 2)) + '%'
                player_power_dps = round(current_phase['dpsStatsTargets'][player_idx][0][1] / phase_duration)         
                player_condi_dps = round(current_phase['dpsStatsTargets'][player_idx][0][2] / phase_duration)
                player_stats = [
                    player_class,
                    player_character,
                    player_id,
                    player_target_dps,
                    player_percent_target_dps,
                    player_power_dps,
                    player_condi_dps
                    ]        
                all_player_stats.append(player_stats)

                add_data_to_table(conn, cursor, log_url, log_id, player_id, player_character, player_class, current_phase_name, player_target_dps, player_percent_target_dps, player_power_dps, player_condi_dps)
    return True


# Add logs to database
def write_to_database(conn, cursor, url_list: "list[str]", phase_config: "list[str]") -> dict:
    # Iterate through all logs 
    log_count = 0 
    results = {}
    for URL in url_list:
        print(URL)
        data = parse_and_upload_data_for_url(conn, cursor, URL, phase_config, log_count)
        log_count += 1
        if data:
            results.setdefault("Successful", []).append(URL)
        else:
            results.setdefault("Unsuccessful", []).append(URL)
    return results


def log_parser_helper(connection, cursor, url_list: "list[str]", phase_config: "list[str]") -> dict:
    results = write_to_database(connection, cursor, url_list, phase_config)
    return results