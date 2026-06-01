import requests
import cloudscraper
import json
from bs4 import BeautifulSoup
import os
import sys

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_IDS_str = os.environ.get("CHAT_ID", "[]")
CHAT_ID = json.loads(CHAT_IDS_str)

URLS = [
    "https://eu.brandymelville.com/collections/just-in",
    "https://eu.brandymelville.com/collections/clothing-tops",
    "https://eu.brandymelville.com/collections/clothing-sweatpants-sweatshirts",
    "https://eu.brandymelville.com/collections/clothing-bottoms",
    "https://eu.brandymelville.com/collections/bottom-skirt",
    "https://eu.brandymelville.com/collections/clothing-sweather",
    "https://eu.brandymelville.com/collections/clothing-shirt",
    "https://eu.brandymelville.com/collections/clothing-dresses",
    "https://eu.brandymelville.com/collections/clothing-yoga-pant",
    "https://eu.brandymelville.com/collections/stripes",
]
SEEN_ITEMS_FILE = "known_produkts.json"

if not BOT_TOKEN or not CHAT_ID:
    print("No token or chat id")
    sys.exit(1)


def send_photo(photo_url, message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    for id in CHAT_ID:
        data = {
            "chat_id": id,
            "photo": photo_url,
            "caption": message,
            "parse_mode": "HTML",
        }

        try:
            response = requests.post(url, data=data)
            if response.status_code != 200:
                print(f"Error by sending photo: {response.text}")
        except Exception as e:
            print(f"failed to connect: {e}")


def send_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    for id in CHAT_ID:
        data = {"chat_id": id, "text": message, "parse_mode": "HTML"}

        try:
            response = requests.post(url, data=data)
            if response.status_code != 200:
                print(f"Error by sending message: {response.text}")
        except Exception as e:
            print(f"failed to connect: {e}")


def get_items(scraper, url):

    try:
        response = scraper.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        items = []
        for product_card in soup.find_all("li", class_="grid__item"):
            link_tag = product_card.find("a", class_="full-unstyled-link")
            if not link_tag or not link_tag.get("href"):
                continue
            full_url = f"https://eu.brandymelville.com{link_tag.get('href')}"

            img_tag = product_card.find("img")
            image_url = ""
            if img_tag and img_tag.get("src"):
                image_url = "https:" + img_tag.get("src")

            info_div = product_card.find("div", class_="card-information")
            if info_div:
                text_info = " ".join(info_div.text.strip().split())
            else:
                text_info = "Details in link"

            items.append({"url": full_url, "image_url": image_url, "info": text_info})

        return items
    except Exception as e:
        print(f"Error by loading the page: {e}")
        return []


def main():
    if os.path.exists(SEEN_ITEMS_FILE):
        with open(SEEN_ITEMS_FILE, "r", encoding="utf-8") as f:
            try:
                seen_items = json.load(f)
            except json.JSONDecodeError:
                seen_items = []

    else:
        seen_items = []

    current_items = []
    for url in URLS:
        scraper = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "windows", "desktop": True}
        )
        items = get_items(scraper, url)
        current_items.extend(items)

    if not current_items:
        print("Nothing was found")
        return

    urls_now = set()
    unique_items = []
    for item in current_items:
        if item["url"] not in urls_now:
            unique_items.append(item)
            urls_now.add(item["url"])

    new_items = []
    for item in unique_items:
        if item["url"] not in seen_items:
            new_items.append(item)

    if new_items:
        print(f"{len(new_items)} new items was found")
        for item in new_items:
            caption = f"🚨 <b>New produkt was found!</b>\n\n{item['info']}\n\n👉 <a href='{item['url']}'>Follow this link</a>"

            if item["image_url"]:
                send_photo(item["image_url"], caption)
            else:
                send_message(caption)

            seen_items.append(item["url"])

        with open(SEEN_ITEMS_FILE, "w", encoding="utf-8") as f:
            json.dump(seen_items, f, ensure_ascii=False, indent=4)
    else:
        print("No new Items was found")
        send_message("No new Items were found")


if __name__ == "__main__":
    main()
