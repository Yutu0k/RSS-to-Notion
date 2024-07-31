import feedparser
from notion_client import Client
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os

# Notion API token and database IDs
NOTION_API_KEY = os.getenv('NOTION_API_KEY')
NOTION_READING_DATABASE_ID = os.getenv('NOTION_READING_DATABASE_ID')
NOTION_URL_DATABASE_ID = os.getenv('NOTION_URL_DATABASE_ID')


# Initialize headers for Notion API requests
headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

def fetch_rss_urls():
    query = {
        "filter": {
            "property": "RSS",
            "rich_text": {
                "is_not_empty": True
            }
        }
    }
    response = requests.post(f"https://api.notion.com/v1/databases/{URL_MANAGEMENT_DB_ID}/query", json=query, headers=headers)
    response.raise_for_status()
    results = response.json().get("results")
    return [item["properties"]["RSS"]["url"] for item in results]

def parse_rss_feed(url):
    feed = feedparser.parse(url)
    entries = []
    for entry in feed.entries:
        entries.append({
            "title": entry.title,
            "link": entry.link,
            "published": datetime(*entry.published_parsed[:6]).isoformat() if entry.get("published_parsed") else None,
            "content": BeautifulSoup(entry.description, "html.parser").get_text()
        })
    return entries

def format_for_notion(entries):
    formatted_entries = []
    for entry in entries:
        formatted_entries.append({
            "Title": {"title": [{"text": {"content": entry["title"]}}]},
            "Link": {"url": entry["link"]},
            "Published": {"date": {"start": entry["published"]}} if entry["published"] else {"date": None},
            "Content": {"rich_text": [{"text": {"content": entry["content"]}}]}
        })
    return formatted_entries

def update_notion_database(entries):
    for entry in entries:
        data = {
            "parent": {"database_id": READ_DB_ID},
            "properties": entry
        }
        response = requests.post("https://api.notion.com/v1/pages", json=data, headers=headers)
        if response.status_code != 200:
            print(f"Failed to create page: {response.status_code} {response.text}")
        response.raise_for_status()

def main():
    rss_urls = fetch_rss_urls()
    for url in rss_urls:
        entries = parse_rss_feed(url)
        formatted_entries = format_for_notion(entries)
        update_notion_database(formatted_entries)

if __name__ == "__main__":
    main()
