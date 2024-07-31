# coding=utf-8

import feedparser
from bs4 import BeautifulSoup

import requests
import json
import os
import time
import re

from datetime import datetime, timezone, timedelta
from dateutil import parser

# 从环境变量中获取Notion API信息
NOTION_API_KEY = os.getenv('NOTION_API_KEY')
NOTION_READING_DATABASE_ID = os.getenv('NOTION_READING_DATABASE_ID')
NOTION_URL_DATABASE_ID = os.getenv('NOTION_URL_DATABASE_ID')

headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
}

def get_rss_feeds_from_notion():
	url = f"https://api.notion.com/v1/databases/{NOTION_URL_DATABASE_ID}/query"
	payload = {
		"page_size": 100,
		"filter": {
			"property": "Disabled",
			"checkbox": {"equals": False},
		}
	}
	response = requests.post(url, json=payload, headers=headers)

	if response.status_code != 200:
		raise Exception(f"Failed to query Notion database: {response.text}")
	
	data = response.json()

	with open('db.json', 'w', encoding='utf8') as f:
		json.dump(data, f, ensure_ascii=False, indent=4)

	pages = data['results']
	rss_feeds = []

	for page in pages:
		page_id = page["id"]
		props = page["properties"]
		feed_name = props["Feed Name"]["title"][0]["text"]["content"]
		url = props["URL"]["url"]
		isDisabled = props["Disabled"]["checkbox"]
		print(feed_name+'\t'+url+'\t'+str(isDisabled)+'\n')

		rss_feeds.append(url)
		# if url and (not isDisabled):
		# 	rss_feeds.append(url)

	return rss_feeds


def parse_rss_feed(url):
	data = []


	url = requests.get(url)
	
	parsed_feed = feedparser.parse(url.content)
	soup = BeautifulSoup(url.content, 'xml')

	feed_title = soup.find('title').text if soup.find('title') else 'No title available'

	for entry in parsed_feed.entries:
		if entry.get("published"):
			published_time = parser.parse(entry.get("published"))
		else:
			published_time = datetime.now(timezone.utc)
		data.append(
			{
				"title": entry.get("title"),
				"link": entry.get("link"),
				"time": published_time.astimezone(timezone(timedelta(hours=8))).strftime("%Y-%m-%dT%H:%M:%S%z"),
				"summary": re.sub(r"<.*?>|\n*", "", entry.get("summary"))[:2000],
			}
		)

		# title = entry.get('title', 'No title')
		# link = entry.get("link")
		# print("\n条目:")
		# print(f"Title: {title}")
		# print(f"Link: {link}")
		# data.append(
		# 	{
		# 		"Title": {"title": [{"text": {"content": {entry.get('title', 'No title')}}}]},
		# 		"Link": {"url": entry.get('link', 'No link')},
		# 		# "Published": {"date": {"start": entry.get('published', entry.get('pubDate', 'No published date'))}},
				
		# 		# "Title": entry.get('title', 'No title'),
		# 		# "Link": entry.get('link', 'No link'),
		# 		# "Published": entry.get('published', entry.get('pubDate', 'No published date'))
		# 	}
		# )
		# content.append(
		# 	[
		# 		{
		# 			"object": "block",
		# 			"type": "paragraph",
		# 			"paragraph": {
		# 				"rich_text": [
		# 					{
		# 						"type": "text",
		# 						"text": {
		# 							"content": entry.get('content','No content')
		# 						}
		# 				}
		# 				]
		# 			}
		# 		}
		# 	]
		# )
	return data[:3]



def add_to_notion_database(entry):
	print(entry.get("title"))
	data = {
		"parent": {"database_id": NOTION_READING_DATABASE_ID},
		"properties": {
			"Title": {
				"title": [
					{
						"type": "text",
						"text": {"content": entry.get("title")},
					}
				]
			},
			"Link": {"url": entry.get("link")},
			# "Origin": {
			# 	"select": {
			# 		"name": entry.get("rss").get("title"),
			# 	}
			# },
			"Published": {"date": {"start": entry.get("time")}},
		},
		"children": [
			{
				"type": "paragraph",
				"paragraph": {
					"rich_text": [
						{
							"type": "text",
							"text": {"content": entry.get("summary")},
						}
					]
				},
			}
		],
	}
	# res = requests.request("POST", url="https://api.notion.com/v1/pages", headers=headers, data=json.dumps(data))
	# print(res.status_code)
	# return res.json()	


	create_url = "https://api.notion.com/v1/pages"

	# payload = {"parent": {"database_id": NOTION_READING_DATABASE_ID}, "properties": data, "children": content}

	res = requests.post(create_url, headers=headers, json=data)
	print(res.content)
	return res



def update():
	rss_feeds = get_rss_feeds_from_notion()
	# print(rss_feeds)
	for rss_feed in rss_feeds:
		entries = parse_rss_feed(rss_feed)
		for entry in entries:
			add_to_notion_database(entry)

if __name__ == "__main__":
	update()