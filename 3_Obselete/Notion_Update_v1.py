# update_rss_to_notion.py

import feedparser
import requests
import json
import os
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import html2text
import time

# 从环境变量中获取Notion API信息
NOTION_API_KEY = os.getenv('NOTION_API_KEY')
NOTION_READING_DATABASE_ID = os.getenv('NOTION_READING_DATABASE_ID')
NOTION_URL_DATABASE_ID = os.getenv('NOTION_URL_DATABASE_ID')


# 解析 RSS Feed
def parse_rss_feed(url):
    feed = feedparser.parse(url)
    if feed.bozo:
        return parse_rss_feed_manually(url)
    return feed

# 手动解析 RSS Feed
def parse_rss_feed_manually(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        feed = {'entries': []}
        for item in root.findall('.//item'):
            entry = {
                'title': item.find('title').text,
                'link': item.find('link').text,
                'summary': item.find('description').text,
            }
            feed['entries'].append(entry)
        return feed
    except Exception as e:
        print(f"Failed to parse RSS feed manually: {url}, error: {e}")
        return None

# 从 Notion URL 管理数据库中获取 RSS Feed URL
def get_rss_urls_from_notion():
    url = f"https://api.notion.com/v1/databases/{NOTION_URL_DATABASE_ID}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    response = requests.post(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Failed to query Notion database: {response.text}")

    data = response.json()
    results = []
    for result in data['results']:
        url = result['properties'].get('URL', {}).get('url')
        if url:  # 只处理有效的 URL
            results.append(url)
    return results

# 将数据导入到 Notion Reading 数据库
def add_to_notion_database(title, link, summary):
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    # 转换 summary 为富文本格式
    markdown_converter = html2text.HTML2Text()
    markdown_converter.ignore_links = False
    summary_rich_text = markdown_converter.handle(summary)

    data = {
        "parent": {"database_id": NOTION_READING_DATABASE_ID},
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
            }
        },
        "children": [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": summary_rich_text
                            }
                        }
                    ]
                }
            }
        ]
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    if response.status_code != 200:
        raise Exception(f"Failed to add page to Notion: {response.text}")

# 检查并更新 RSS feed
def update_rss_feeds():
    urls = get_rss_urls_from_notion()
    for rss_url in urls:
        feed = parse_rss_feed(rss_url)
        if feed:
            for entry in feed['entries']:
                title = entry['title']
                link = entry['link']
                summary = entry['summary']
                add_to_notion_database(title, link, summary)

def main():
    update_rss_feeds()

if __name__ == "__main__":
    main()