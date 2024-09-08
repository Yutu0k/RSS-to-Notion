import feedparser
from bs4 import BeautifulSoup

import re
import json
import requests
from datetime import datetime, timezone, timedelta
from dateutil import parser
import time

now = datetime.now(timezone.utc)
load_time = 60  # 导入60天内的内容


def parse_rss_entries(url, retries=3):
	entries = []
	feeds = []
	for attempt in range(retries):
		try:
			res = requests.get(
				url=url,
				headers={"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.55 Safari/537.36 Edg/96.0.1054.34"},
			)
			error_code = 0
		except requests.exceptions.ProxyError as e:
			print(f"Load {url} Error, Attempt {attempt + 1} failed: {e}")
			time.sleep(1)  # 等待1秒后重试
			error_code = 1
		except requests.exceptions.ConnectTimeout as e:
			print(f"Load {url} Timeout, Attempt {attempt + 1} failed: {e}")
			time.sleep(1)  # 等待1秒后重试
			error_code = 1

		if error_code == 0:
			parsed_feed = feedparser.parse(res.content)
			soup = BeautifulSoup(res.content, 'xml')

			## Update RSS Feed Status
			feed_title = soup.find('title').text if soup.find('title') else 'No title available'
			feeds = {
				"title": feed_title,
				"link": url,
				"status": "Active"
			}

			for entry in parsed_feed.entries:
				if entry.get("published"):
					published_time = parser.parse(entry.get("published"))
				else:
					published_time = datetime.now(timezone.utc)
				if not published_time.tzinfo:
					published_time = published_time.replace(tzinfo=timezone(timedelta(hours=8)))
				if now - published_time < timedelta(days=load_time):
					cover = BeautifulSoup(entry.get("summary"),'html.parser')
					cover_list = cover.find_all('img')
					src = "https://www.notion.so/images/page-cover/rijksmuseum_avercamp_1620.jpg" if not cover_list else cover_list[0]['src']
					# Use re.search to find the first match
					entries.append(
						{
							"title": entry.get("title"),
							"link": entry.get("link"),
							"time": published_time.astimezone(timezone(timedelta(hours=8))).strftime("%Y-%m-%dT%H:%M:%S%z"),
							"summary": re.sub(r"<.*?>|\n*", "", entry.get("summary"))[:2000],
							"content": entry.get("content"),
							"cover": src
						}
				)

			return feeds, entries[:50]
			# return feeds, entries[:3]	
		
	feeds = {
		"title": "Unknown",
		"link": url,
		"status": "Error"
	}

		
	return feeds, None


class NotionAPI:
	NOTION_API_pages = "https://api.notion.com/v1/pages"
	NOTION_API_database = "https://api.notion.com/v1/databases"


	def __init__(self, secret, read, feed) -> None:
		self.reader_id = read
		self.feeds_id = feed
		self.headers = {
			"Authorization": f"Bearer {secret}",
			"Notion-Version": "2022-06-28",
			"Content-Type": "application/json",
		}
		# self.delete_rss()

	def queryFeed_from_notion(self):
		"""
		从URL Database里读取url和page_id

		return:
		dict with "url" and "page_id"
		"""
		rss_feed_list = []
		url=f"{self.NOTION_API_database}/{self.feeds_id}/query"
		payload = {
			"page_size": 100,
			"filter": {
				"property": "Disabled",
				"checkbox": {"equals": False},
			}
		}
		response = requests.post(url, headers=self.headers, json=payload)

		# Check Status
		if response.status_code != 200:
			raise Exception(f"Failed to query Notion database: {response.text}")
		
		# Grab requests
		data = response.json()

		# Dump the requested JSON file for test
		# with open('db.json', 'w', encoding='utf8') as f:
		# 	json.dump(data, f, ensure_ascii=False, indent=4)

		rss_feed_list = []
		for page in data['results']:
			props = page["properties"]
			multi_select = props["Tag"]["multi_select"]
			name_color_pairs = [(item['name'], item['color']) for item in multi_select]
			rss_feed_list.append(
				{
					"url": props["URL"]["url"],
					"page_id": page.get("id"),
					"tags": name_color_pairs
				}
			)

		return rss_feed_list

	def saveEntry_to_notion(self, entry, page_id, tags):
		"""
		Save entry lists into reading database

		params: entry("title", "link", "time", "summary"), page_id

		return:
		api response from notion
		"""
		# print(entry.get("cover"))
		# Construct post request to reading database
		payload = {
			"parent": {"database_id": self.reader_id},
			"cover": {
				"type": "external",
				"external": {"url": entry.get("cover")}
			},
			"properties": {
				"Name": {
					"title": [
						{
							"type": "text",
							"text": {"content": entry.get("title")},
						}
					]
				},
				"URL": {"url": entry.get("link")},
				"Published": {"date": {"start": entry.get("time")}},
				"Source":{
					"relation": [{"id": page_id}]
				},
				"Tag": {
					"multi_select": [{"name": tag[0], "color": tag[1]} for tag in tags]
				}
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
		res = requests.post(url=self.NOTION_API_pages, headers=self.headers, json=payload)


		print(res.status_code)
		return res
	
	def saveFeed_to_notion(self, prop, page_id):
		"""
		Update feed info into URL database

		params: prop("title", "status"), page_id

		return:
		api response from notion
		"""

		# Update to Notion
		url = f"{self.NOTION_API_pages}/{page_id}"
		payload = {
			"parent": {"database_id": self.feeds_id},
			"properties": {
				"Feed Name": {
					"title": [
						{
							"type": "text",
							"text": {"content": prop.get("title")},
						}
					]
				},
				"Status":{
					"select":{
						"name": prop.get("status"),
						"color": "red" if prop.get("status") == "Error" else "green"
					}
					
				}
			},
		}

		res = requests.patch(url=url, headers=self.headers, json=payload)
		print(res.status_code)
		return res

	## Todo: figure out deleting process
	# def delete_rss(self):
	# 	filter_json = {
	# 		"filter": {
	# 			"and": [
	# 				{
	# 					"property": "Check",
	# 					"checkbox": {"equals": True},
	# 				},
	# 				{
	# 					"property": "Published",
	# 					"date": {"before": delete_time.strftime("%Y-%m-%dT%H:%M:%S%z")},
	# 				},
	# 			]
	# 		}
	# 	}
	# 	results = requests.request("POST", url=f"{self.NOTION_API_database}/{self.reader_id}/query", headers=self.headers, json=filter_json).json().get("results")
	# 	responses = []
	# 	if len(results) != 0:
	# 		for result in results:
	# 			url = f"https://api.notion.com/v1/blocks/{result.get('id')}"
	# 			responses += [requests.delete(url, headers=self.headers)]
	# 	return responses
	
