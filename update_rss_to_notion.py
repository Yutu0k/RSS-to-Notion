import feedparser
import requests
import json
import os

# 从环境变量中获取RSS Feed URL和Notion API信息
RSS_FEED_URL = os.getenv('RSS_FEED_URL')
NOTION_API_KEY = os.getenv('NOTION_API_KEY')
NOTION_DATABASE_ID = os.getenv('NOTION_DATABASE_ID')

def parse_rss_feed(url):
    return feedparser.parse(url)

def add_to_notion_database(title, link, summary):
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    data = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": {
            "Title": {
                "title": [
                    {
                        "text": {
                            "content": title
                        }
                    }
                ]
            },
            "Link": {
                "url": link
            },
            "Summary": {
                "rich_text": [
                    {
                        "text": {
                            "content": summary
                        }
                    }
                ]
            }
        }
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    if response.status_code != 200:
        raise Exception(f"Failed to add page to Notion: {response.text}")

def main():
    feed = parse_rss_feed(RSS_FEED_URL)
    for entry in feed.entries:
        title = entry.title
        link = entry.link
        summary = entry.summary
        add_to_notion_database(title, link, summary)

if __name__ == "__main__":
    main()