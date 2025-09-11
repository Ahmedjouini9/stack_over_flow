import re, json, logging
import pandas as pd
from abc import ABC
from whats_that_code.election import guess_language_all_methods
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from core.web_scraper import WebScraper  # Your custom Selenium wrapper

class DataExtractor(ABC):
    def __init__(self):
        self.data = []

    def process_urls_from_csv(self, csv_filepath):
        try:
            df = pd.read_csv(csv_filepath)
            urls = df['URL'].tolist()
            logging.info(f"Found {len(urls)} URLs to process.")
            for url in urls:
                page_data = self.process_single_page(url)
                if page_data:
                    self.data.append(page_data)
                    logging.info(f"✅ Processed: {url}")
        except Exception as e:
            logging.error(f"❌ Error reading CSV: {e}")

    def process_single_page(self, url):
        scraper = WebScraper(url)
        scraper.open_website()
        wait = WebDriverWait(scraper.driver, 10)
        page_data = {
            "topic": "SAP",
            "tags": [],
            "question": {},
            "accepted_answer": {},
            "other_answers": []
        }

        try:
            # Extract question title and body
            title_el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#question-header > h1 > a")))
            question_container = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".question .js-post-body")))
            ordered_content = self.extract_ordered_content(question_container)
            ordered_content = self.regroup_quoted_blocks(ordered_content)

            """ paragraphs = question_container.find_elements(By.TAG_NAME, "p")
            question_body = "\n\n".join(p.text.strip() for p in paragraphs if p.text.strip())

            images = question_container.find_elements(By.TAG_NAME, "img")
            image_urls = [img.get_attribute("src") for img in images if img.get_attribute("src")]
 """
            page_data["question"] = {
                "title": title_el.text.strip(),
                "content": ordered_content,
                "url": url
            }

            # Extract tags
            try:
                tag_elements = scraper.driver.find_elements(By.CSS_SELECTOR, ".post-taglist .post-tag")
                page_data["tags"] = [tag.text.strip() for tag in tag_elements]
            except Exception as e:
                logging.warning(f"⚠️ Failed to extract tags: {e}")
                page_data["tags"] = []

            # Extract answers
            try:
                answers = scraper.driver.find_elements(By.CSS_SELECTOR, ".answer")
                for ans in answers:
                    try:
                        body = ans.find_element(By.CSS_SELECTOR, ".js-post-body")
                        votes = int(ans.find_element(By.CSS_SELECTOR, ".js-vote-count").text.strip())
                        is_accepted = "accepted-answer" in ans.get_attribute("class")
                        answer_content = self.extract_ordered_content(body)
                        answer_content = self.regroup_quoted_blocks(answer_content)


                        answer_data = {
                            "content": answer_content,
                            "votes": votes,
                        }

                        if is_accepted:
                            page_data["accepted_answer"] = answer_data
                        else:
                            page_data["other_answers"].append(answer_data)

                    except Exception as e:
                        logging.warning(f"⚠️ Failed to parse answer block: {e}")
                        continue
            except Exception as e:
                logging.warning(f"⚠️ No answers found: {e}")

            return page_data

        except Exception as e:
            logging.error(f"❌ Failed to process page: {e}")
            return None
        finally:
            scraper.close_website()

    def clean_scraped_text(self, text):
        if not text:
            return ""
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def save_to_json(self, output_file):
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=4)
            logging.info(f"✅ Saved {len(self.data)} entries to {output_file}")
        except Exception as e:
            logging.error(f"❌ Failed to save JSON: {e}")

    def extract_ordered_content(self, container):
        content_blocks = []
        children = container.find_elements(By.XPATH, "./*")

        for child in children:
            tag = child.tag_name.lower()

            if tag in ["p","div"]:
                text = child.text.strip()
                text_body = self.clean_scraped_text(text)
                if text_body:
                    content_blocks.append({
                        "type": "text",
                        "value": text_body,
                    })
            elif tag == "blockquote":
                nested_text = child.find_elements(By.XPATH, ".//*")
                for sub in nested_text:
                    sub_tag = sub.tag_name.lower()
                    if sub_tag in ["p","div"]:
                        text = sub.text.strip()
                        text_body = self.clean_scraped_text(text)
                        if text_body:
                            content_blocks.append({
                                "type": "quoted",
                                "value": text_body,
                            })
                    elif sub_tag == "pre":
                        code = sub.text.strip()
                        if code:
                            content_blocks.append({
                                "type": "code",
                                "value": code,
                            })
                    elif sub_tag == "img":
                        src = sub.get_attribute("src")
                        if src:
                            content_blocks.append({
                                "type": "image",
                                "value": src,
                            })
            elif tag == "pre":
                code = child.text.strip()
                if code:
                    content_blocks.append({
                        "type": "code",
                        "value": code,
                    })

            elif tag == "img":
                src = child.get_attribute("src")
                if src:
                    content_blocks.append({
                        "type": "image",
                        "value": src,
                    })

        return content_blocks

    def regroup_quoted_blocks(self, content):
        grouped = []
        buffer = []

        for block in content:
            if block["type"] == "quoted":
                buffer.append(block["value"])
            else:
                if buffer:
                    grouped.append({
                        "type": "quoted",
                        "value": buffer
                    })
                    buffer = []
                grouped.append(block)

        # Flush remaining buffer
        if buffer:
            grouped.append({
                "type": "quoted",
                "value": buffer
            })

        return grouped

""" 
    def detect_language(self, code):
        code_lower = code.lower()

        # Heuristic layer
        if "public static" in code_lower or "system.out.println" in code_lower:
            return "java"
        elif "def " in code_lower or "import " in code_lower:
            return "python"
        elif "function(" in code_lower or "console.log" in code_lower:
            return "javascript"
        elif "#include" in code_lower or "int main()" in code_lower:
            return "c++"
        elif "<html>" in code_lower or "<div>" in code_lower:
            return "html"
        elif "select " in code_lower and "from " in code_lower:
            return "sql"
        elif "using system;" in code_lower or "console.writeline" in code_lower or "namespace " in code_lower:
            return "c#"

        # Fallback to whats-that-code
        try:
            result = guess_language_all_methods(code)
            lang = result[0] if result else "unknown"

            # Sanity check: must be a known language name
            if len(lang) < 3 or not lang.isalpha():
                return "unknown"

            return lang.lower()
        except Exception:
            return "unknown"
 """