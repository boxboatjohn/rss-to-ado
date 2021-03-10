import datetime
import feedparser
import os
import sqlite3
import time
from client import Client
from azure.devops.connection import Connection
from azure.devops.v6_0.work_item_tracking.models import JsonPatchOperation
from azure.devops.v6_0.work_item_tracking.models import WorkItemRelation
from azure.devops.v6_0.work_item_tracking.work_item_tracking_client import WorkItemTrackingClient
from msrest.authentication import BasicAuthentication

# Populate variables from environment variables
db_path = os.getenv('DB_PATH')

client = Client()


def init_db(db_conn):
    db_conn.execute("CREATE TABLE IF NOT EXISTS items (guid TEXT PRIMARY KEY, timestamp INTEGER NOT NULL);")


def exists_in_db(c: sqlite3.Cursor, guid: str) -> bool:
    c.execute("SELECT COUNT(*) FROM items WHERE guid = ?", (guid,))
    return c.fetchone()[0] > 0


def insert_in_db(c: sqlite3.Cursor, guid: str, timestamp: float):
    c.execute("INSERT INTO items (guid, timestamp) VALUES (?, ?)",
              (guid, timestamp,))


def main():
    db_conn = sqlite3.connect('feed.db')
    init_db(db_conn)
    work_item_tracking_client = client.init_ado()
    db_cursor = db_conn.cursor()
    # How far back to look for new events
    days_to_include = 2 * 7
    start_datetime = datetime.datetime.today() - datetime.timedelta(days=days_to_include)
    print(f"Start Date: {start_datetime}")
    feed_data = feedparser.parse(client.feed_url)
    curtime = datetime.datetime.now().strftime('%m/%d/%Y')
    f_resp = client.create_work_item(parent_url=client.ad_epic_url, tags=client.ad_tags,
                                     desc=f'Evaluate new Azure features - {curtime}', area_path=client.ad_area_path,
                                     title=f'Evaluate new Azure Features - {curtime}', item_type="Feature")
    feature_url = f_resp.url

    for index, item in enumerate(feed_data.entries):
        published_datetime = datetime.datetime.fromtimestamp(time.mktime(item.published_parsed))
        if published_datetime < start_datetime:
            continue
        elif exists_in_db(c=db_cursor, guid=item.id):
            continue
        try:
            resp = client.create_work_item(parent_url=feature_url, area_path=client.ad_area_path, title=f'{item.title}',
                                           tags=client.ad_tags,
                                           desc=f"{item.description}<br />\n<br />\n<a href=\"{item.link}\">Source</a>")
            print("User Story Response:")
            print(resp)
            print("")
            print(f"User Story ID: {resp.id}")
            print("")
        except Exception as err:
            print(f'Failed to add item {item.title}')
            exit(1)

        insert_in_db(c=db_cursor, guid=item.id, timestamp=published_datetime.timestamp())
        db_conn.commit()

        print(f"Item inserted: {item.title}")
        print(f"Item:    {index}")
        print(f"Title:   {item.title}")
        print(f"Date:    {item.published}")
        print(f"Summary: {item.summary}")
        print(f"Desc:    {item.description}")
        print(f"Link:    {item.link}")
        print(f"GUID:    {item.id}")
        print("")
        print("")

    db_conn.close()


main()
