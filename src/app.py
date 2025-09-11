import pandas as pd
import logging
import json
from time import sleep
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class FetchUrlsData:
    def __init__(self, url):
        self.url = url
        self.information = []

    def fetch_urls(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False, slow_mo=50)
            context = browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/117.0.0.0 Safari/537.36",
                locale="en-US",
                timezone_id="Europe/Paris"
            )

            # Load cookies from a real session
            try:
                with open("stackoverflow_cookies.json", "r") as f:
                    cookies = json.load(f)
                    context.add_cookies(cookies)
                    logging.info("Injected session cookies")
            except FileNotFoundError:
                logging.warning("No cookies found — running without login")

            page = context.new_page()
            stealth = Stealth()
            stealth.apply_stealth_sync(page)

            logging.info(f"Navigating to {self.url}")
            page.goto(self.url, timeout=60000)

            # CAPTCHA detection
            if "/nocaptcha" in page.url:
                logging.error("Blocked by CAPTCHA — scraping aborted")
                browser.close()
                return

            # Set page size to 50 via UI interaction
            try:
                page.wait_for_selector("select[name='pagesize']", timeout=5000)
                page.select_option("select[name='pagesize']", "50")
                sleep(2)
                logging.info("Set page size to 50")
            except Exception:
                logging.warning("Page size selector not found — continuing with default")

            try:
                while True:
                    # Simulate human behavior
                    page.mouse.move(100, 100)
                    page.mouse.move(300, 200)
                    page.mouse.move(500, 400)
                    page.keyboard.press("PageDown")
                    sleep(1)

                    page.wait_for_selector(".s-post-summary h3 a", timeout=10000)
                    urls = page.query_selector_all(".s-post-summary h3 a")

                    logging.info(f"Found {len(urls)} rows on current page")

                    for url in urls:
                        href = url.get_attribute("href")
                        if href and href.startswith("/questions"):
                            full_url = f"https://stackoverflow.com{href}"
                            if full_url not in self.information:
                                self.information.append(full_url)
                                logging.info(f"Scraped URL: {full_url}")

                    next_button = page.query_selector("a[rel='next']")
                    if next_button:
                        next_button.scroll_into_view_if_needed()
                        sleep(1)
                        next_button.click()
                        sleep(2)
                    else:
                        logging.info("No more pages to scrape")
                        break

            except Exception as e:
                logging.error(f"Error during scraping: {str(e)}")
            finally:
                browser.close()

    def parse_to_excel(self, data_list):
        df = pd.DataFrame(data_list, columns=["URL"])
        df.to_csv("SAP.csv", index=False)
        logging.info("URLs saved to SAP.csv")

def main():
    url = "https://stackoverflow.com/search?tab=Relevance&pagesize=50&q=sap&searchOn=3"
    data = FetchUrlsData(url)
    data.fetch_urls()
    data.parse_to_excel(data.information)

if __name__ == "__main__":
    main()
