# -*- coding: utf-8 -*-
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from datetime import datetime
import time
import re
import logging
import traceback

GM_WEBPAGE = 'https://www.google.com/maps/'
MAX_WAIT = 10
MAX_RETRY = 5
MAX_SCROLLS = 40

class GoogleMapsScraper:

    def __init__(self, debug=False):
        self.debug = debug
        self.driver = self.__get_driver()
        self.logger = self.__get_logger()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        if exc_type is not None:
            traceback.print_exception(exc_type, exc_value, tb)

        self.driver.close()
        self.driver.quit()

        return True

    def sort_by(self, url, ind):
        self.driver.get(url)
        wait = WebDriverWait(self.driver, MAX_WAIT)

        # open dropdown menu
        clicked = False
        tries = 0
        while not clicked and tries < MAX_RETRY:
            try:
                #if not self.debug:
                #    menu_bt = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div.cYrDcjyGO77__container')))
                #else:
                menu_bt = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@data-value=\'Sort\']')))
                menu_bt.click()

                clicked = True
                time.sleep(3)
            except Exception as e:
                tries += 1
                self.logger.warn('Failed to click recent button')

            # failed to open the dropdown
            if tries == MAX_RETRY:
                return -1

        #  element of the list specified according to ind
        recent_rating_bt = self.driver.find_elements_by_xpath('//li[@role=\'menuitemradio\']')[ind]
        recent_rating_bt.click()

        # wait to load review (ajax call)
        time.sleep(15)

        return 0


    def get_reviews(self, offset):

        # scroll to load reviews

        # wait for other reviews to load (ajax)
        time.sleep(14)

        self.__scroll()


        # expand review text
        self.__expand_reviews()

        # parse reviews
        response = BeautifulSoup(self.driver.page_source, 'html.parser')
        # rblock = response.find_all('div', class_='section-review-content')
        rblock = response.find_all('div', class_='ODSEW-ShBeI NIyLF-haAclf gm2-body-2')
        parsed_reviews = []
        for index, review in enumerate(rblock):
            if index >= offset:
                parsed_reviews.append(self.__parse(review))
                print(self.__parse(review))

        return parsed_reviews


    def get_account(self, url):

        self.driver.get(url)

        # ajax call also for this section
        time.sleep(14)

        resp = BeautifulSoup(self.driver.page_source, 'html.parser')

        place_data = self.__parse_place(resp)

        return place_data

    def get_address(self,url):
        self.driver.get(url)

        time.sleep(16)

        # resp = BeautifulSoup(self.driver.page_source, 'html.parser')

        # address = self.__get_address(resp)
        address = self.driver.find_element_by_xpath('//*[@id="pane"]/div/div[1]/div/div/div[9]/div[1]/button/div[1]/div[2]/div[1]').text

        return address


    def __get_address(self,resp):
        # use XPath to load complete reviews
        
        # button = self.driver.find_elements_by_xpath('/button[@class=\'class="iRxY3GoUYUY__button gm2-hairline-border section-action-chip-button"\']')
        # button.click()
        # time.sleep(2)
        #address = resp.find("div",class_="ugiz4pqJLAG__root ugiz4pqJLAG__one-line-text ugiz4pqJLAG__dense ugiz4pqJLAG__metadata-shown-on-hover-only ugiz4pqJLAG__clickable'").text
        address = self.driver.find_element_by_css_selector("[data-item-id='address']").text
        return address






    def __parse(self, review):
        
        # get address here 
        
        item = {}

        # id_review = review.find('button', class_='section-review-action-menu')['data-review-id']
        # username = review.find('div', class_='section-review-title').find('span').text
        id_review = review.findChild("div")['data-review-id']
        username = review.find('div', class_='ODSEW-ShBeI-title').find('span').text

        try:
            # review_text = self.__filter_string(review.find('span', class_='section-review-text').text)
            review_text = self.__filter_string(review.find('span', class_='ODSEW-ShBeI-text').text)
        except Exception as e:
            review_text = None

        # rating = float(review.find('span', class_='section-review-stars')['aria-label'].split(' ')[1])
        # relative_date = review.find('span', class_='section-review-publish-date').text

        rating = float(review.find('span', class_='ODSEW-ShBeI-H1e3jb')['aria-label'].split(' ')[1])
        relative_date = review.find('span', class_='ODSEW-ShBeI-RgZmSc-date').text

        try:
            # n_reviews_photos = review.find('div', class_='section-review-subtitle').find_all('span')[1].text
            n_reviews_photos = review.find('div', class_='ODSEW-ShBeI-subtitle').find_all('span')[1].text
            metadata = n_reviews_photos.split('\xe3\x83\xbb')
            if len(metadata) == 3:
                n_photos = int(metadata[2].split(' ')[0].replace('.', ''))
            else:
                n_photos = 0

            idx = len(metadata)
            n_reviews = int(metadata[idx - 1].split(' ')[0].replace('.', ''))

        except Exception as e:
            n_reviews = 0
            n_photos = 0

        user_url = review.find('a')['href']

        item['id_review'] = id_review
        item['caption'] = review_text

        # depends on language, which depends on geolocation defined by Google Maps
        # custom mapping to transform into date shuold be implemented
        item['relative_date'] = relative_date

        # store datetime of scraping and apply further processing to calculate
        # correct date as retrieval_date - time(relative_date)
        item['retrieval_date'] = datetime.now()
        item['rating'] = rating
        item['username'] = username
        item['n_review_user'] = n_reviews
        item['n_photo_user'] = n_photos
        item['url_user'] = user_url

        return item


    def __parse_place(self, response):

        place = {}
        try:
            place['overall_rating'] = float(response.find('div', class_='gm2-display-2').text.replace(',', '.'))
        except:
            place['overall_rating'] = 'NOT FOUND'

        try:
            place['n_reviews'] = int(response.find('div', class_='gm2-caption').text.replace('.', '').replace(',','').split(' ')[0])
        except:
            place['n_reviews'] = 0

        return place

    # expand review description
    def __expand_reviews(self):
        # use XPath to load complete reviews
        # links = self.driver.find_elements_by_xpath('//button[@class=\'section-expand-review blue-link\']')
        links = self.driver.find_elements_by_xpath('//*[@id="pane"]/div/div[1]/div/div/div[2]/div[9]/div[19]/div/div[3]/div[3]/jsl/button')
        for l in links:
            l.click()
        time.sleep(12)

    # load more reviews
    def more_reviews(self):
        # use XPath to load complete reviews
        # links = self.driver.find_elements_by_xpath('//button[@jsaction=\'pane.reviewChart.moreReviews\']')
        links = self.driver.find_elements_by_xpath('//*[@id="pane"]/div/div[1]/div/div/div[53]/div/div/button/span')
        print('LINKS HERE', links)
        for l in links:
            l.click()
        time.sleep(12)

        
    def __scroll(self):
        scrollable_div = self.driver.find_element_by_css_selector('div.section-layout.section-scrollbox.cYB2Ge-oHo7ed') #cYB2Ge-ti6hGc
        # scrollable_div = self.driver.find_element_by_class_name('section-layout section-scrollbox')
        self.driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', scrollable_div)
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        #document.getElementsByClassName('section-layout section-scrollbox')[0].scrollBy(0,document.getElementsByClassName('section-layout section-scrollbox')[0].scrollHeight)


    def __get_logger(self):
        # create logger
        logger = logging.getLogger('googlemaps-scraper')
        logger.setLevel(logging.DEBUG)

        # create console handler and set level to debug
        fh = logging.FileHandler('gm-scraper.log')
        fh.setLevel(logging.DEBUG)

        # create formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        # add formatter to ch
        fh.setFormatter(formatter)

        # add ch to logger
        logger.addHandler(fh)

        return logger


    def __get_driver(self, debug=False):
        options = Options()

        if not self.debug:
            options.add_argument("--headless")
        else:
            options.add_argument("--window-size=1366,768")

        options.add_argument("--disable-notifications")
        options.add_argument("--lang=en-GB")
        input_driver = webdriver.Chrome("C:\Program Files (x86)\chromedriver.exe",chrome_options=options)


        return input_driver


    # util function to clean special characters
    def __filter_string(self, str):
        strOut = str.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')
        return strOut
