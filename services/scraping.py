# import web driver
import os, sys, time, csv

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver import ChromeOptions

from services.email_verify import EmailVerify

field_names = ['Name', 'Title', 'Company','Link']
def write_to_csv(data):    
    with open('output.csv', 'a', newline='', encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames = field_names)
        writer.writerows(data)


class ScrapingService:
    sales_url = "https://www.linkedin.com/sales/login"

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
        self.browser = webdriver.Chrome(
            '/usr/local/bin/chromedriver', options=options)
        self.browser.get(self.sales_url)
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
    
    def wait(self, wait_time):
        for i in range(wait_time):
            print(f"Waiting for {wait_time} seconds" + "." * i)
            sys.stdout.write("\033[F")
            time.sleep(1)
    
    def scroll_till_end(self):
        error_count = 0
        self.wait(3*self.speed)
        start = time.time()
        initialScroll = 0
        finalScroll = 500
        while True:
            self.wait(1*self.speed)
            try:
                self.browser.execute_script(f"document.getElementById('search-results-container').scroll({initialScroll},{finalScroll})")
                initialScroll = finalScroll
                finalScroll += 500
                self.wait(2*self.speed)
                end = time.time()
                if round(end - start) > self.total_scroll_time:
                    break
            except Exception as e:
                print("Error in scrolling down, continuing...")
                error_count += 1
                if error_count > 2:
                    break
    
    def next_page(self):
        self.wait(1*self.speed)
        btn=self.browser.find_elements(By.CSS_SELECTOR,"[aria-label='Next']")
        print(f"Moving to page {self.current_page + 1}...")
        if btn[0].is_enabled():
            if btn[0].is_displayed():
                btn[0].click()
            else:
                print("Next button not visible")
        else:
            print("No more pages")
        self.current_page  = self.current_page + 1
        self.wait(1*self.speed)
    
    def get_page_data(self):
        self.scroll_till_end()

        extracted_data=[]
        src = self.browser.page_source
        soup = BeautifulSoup(src, 'lxml')
        content = soup.find('ol', {'class': 'artdeco-list background-color-white _border-search-results_1igybl'})
        if content:
            list_emp=content.find_all('li', {'class': 'artdeco-list__item pl3 pv3'})
            for j in list_emp:
                name=j.find('span', {'data-anonymize': 'person-name'})
                title=j.find('span', {'data-anonymize': 'title'})
                cname=j.find('a', {'class': 'ember-view t-black--light t-bold inline-block'})
                link=j.find('a', {'class': 'ember-view'})
                try:
                    dict_emp={'Name': '', 'Title': "", 'Company': '', 'Link': ''}
                    if name:
                        dict_emp["Name"]=(name.text)
                    if title:
                        dict_emp["Title"]=(title.text)
                    if cname:
                        dict_emp["Company"]=(cname.text.strip())
                    if link:
                        dict_emp["Link"]=(link['href'])
                    extracted_data.append(dict_emp)
                except Exception as e:
                    print("Error in extracting data")
                    print(j)
                    print(e)
                
            write_to_csv(extracted_data)
            self.process_extracted_data(extracted_data)
            print(f"Successfully extracted data from page {self.current_page}")
            return True
        else:
            print(f"No data found on page {self.current_page}, please check url: {self.url}")
            return False
          
    def start_scraping(self):
        total_pages = self.end_page - self.start_page
        self.url = self.url + "&page=" + str(self.start_page)

        self.browser.get(self.url)
        self.wait(5)
        
        for _ in range(total_pages):
            run_page_data = self.get_page_data()
            if run_page_data:
                self.next_page()
            else:
                break

    def process_extracted_data(self, extracted_data):
        print("Processing extracted data")
        email_verify = EmailVerify(linkedin_data=extracted_data, extraction_id=self.extraction_id)
        email_verify.process_data()
        print("Successfully processed extracted data")
        