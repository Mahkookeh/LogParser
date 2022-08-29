from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import requests
from time import sleep
from bs4 import BeautifulSoup
import re
import sys
import psycopg2
from datetime import datetime, timezone, timedelta
import uuid
import pytz
import yaml
import logging


config = yaml.safe_load(open("config.yml"))

# Current list of files
included_players_file = config["files"]["includedPlayers"]
url_list_file = config["files"]["urlList"]
log_results_file = config["files"]["logResults"]
debug_logging_file = config["files"]["debugLogging"]
accepted_boss_list_file = config["files"]["acceptedBossList"]

current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
name = f"LogParserLogs\\{current_time}_{debug_logging_file}"
print(name)
logging.basicConfig(filename=name, level=logging.DEBUG)

# Install Chrome Driver Manager
chrome_driver_manager_path = ChromeDriverManager().install()

# Start logging

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

# Connect to a website
def selenium_connect(log_url, chrome_options):
    # Try connecting to the website 4 times before giving up
    for x in range(0,4):
        try:

            # Try creating the headless chrome driver 4 times before giving up
            for y in range(0,4):
                try:
                    driver = webdriver.Chrome(chrome_driver_manager_path, options=chrome_options)
                    driver.get(log_url)
                    str_error = None
                except Exception as ex:
                    logging.error("Exception has been thrown for log %s." % log_url)
                    str_error = str(ex)
                    logging.error(str_error)
                    pass
                if str_error:
                    sleep(2)
                else:
                    break
            wait = WebDriverWait(driver, 30)
            wait.until(EC.visibility_of_element_located((By.ID, "content")))
            str_error = None
        except Exception as ex:
            logging.error("Exception has been thrown for log %s." % log_url)
            str_error = str(ex)
            logging.error(str_error)
            driver.close()
            pass
        if str_error:
            sleep(2)
        else:
            break
    return driver

def check_success(soup_content):
    success = soup_content.find("div", class_="mb-2 text text-success")
    print(success)
    if success:
        return True
    else:
        return False

# Get Phases from soup content
def get_phase_soup_content(soup_content):
    # Set phase to scrape
    phases = soup_content.find("ul", class_="nav nav-pills d-flex flex-row justify-content-center")
    # If it has phases, navigate to the right phase
    if phases:
        first_phase = None
        found = False
        for phase in phases:
            # print(phase)
            current_phase = phase.text
            first_phase = phase.text if first_phase is None else first_phase
            # If commandline has desired phase, set desired phase
            if len(sys.argv) > 1:
                desired_phase = sys.argv[1]
            # Otherwise, set it to None and break out of phase search
            else:
                desired_phase = None
                found = True
                break
            # If desired phase is found:
            if desired_phase == phase.text:    
                found = True
                current_phase = phase.text
                logging.info(current_phase)
                print(current_phase)
                # Set current phase to another phase
                desired_page = driver.find_element("xpath", f"//a[contains(text(), '{phase.text}')]")
                driver.implicitly_wait(10)
                driver.execute_script("arguments[0].click();", desired_page);

                data = driver.page_source

                soup = BeautifulSoup(data, "html.parser")
                # Load main content html
                soup_content = soup.find(id="content")
                break
        # If desired phase isn't ever found, set first phase to default
        if found is False:
            current_phase = first_phase
    # If it's a one phase fight, set phase value to "Full Fight"
    else:
        current_phase = "Full Fight"

    return soup_content, current_phase

# Grab start time, end time, and elite insights version from footer data
def parse_footer(soup_content):
    footer = soup_content.find("div", class_="footer")
    time_start = re.search("Time Start: (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} -?\+?\d{2}:\d{2})", str(footer)).group(1)
    time_end = re.search("Time End: (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} -?\+?\d{2}:\d{2})", str(footer)).group(1)

    time_start_timestamp = datetime.strptime(time_start, "%Y-%m-%d %H:%M:%S %z")
    time_end_timestamp = datetime.strptime(time_end, "%Y-%m-%d %H:%M:%S %z")

    elite_insights_version = re.search("Elite Insights (\d*.\d*.\d*.\d*)", str(footer)).group(1)

    print(f"Time Start: {time_start_timestamp}\nTime End: {time_end_timestamp}\nElite Insights Version: {elite_insights_version}")
    logging.info(f"Time Start: {time_start_timestamp}\nTime End: {time_end_timestamp}\nElite Insights Version: {elite_insights_version}")
    time_start_timestamp = time_start_timestamp.astimezone(pytz.utc)
    time_end_timestamp = time_end_timestamp.astimezone(pytz.utc)

    print(f"Time Start: {time_start_timestamp}\nTime End: {time_end_timestamp}\nElite Insights Version: {elite_insights_version}")
    logging.info(f"Time Start: {time_start_timestamp}\nTime End: {time_end_timestamp}\nElite Insights Version: {elite_insights_version}")
    # exit()
    return time_start_timestamp, time_end_timestamp, elite_insights_version

def generate_log_id():
    return str(uuid.uuid4())

# Add log to Logs table
def add_log_to_table(conn, cursor, log_url, log_id, boss_name, mode, duration, time_start_timestamp, time_end_timestamp, players_list, total_player_count, elite_insights_version):
    log_id = check_log_equality(cursor, log_id, boss_name, duration, time_start_timestamp, time_end_timestamp, players_list)

    cursor.execute("""INSERT INTO "Logs" ("LogUrl", "LogId", "Boss", "Mode", "Duration", "TimeStart", "TimeEnd", "Players", "TotalPlayers", "EliteInsightVersion") VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT ("LogUrl") DO NOTHING""", (log_url, log_id, boss_name, mode, duration, time_start_timestamp, time_end_timestamp, players_list, total_player_count, elite_insights_version))
    conn.commit() 
    return log_id

# Add player to Players table
def add_player_to_table(cursor, player_id, player_character, included_players):
    group_name = ''

    # If the player is in the list of included players, add them to the group specified
    if player_id in included_players:
        # boba as test
        group_name = "Boba"
    cursor.execute("""INSERT INTO "Players" ("PlayerId", "Groups", "Characters") VALUES (%s, ARRAY [%s], ARRAY [%s]) ON CONFLICT ("PlayerId") DO UPDATE SET "Groups" = CASE WHEN %s = ANY("Players"."Groups") THEN "Players"."Groups" ELSE array_append("Players"."Groups", %s) END, "Characters" = CASE WHEN %s = ANY("Players"."Characters") THEN "Players"."Characters" ELSE array_append("Players"."Characters", %s) END""", (player_id, group_name, player_character, group_name, group_name, player_character, player_character))

# Add player to Players table
def add_data_to_table(cursor, log_url, log_id, player_id, player_character, player_class, current_phase, player_target_dps, player_percent_target_dps, player_power_dps, player_condi_dps):
    cursor.execute("""INSERT INTO "Data" ("LogUrl", "LogId", "PlayerId", "Character", "Class", "Phase", "TargetDps", "PercentTargetDps", "PowerDps", "CondiDps") VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT ("LogUrl", "PlayerId", "Phase") DO NOTHING""", (log_url, log_id, player_id, player_character, player_class, current_phase, player_target_dps, player_percent_target_dps, player_power_dps, player_condi_dps))

# Check if two logs are the same fight
def check_log_equality(cursor, log_id, boss_name, duration, time_start_timestamp, time_end_timestamp, players_list):
    
    duration_datetime = datetime.strptime(duration, "%Mm %Ss %fms")
    print(duration_datetime)
    duration_timedelta = timedelta(minutes=duration_datetime.minute,
                                seconds=duration_datetime.second,
                                microseconds=duration_datetime.microsecond)
    # Check boss name is same
    duration_minus5 = duration_timedelta - timedelta(seconds=5)
    duration_plus5 = duration_timedelta + timedelta(seconds=5)
    time_start_minus5 = time_start_timestamp - timedelta(seconds=5)
    time_start_plus5 = time_start_timestamp + timedelta(seconds=5)
    time_end_minus5 = time_end_timestamp - timedelta(seconds=5)
    time_end_plus5 = time_end_timestamp + timedelta(seconds=5)

    cursor.execute("""SELECT "LogId", "Players" FROM "Logs" where "Logs"."Boss" = %s AND "Logs"."Duration" BETWEEN %s::interval AND %s::interval AND "Logs"."TimeStart" BETWEEN %s AND %s AND "Logs"."TimeEnd" BETWEEN %s AND %s""", (boss_name, duration_minus5, duration_plus5, time_start_minus5, time_start_plus5, time_end_minus5, time_end_plus5))
    log_equality_list = cursor.fetchall()

    new_log_id = log_id
    for log_equality_value in log_equality_list:
        print(log_equality_value)
        logging.info(log_equality_value)
        log_equality_id, log_equality_players = log_equality_value
        if set(players_list) == set(log_equality_players):
            print("Found a duplicate log")
            logging.info("Found a duplicate log")
            new_log_id = log_equality_id
            break

    return new_log_id


def main():


    conn, cursor = connect_database()

    # Pull list of included players from text file
    included_players = set(line.strip() for line in open(included_players_file))
    # TODO
    # Change to command line argument 
    included_player_minimum = 5
    print(included_players)
    logging.info(included_players)


    # Grab urls from text file
    with open(url_list_file) as f:
        urls = f.readlines()
    print(urls)
    logging.info(urls)
    # Pull list of logs that are already parsed from text file
    parsed_logs = set()



    # Load website scraper
    chrome_options = Options()
    chrome_options.add_argument("--headless")

    # Create output file and add header line
    with open(log_results_file, 'w') as f:
        f.write("Boss, Mode, Phase, Player Id, Character, Class, "\
            "Target DPS, % Target DPS, Power DPS, Condi DPS, Duration, "\
            "Log Url, In-House Players, Total Players, Start Time, End Time, Elite Insights Version\n")

    # Iterate through all logs 
    log_count = 0 
    for URL in urls:
        print(URL)
        logging.info(URL)
        log_count += 1
        print("log %d" % log_count)
        logging.info("log %d" % log_count)
        log_url = URL.strip()

        log_id = generate_log_id()

        # Connect to the website
        driver = selenium_connect(log_url, chrome_options)
        data = driver.page_source

        soup = BeautifulSoup(data, "html.parser")

        # Load main content html
        soup_content = soup.find(id="content")

        # Grab footer information
        time_start_timestamp, time_end_timestamp, elite_insights_version = parse_footer(soup_content)

        # Check mode
        boss_name = soup_content.find(class_="card-header text-center").text
        print(boss_name)
        logging.info(boss_name)

        success = check_success(soup_content)
        print(f"Success: {success}")
        logging.info(f"Success: {success}")
        if not success:
            continue

        mode = "Normal"
        # Check CM
        cm_flag = boss_name.endswith(" CM")
        if cm_flag:
            mode = "CM"
            boss_name = boss_name[:-len(" CM")]
        else:
            # Check emboldened
            emboldened_element = soup_content.find(class_="d-flex flex-row justify-content-around mb-1")
            if emboldened_element:
                emboldened_stack_regex = re.search("<span>\s*(\d?)\s*x?\s*<img class=\"icon icon-hover\" data-original-title=\"Emboldened", str(emboldened_element))
                if emboldened_stack_regex:
                    stacks = emboldened_stack_regex.group(1)
                    if not stacks:
                        stacks = 1
                    mode = f"EM{stacks}"        
        logging.info(f"Mode: {mode}")


        # Change phases and update soup content
        current_phase = None
        soup_content, current_phase = get_phase_soup_content(soup_content)

        # Finally close website
        driver.close()


        # Get duration of the fight
        duration_string = soup_content.find("div", class_="mb-2", text=re.compile(r'Duration')).text.split("Duration: ")[1]
        duration = duration_string
        print(duration_string)
        logging.info(duration_string)
        # if ()
        # duration_datetime = datetime.strptime(duration_string, "%Mm %Ss %fms")
        # print(duration_datetime)
        # duration = timedelta(minutes=duration_datetime.minute,
        #                               seconds=duration_datetime.second,
        #                               microseconds=duration_datetime.microsecond)
        print(duration)
        logging.info(duration)


        # Get main dps table
        dps_table = soup_content.find(id="dps-table_wrapper")

        table_body = dps_table.find("tbody")

        # Check for number of included players
        included_player_count = 0

        final_result = ""
        # check all players in the log

        all_player_stats = []
        num_extraneous_players = 0
        for player in table_body:
            player_stats = []
            td_tags = player.find_all("td")
            player_subgroup = td_tags[0].text
            player_class = td_tags[1].text
            player_character = td_tags[2].text
            player_id = td_tags[3].text
            # Edge case where Conjured Swords on CA count as players
            if player_id in {"Conjured Sword", "Saul D'Alessio"}:
                num_extraneous_players += 1
                continue
            # if player is an included player, add to count
            if player_id in included_players:
                print(f"included: {player_id}")
                logging.info(f"included: {player_id}")
                included_player_count += 1
            else:
                print(f"not included: {player_id}")
                logging.info(f"not included: {player_id}")
            player_target_dps_info = str(td_tags[4])
            regex_percent_target_dps = re.search("&lt;br&gt;(\d*\.?\d*%) of total&lt;br&gt;", player_target_dps_info)
            player_percent_target_dps = regex_percent_target_dps.group(1)
            player_target_dps = td_tags[4].text.strip()
            player_power_dps = td_tags[5].text.strip()
            player_condi_dps = td_tags[6].text.strip()
            # player_breakbar_dps = td_tags[7].text.strip()
            player_stats = [
                player_class,
                player_character,
                player_id,
                player_target_dps,
                player_percent_target_dps,
                player_power_dps,
                player_condi_dps
                ]
            # result = f"{boss_name}, {mode}, {current_phase}, {player_id}, {player_character}, {player_class}, {player_target_dps}, {player_percent_target_dps}, {player_power_dps}, {player_condi_dps}, {duration}, {log_url}\n"
            all_player_stats.append(player_stats)
            # final_result += result
        

        players_list = []


        result_with_player_count = ""
        # for player in final_result.split("\n")[:-1]:
        #     player += f", {included_player_count}, {len(table_body) - num_extraneous_players}\n"
        #     result_with_player_count += player
        total_player_count = len(table_body) - num_extraneous_players


        # Insert into players list
        for player in all_player_stats:
            player_class, player_character, player_id, player_target_dps, player_percent_target_dps, player_power_dps, player_condi_dps = player
            players_list.append(player_id)


        log_id = add_log_to_table(conn, cursor, log_url, log_id, boss_name, mode, duration, time_start_timestamp, time_end_timestamp, players_list, total_player_count, elite_insights_version)
        

        # Insert into player and data tables
        for player in all_player_stats:
            player_class, player_character, player_id, player_target_dps, player_percent_target_dps, player_power_dps, player_condi_dps = player
            result_with_player_count += f"{boss_name}, {mode}, {current_phase}, "\
            f"{player_id}, {player_character}, {player_class}, {player_target_dps}, "\
            f"{player_percent_target_dps}, {player_power_dps}, {player_condi_dps}, {duration}, {log_url}, "\
            f"{included_player_count}, {total_player_count}, {time_start_timestamp}, "\
            f"{time_end_timestamp}, {elite_insights_version}\n"
            add_player_to_table(cursor, player_id, player_character, included_players)

            add_data_to_table(cursor, log_url, log_id, player_id, player_character, player_class, current_phase, player_target_dps, player_percent_target_dps, player_power_dps, player_condi_dps)

        # Ignore the log if there are less than the minimum included players
        if included_player_count >= included_player_minimum: 
            with open(log_results_file, 'a') as f:
                f.write(result_with_player_count)
            # print(result_with_player_count)

    
if __name__ == "__main__":
    main()