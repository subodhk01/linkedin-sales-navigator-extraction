# import web driver
import os, time, csv, random

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver import ChromeOptions

from services.email_verify import EmailVerify

field_names = ['Name', 'Title', 'Company', 'Link']

def get_user_agent():
    user_agents = [
        # "Mozilla/5.0 (Linux; Android 6.0.1; SM-G532G Build/MMB29T) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Mobile Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36", 
        # "Mozilla/5.0 (Linux; Android 6.0.1; SM-G532G Build/MMB29T) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.4389.114 Mobile Safari/537.36",
        # "Mozilla/5.0 (Linux; Android 6.0.1; SM-G532G Build/MMB29T) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.4389.114 Mobile Safari/537.36",
    ]
    return user_agents[random.randint(0, len(user_agents) - 1)]

def write_to_csv(data):
    with open('output.csv', 'a', newline='', encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=field_names)
        writer.writerows(data)


class ScrapingService:
    login_url = "https://www.linkedin.com/sales/login"

    def __init__(self, url, start_page, end_page, extraction_id):
        self.url = url
        self.start_page = start_page
        self.current_page = start_page
        self.end_page = end_page
        self.extraction_id = extraction_id
        self.speed = 1  # lower is faster
        self.total_scroll_time = 25  # seconds
        self.get_creds()
        self.init_driver()
        self.login()

    def get_creds(self):
        self.linkedin_username = os.environ['LINKEDIN_USERNAME']
        self.linkedin_password = os.environ['LINKEDIN_PASSWORD']

    def init_driver(self):
        options = ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-setuid-sandbox")
        options.add_argument("--disable-logging")
        options.add_argument("--log-level=3")
        browser = webdriver.Chrome('/usr/local/bin/chromedriver', options=options)
        browser.execute_cdp_cmd("Network.setUserAgentOverride", {
            "userAgent": get_user_agent(),
        })
        self.browser = browser
        self.browser.get(self.login_url)
        print("Successfully initiated Web Driver")

    def login(self):
        frame = self.browser.find_element(By.TAG_NAME, "iframe")
        self.browser.switch_to.frame(frame)
        elem_username = self.browser.find_element("id", "username")
        elem_username.send_keys(self.linkedin_username)
        elem_psswd = self.browser.find_element("id", "password")
        elem_psswd.send_keys(self.linkedin_password)
        log_in_button = self.browser.find_element(
            'xpath', '//*[@type="submit"]')
        log_in_button.click()
        print("Successfully logged in")
        time.sleep(1000)

    def wait(self, wait_time, wait_message=""):
        print(f"Waiting for {wait_time} seconds : {wait_message}")
        time.sleep(wait_time)
        # asyncio.sleep(wait_time)
        # for i in range(wait_time):
        #     print(f"Waiting for {wait_time} seconds" + "." * i)
        #     sys.stdout.write("\033[F")
        #     time.sleep(1)

    def scroll_results_container(self):        
        scroll_step = 200
        scroll_height = 0
        for _ in range(self.total_scroll_time):
            self.wait(1, "Scrolling")
            self.browser.execute_script(f"document.getElementById('search-results-container').scroll(0,{scroll_height})")
            scroll_height += scroll_step
        
            

    def next_page(self):
        self.wait(1*self.speed)
        btn = self.browser.find_elements(
            By.CSS_SELECTOR, "[aria-label='Next']")
        print(f"Moving to page {self.current_page + 1}...")
        if btn[0].is_enabled():
            if btn[0].is_displayed():
                btn[0].click()
            else:
                print("Next button not visible")
        else:
            print("No more pages")
        self.current_page = self.current_page + 1
        self.wait(1*self.speed)

    def get_page_data(self):
        self.scroll_results_container()

        extracted_data = []
        src = self.browser.page_source
        soup = BeautifulSoup(src, 'lxml')
        content = soup.find('ol', {'class': 'artdeco-list background-color-white _border-search-results_1igybl'})
        if content:
            list_items = content.find_all(
                'li', {'class': 'artdeco-list__item pl3 pv3'})
            for item in list_items:
                name = item.find('span', {'data-anonymize': 'person-name'})
                title = item.find('span', {'data-anonymize': 'title'})
                cname = item.find('a', {'class': 'ember-view t-black--light t-bold inline-block'})
                link = item.find('a', {'class': 'ember-view'})
                try:
                    data_dict = {'Name': '', 'Title': "", 'Company': '', 'Link': ''}
                    if name:
                        data_dict["Name"] = (name.text)
                    if title:
                        data_dict["Title"] = (title.text)
                    if cname:
                        data_dict["Company"] = (cname.text.strip())
                    if link:
                        data_dict["Link"] = (link['href'])
                    extracted_data.append(data_dict)
                except Exception as e:
                    print("Error in extracting data")
                    print(item)
                    print(e)

            write_to_csv(extracted_data)
            self.process_extracted_data(extracted_data)
            print(f"Successfully extracted data from page {self.current_page}")
            return True
        else:
            print(
                f"No data found on page {self.current_page}, please check url: {self.url}")
            return False

    def start_scraping(self):
        self.url = self.url + "&page=" + str(self.start_page)
        self.browser.get(self.url)
        self.wait(3*self.speed, f"Waiting for page {self.start_page} to load")

        # search for document.getElementById('search-results-container') element for 10 seconds
        # if not found, then wait for human check
        # if found, then scroll till end
        timeout = time.time() + 20
        for i in range(10):
            try:
                self.browser.find_element(By.ID, "search-results-container")
                break
            except Exception as e:
                self.wait(2, "Waiting for search-results-container element")
                if time.time() > timeout:
                    print("Error in getting page data: ", str(e))
                    human_check_wait = input("Error in getting page data, please solve the captcha and press enter to continue:")
                    print("human_check_wait: ", human_check_wait)

        while self.current_page <= self.end_page:
            run_page_data = self.get_page_data()
            if run_page_data:
                self.next_page()
            else:
                break

    def process_extracted_data(self, extracted_data):
        print("\nProcessing extracted data")
        # print("Extracted data: ", extracted_data)
        email_verify = EmailVerify(
            linkedin_data=extracted_data, extraction_id=self.extraction_id)
        email_verify.process_data()
        print("Successfully processed extracted data")
