from selenium import webdriver
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from time import sleep
from datetime import datetime
import requests
import json
import pandas as pd


with open('creds.txt') as f:
    creds = json.load(f)
def get_keywords():
    sheet_id = '1u1ATbHk92CnkGrBDph7unp-3_sIYdxKVYzORJk-FLos'
    sheet_csv = f'https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv'
    df = pd.read_csv(sheet_csv)
    return df['Keyword'].to_list()

keywords = get_keywords()
print(keywords)

def post_to_webhook(package):
    headers = {'Content-Type': 'application/json'}
    r = requests.post('https://hooks.zapier.com/hooks/catch/3009665/bvtptmi/', json=package, headers=headers)
    print(r.status_code)

now = datetime.now()

for keyword in keywords:
    content = {'keyword': keyword, 'posts': []}

    # SET UP DRIVER
    options = Options()
    options.add_argument("--disable-notifications")
    driver = webdriver.Edge(service=EdgeService(EdgeChromiumDriverManager().install()), options=options)
    driver.maximize_window()
    driver.get('https://www.facebook.com')

    # HANDLE COOKIE POP-UP
    try:
        WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, '//button[@data-cookiebanner="accept_only_essential_button"]'))).click()
    except TimeoutException:
        pass

    # LOGIN
    driver.find_element(By.XPATH, '//input[@name="email"]').send_keys(creds['email'])
    driver.find_element(By.XPATH, '//input[@name="pass"]').send_keys(creds['pass'])
    driver.find_element(By.XPATH, '//button[@name="login"]').click()
    sleep(8)
    driver.get('https://www.facebook.com/groups/businessbabesnl')

    # SEARCH
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '//div[@aria-label="Search" or @aria-label="Zoeken"]'))).click()
    search_field = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, '//input[@aria-label="Search this group" or @aria-label="Deze groep zoeken"]')))
    search_field.send_keys(keyword)
    search_field.send_keys(Keys.ENTER)
    sleep(5)
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//input[@aria-label="Most recent" or @aria-label="Meest recent"]'))).click()
    sleep(3)
    feed = driver.find_elements(By.XPATH, '//div[@role="feed"]/div')

    # LOOP THROUGH RECENT POSTS
    for post in feed:
        try:
            # GET NAME, LINK AND TIMESTRING
            name = post.find_element(By.XPATH, './/a[@role="link" and contains(@href, "/user/")]/strong/span').text
            href_element = post.find_element(By.XPATH, './/a[@role="link" and contains(@href, "#")]')
            ActionChains(driver).move_to_element(href_element).perform()  # HOVER MOUSE TO SHOW DATETIME AND HREF
            sleep(0.5)
            timestring = driver.find_element(By.XPATH, '/html/body/div[1]/div/div[1]/div/div[3]/div/div/div/div[2]/div').text
            href = post.find_element(By.XPATH, './/a[@role="link" and contains(@href, "/posts/")]').get_attribute('href')
            # CONVERT TIMESTRING TO DATETIME
            date_time = timestring.split(', ')[1]
            date_time2 = datetime.strptime(date_time,'%d %B %Y at %H:%M')
            days_ago = now-date_time2
            if days_ago.days < 1:
                dct = {'name': name, 'datetime': date_time, 'href': href}
                print(dct)
                content['posts'].append(dct)
            else:
                continue
        except:
            continue
    driver.quit()
    post_to_webhook(content)
