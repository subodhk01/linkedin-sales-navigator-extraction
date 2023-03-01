# import web driver
import os, sys, time

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver import ChromeOptions
from utils import write_to_csv


class ScrapingService:
    sales_url = "https://www.linkedin.com/sales/login"

    def __init__(self, url, number_of_contacts):
        self.url = url
        self.number_of_contacts = number_of_contacts
        self.speed = 1  # lower is faster
        self.get_creds()
        self.init_driver()
        self.login()
        
    def get_creds(self):
        self.linkedin_username = os.environ['LINKEDIN_USERNAME']
        self.linkedin_password = os.environ['LINKEDIN_PASSWORD']

    def init_driver(self):
        opts = ChromeOptions()
        # opts.add_argument("--headless")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--disable-extensions")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-setuid-sandbox")
        self.browser = webdriver.Chrome(
            '/usr/local/bin/chromedriver', options=opts)
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
    
    def scroll_down(self):
        try:
            start = time.time()
            initialScroll = 0
            finalScroll = 500
            while True:
                self.browser.execute_script(f"document.getElementById('search-results-container').scroll({initialScroll},{finalScroll})")
                initialScroll = finalScroll
                finalScroll += 500
                self.wait(2*self.speed)
                end = time.time()
                if round(end - start) > 15:
                    break
        except Exception as e:
            print("Error in scrolling down, continuing...")
            print(e)
    
    def next_page(self):
        btn=self.browser.find_elements(By.CSS_SELECTOR,"[aria-label='Next']")
        print("Moving to next page -> ")
        if btn[0].is_enabled():
            btn[0].click()
        else:
            print("No more pages")
        self.wait(1*self.speed)
    
    def get_page_data(self):
        self.scroll_down()

        extracted_data=[]
        src = self.browser.page_source
        soup = BeautifulSoup(src, 'lxml')
        cont = soup.find('ol', {'class': 'artdeco-list background-color-white _border-search-results_1igybl'})
        list_emp=cont.find_all('li', {'class': 'artdeco-list__item pl3 pv3'})
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
        
    
    def start_scraping(self):
        self.browser.get(self.url)
        self.wait(5)
        total_pages = (self.number_of_contacts//25)+1
        for i in range(total_pages):
            self.get_page_data()
            self.next_page()
