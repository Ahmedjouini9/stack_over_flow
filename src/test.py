import requests
import time
import csv

BASE_URL = "https://api.stackexchange.com/2.3/questions"
TAG = "sap-basis"
SITE = "stackoverflow"
PAGE_SIZE = 100
MAX_PAGES = 100  # safety cap

def fetch_all_questions():
    all_questions = []
    page = 1

    while page <= MAX_PAGES:
        params = {
            "order": "desc",
            "sort": "creation",          
            "tagged": TAG,
            "site": SITE,
            "pagesize": PAGE_SIZE,
            "page": page
        }

        res = requests.get(BASE_URL, params=params)
        res.raise_for_status()
        data = res.json()

        items = data.get("items", [])
        if not items:
            print(f"⚠️ No items on page {page}. Stopping.")
            break

        for q in items:
            all_questions.append({
                "title": q.get("title"),
                "creation_date": q.get("creation_date"),
                "score": q.get("score"),
                "link": q.get("link"),
                "tags": ", ".join(q.get("tags", [])),
                "is_answered": q.get("is_answered")
            })

        print(f"[DEBUG] Page {page}: Collected {len(items)} questions")
        if not data.get("has_more"):
            print("✅ Reached end of available data.")
            break

        page += 1
        time.sleep(1.5)  # polite delay

    return all_questions

def save_to_csv(data, filename="stack_overflow_sap-basis.csv"):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    print(f"✅ Saved {len(data)} questions to {filename}")

if __name__ == "__main__":
    questions = fetch_all_questions()
    if questions:
        save_to_csv(questions)
