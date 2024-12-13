from datetime import date, datetime, timedelta
import http.client
from dotenv import load_dotenv, set_key
from os import environ as env
from time import sleep
import re
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from seleniumrequests import Firefox

options = Options()
options.set_preference("browser.download.panel.shown", False)
options.binary_location = r'C:\Program Files\Mozilla Firefox\firefox.exe'
options.headless = False
driver = Firefox()
driver.set_window_size(1920, 1080)

# environment variables
load_dotenv(r'vars.env')

webhook_url = env.get('webhook_url')


def send(message):
    # compile the form data (BOUNDARY can be anything)
    formdata = "------:::BOUNDARY:::\r\nContent-Disposition: form-data; name=\"content\"\r\n\r\n" + message + "\r\n------:::BOUNDARY:::--"

    # get the connection and make the request
    connection = http.client.HTTPSConnection("discordapp.com")
    connection.request("POST", webhook_url, formdata.encode('utf-8'), {
        'content-type': "multipart/form-data; boundary=----:::BOUNDARY:::",
        'cache-control': "no-cache",
    })

    # get the response
    wh_response = connection.getresponse()
    result = wh_response.read()

    # return back to the calling function with the result
    return result.decode("utf-8")


local_timezone_list = str(datetime.now().astimezone().tzinfo).split()
local_timezone = ''
for word in local_timezone_list:
    local_timezone += word[0]

discord_message = ""

driver.get(url='https://www.ufc.com/events')
sleep(3)

next_fight_raw = driver.find_element(By.XPATH, "//div[@class='c-card-event--result__date tz-change-data']")
next_fight_timestamp = int(next_fight_raw.get_attribute('data-main-card-timestamp'))
fight_date_time = datetime.fromtimestamp(next_fight_timestamp)
if datetime.now() <= fight_date_time <= datetime.now() + timedelta(hours=24):
    discord_message += f"# Fight Today {fight_date_time.strftime('%m/%d/%Y')}"
    fight_url_raw = driver.find_element(By.XPATH, "//div[@class='c-card-event--result__date tz-change-data']/a")
    fight_url = str(fight_url_raw.get_attribute('href'))
    driver.get(url=fight_url)
    sleep(60)
    event_list = ['main-card', 'prelims-card', 'early-prelims']
    for event in event_list:
        try:
            event_name = driver.find_element(By.XPATH, f"//div[@id='{event}']//strong").text
        except NoSuchElementException:
            event_name = None
            continue
        event_time = driver.find_element(By.XPATH, f"//div[@id='{event}']//div[@class='c-event-fight-card-broadcaster__time tz-change-inner']").text
        event_time = re.sub(r'.*/\s', '', event_time)
        discord_message += f"\n\n # {event_name} {event_time}"
        fight_matchups = driver.find_elements(By.XPATH, f"//div[@id='{event}']//div[@class='c-listing-fight__names-row']")

        for matchup in fight_matchups:
            name_list = matchup.find_elements(By.XPATH, f".//a")
            fighter_one = name_list[0].get_attribute('href').replace('https://www.ufc.com/athlete/', '').replace('-', " ").upper()
            fighter_two = name_list[1].get_attribute('href').replace('https://www.ufc.com/athlete/', '').replace('-', " ").upper()
            discord_message += f"\n{fighter_one} **VS** {fighter_two}"

    send(discord_message)

driver.close()