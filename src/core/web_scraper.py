from .web_driver_factory import WebDriverFactory
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
)
import logging


class WebScraper:
    def __init__(self, url):
        self.driver = WebDriverFactory.get_driver()
        self.url = url

    def open_website(self):
        try:
            self.driver.get(self.url)
        except Exception as e:
            logging.error(f"Error opening website: {str(e)}")

    def click_element(self, by, value):
        element = self.driver.find_element(by, value)
        element.click()

    def select_option_by_value(self, element, value):
        select = Select(element)
        select.select_by_value(value)

    def find_elements(self, by, value):
        return self.driver.find_elements(by, value)

    def find_element(self, by, value):
        return self.driver.find_element(by, value)

    def close_website(self):
        try:
            self.driver.quit()
        except Exception as e:
            logging.error(f"Error closing website: {str(e)}")

    def is_element_clickable(self, by, value):
        try:
            element = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((by, value))
            )
            return element.is_enabled()
        except TimeoutException:
            return False
