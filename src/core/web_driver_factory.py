from selenium import webdriver
from selenium.webdriver.chrome.options import Options


class WebDriverFactory:
    @staticmethod
    def get_driver():
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        return webdriver.Chrome()
