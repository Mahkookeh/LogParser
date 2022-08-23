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

# TODO 
# Replace hard-coded input text files

def selenium_connect():
    # Try connecting to the website 4 times before giving up
    for x in range(0,4):
        try:

            # Try creating the headless chrome driver 4 times before giving up
            for y in range(0,4):
                try:
                    driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
                    driver.get(log_url)
                    str_error = None
                except Exception as ex:
                    print("Exception has been thrown for log %s." % log_url)
                    str_error = str(ex)
                    print(str_error)
                    pass
                if str_error:
                    sleep(2)
                else:
                    break
            wait = WebDriverWait(driver, 30)
            wait.until(EC.visibility_of_element_located((By.ID, "content")))
            str_error = None
        except Exception as ex:
            print("Exception has been thrown for log %s." % log_url)
            str_error = str(ex)
            print(str_error)
            driver.close()
            pass
        if str_error:
            sleep(2)
        else:
            break
    return driver


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
                # Set current phase to another phase
                desired_page = driver.find_element_by_xpath(f"//a[contains(text(), '{phase.text}')]")
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


# Check if two logs are the same fight
def check_log_equality():
    # Check boss name is same
    # Check Duration is within 5 seconds of each other
    # Check Time start and Time end are within 5 seconds of each other
    # Check all playesr are the same
    # Check Elite Insights version
    pass


# Pull list of included players from text file
included_players = set(line.strip() for line in open('includedPlayers.txt'))
# TODO
# Change to command line argument 
included_player_minimum = 5
print(included_players)


# Grab urls from text file
with open('urlList.txt') as f:
# with open('arsListInclude.txt') as f:
    urls = f.readlines()
print(urls)

# Pull list of logs that are already parsed from text file
parsed_logs = set(line.strip() for line in open('parsedLogs.txt'))


# # Grab cutoff times from text file
# with open('cutoffTimes.txt') as f:
#     cutoffs = f.readlines()
# print(cutoffs)

# Load website scraper
chrome_options = Options()
chrome_options.add_argument("--headless")

# Create output file and add header line
with open('logResults.txt', 'w') as f:
    f.write("Boss, Mode, Phase, Player Id, Character, Class, Target DPS, % Target DPS, Power DPS, Condi DPS, Duration, Log Url, In-House Players, Total Players\n")

# Iterate through all logs 
log_count = 0 
for URL in urls:
    if URL in parsed_logs:
        print(f"Url {URL} is already parsed.")
        continue
    log_count += 1
    print("log %d" % log_count)
    log_url = URL.strip()


    # Connect to the website
    driver = selenium_connect()
    data = driver.page_source

    soup = BeautifulSoup(data, "html.parser")

    # Load main content html
    soup_content = soup.find(id="content")
    # print(soup_content.prettify())

    # Check mode
    boss_name = soup_content.find(class_="card-header text-center").text
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
            stacks = emboldened_stack_regex.group(1)
            if not stacks:
                stacks = 1
            mode = f"EM{stacks}"        



    # Change phases and update soup content
    current_phase = None
    soup_content, current_phase = get_phase_soup_content(soup_content)

    # Finally close website
    driver.close()


    # Get duration of the fight
    duration = soup_content.find("div", class_="mb-2", text=re.compile(r'Duration')).text.split("Duration: ")[1]
    

    # Get main dps table
    dps_table = soup_content.find(id="dps-table_wrapper")

    table_body = dps_table.find("tbody")

    # Check for number of included players
    included_player_count = 0

    final_result = ""
    # check all players in the log

    player_stats = []
    for player in table_body:
        td_tags = player.find_all("td")
        player_subgroup = td_tags[0].text
        player_class = td_tags[1].text
        player_character = td_tags[2].text
        player_id = td_tags[3].text
        # if player is an included player, add to count
        if player_id in included_players:
            print(f"included: {player_id}")
            included_player_count += 1
        else:
            print(f"not included: {player_id}")
            continue
        player_target_dps_info = str(td_tags[4])
        regex_percent_target_dps = re.search("&lt;br&gt;(\d*\.?\d*%) of total&lt;br&gt;", player_target_dps_info)
        player_percent_target_dps = regex_percent_target_dps.group(1)
        player_target_dps = td_tags[4].text.strip()
        player_power_dps = td_tags[5].text.strip()
        player_condi_dps = td_tags[6].text.strip()
        # player_breakbar_dps = td_tags[7].text.strip()
        result = f"{boss_name}, {mode}, {current_phase}, {player_id}, {player_character}, {player_class}, {player_target_dps}, {player_percent_target_dps}, {player_power_dps}, {player_condi_dps}, {duration}, {log_url}\n"
        final_result += result

    result_with_player_count = ""
    for player in final_result.split("\n")[:-1]:
        player += f", {included_player_count}, {len(table_body)}\n"
        result_with_player_count += player

    # Ignore the log if there are less than the minimum included players
    if included_player_count >= included_player_minimum: 
        with open('logResults.txt', 'a') as f:
            f.write(result_with_player_count)
        print(result_with_player_count)

    

