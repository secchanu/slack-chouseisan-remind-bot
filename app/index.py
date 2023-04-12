import configparser
import csv
import datetime
from functools import reduce
import os
import threading
import time

import schedule
from slack_bolt import Ack, App, BoltContext
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient

from chouseisan import csv2data, getCSV, getHash
from util import get_weekday_str

config = configparser.ConfigParser()
config.read("config.ini")
schedule_path = "./schedule.csv"

app = App(token=config["SLACK"]["BOT_TOKEN"])


@app.command("/subscribe")
def subscribe(ack: Ack, body: dict, client: WebClient):
    ack()
    client.views_open(
        trigger_id=body["trigger_id"],
        view={
            "type": "modal",
            "callback_id": "add_chouseisan_remind",
            "title": {
                "type": "plain_text",
                "text": "調整さんリマインド",
            },
            "blocks": [
                {
                    "type": "input",
                    "block_id": "chouseisan",
                    "label": {
                        "type": "plain_text",
                        "text": "調整さんのイベントのURLを入力してください",
                    },
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "url",
                    },
                },
                {
                    "type": "divider",
                },
                {
                    "type": "section",
                    "text": {
                        "type": "plain_text",
                        "text": "何曜日の何時にリマインドするか選択してください",
                        "emoji": True,
                    },
                },
                {
                    "type": "input",
                    "block_id": "weekday",
                    "element": {
                        "type": "static_select",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Select options",
                            "emoji": True,
                        },
                        "options": [
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "月曜日",
                                    "emoji": True,
                                },
                                "value": "0",
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "火曜日",
                                    "emoji": True,
                                },
                                "value": "1",
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "水曜日",
                                    "emoji": True,
                                },
                                "value": "2",
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "木曜日",
                                    "emoji": True,
                                },
                                "value": "3",
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "金曜日",
                                    "emoji": True,
                                },
                                "value": "4",
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "土曜日",
                                    "emoji": True,
                                },
                                "value": "5",
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "日曜日",
                                    "emoji": True,
                                },
                                "value": "6",
                            },
                        ],
                        "action_id": "picker",
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "曜日",
                        "emoji": True,
                    },
                },
                {
                    "type": "input",
                    "block_id": "time",
                    "element": {
                        "type": "timepicker",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Select time",
                            "emoji": True,
                        },
                        "action_id": "picker",
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "時間",
                        "emoji": True,
                    },
                },
                {
                    "type": "input",
                    "block_id": "channel",
                    "element": {
                        "type": "conversations_select",
                        "action_id": "selector",
                        "response_url_enabled": True,
                        "default_to_current_conversation": True,
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "通知するチャンネル",
                    },
                },
            ],
            "submit": {
                "type": "plain_text",
                "text": "Subscribe",
            },
        },
    )


@app.view("add_chouseisan_remind")
def add_chouseisan_remind(ack: Ack, view: dict, client: WebClient):
    ack()
    values = view["state"]["values"]
    url = values["chouseisan"]["url"]["value"]
    weekday = values["weekday"]["picker"]["selected_option"]["value"]
    time = values["time"]["picker"]["selected_time"]
    channel = values["channel"]["selector"]["selected_conversation"]
    if url and weekday and time and channel:
        hash = getHash(url)
        hour = int(time[:2])
        csvData = getCSV(hash)
        title, data = csv2data(csvData)
        text = f"{title} を登録しました"
        with open(schedule_path, mode="a", encoding="utf-8") as af:
            writer = csv.writer(af)
            writer.writerow([hash, channel, weekday, hour, title])
        client.chat_postMessage(text=text, channel=channel)


def get_unsubscribe_view(selected_channel: str):
    options = []
    with open(schedule_path, mode="r", encoding="utf-8") as rf:
        reader = csv.reader(rf)
        for job in reader:
            if not len(job):
                continue
            hash, channel, weekday, hour, title = job
            if not selected_channel == channel:
                continue
            option = {
                "text": {
                    "type": "plain_text",
                    "text": f"{get_weekday_str(weekday)} {hour}時 {title}",
                    "emoji": True,
                },
                "value": hash,
            }
            options.append(option)
    view = {
        "type": "modal",
        "callback_id": "remove_chouseisan_remind",
        "title": {
            "type": "plain_text",
            "text": "調整さんリマインド",
        },
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "plain_text",
                    "text": "削除する調整さんを選んでください",
                    "emoji": True,
                },
            },
            {
                "type": "actions",
                "block_id": "channel",
                "elements": [
                    {
                        "type": "conversations_select",
                        "action_id": "update_unsubscribe_view",
                        "response_url_enabled": True,
                        "default_to_current_conversation": True,
                    }
                ],
            },
        ]
        + (
            [
                {
                    "type": "input",
                    "block_id": "job",
                    "element": {
                        "type": "static_select",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Select options",
                            "emoji": True,
                        },
                        "options": options,
                        "action_id": "picker",
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "削除する調整さん",
                        "emoji": True,
                    },
                }
            ]
            if len(options)
            else []
        ),
    } | (
        {
            "submit": {
                "type": "plain_text",
                "text": "Unsubscribe",
            }
        }
        if len(options)
        else {}
    )
    return view


@app.command("/unsubscribe")
def unsubscribe(ack: Ack, body: dict, client: WebClient, context: BoltContext):
    ack()
    selected_channel = context["channel_id"]
    client.views_open(
        trigger_id=body["trigger_id"], view=get_unsubscribe_view(selected_channel)
    )


@app.action("update_unsubscribe_view")
def update_unsubscribe_view(ack: Ack, body: dict, client: WebClient):
    ack()
    selected_channel = body["actions"][0]["selected_conversation"]
    client.views_update(
        view_id=body["view"]["id"],
        hash=body["view"]["hash"],
        view=get_unsubscribe_view(selected_channel),
    )


@app.view("remove_chouseisan_remind")
def remove_chouseisan_remind(ack: Ack, view: dict, client: WebClient):
    ack()
    values = view["state"]["values"]
    if not "job" in values:
        return
    selected_channel = values["channel"]["update_unsubscribe_view"][
        "selected_conversation"
    ]
    selected_hash = values["job"]["picker"]["selected_option"]["value"]
    csvData = getCSV(selected_hash)
    title, data = csv2data(csvData)
    text = f"{title} を削除しました"
    jobs = []
    with open(schedule_path, mode="r", encoding="utf-8") as rf:
        reader = csv.reader(rf)
        for job in reader:
            if not len(job):
                continue
            hash, channel, weekday, hour, title = job
            if selected_channel == channel and selected_hash == hash:
                continue
            jobs.append(job)
    with open(schedule_path, mode="w", encoding="utf-8") as wf:
        writer = csv.writer(wf)
        writer.writerows(jobs)
    client.chat_postMessage(text=text, channel=selected_channel)


def get_list_view(selected_channel: str):
    text = ""
    with open(schedule_path, mode="r", encoding="utf-8") as rf:
        reader = csv.reader(rf)
        for job in reader:
            if not len(job):
                continue
            hash, channel, weekday, hour, title = job
            if not selected_channel == channel:
                continue
            row = f"{get_weekday_str(weekday)} {hour}時 {title}"
            text += row
    view = {
        "type": "modal",
        "callback_id": "list_chouseisan_remind",
        "title": {
            "type": "plain_text",
            "text": "調整さんリマインド",
        },
        "blocks": [
            {
                "type": "actions",
                "block_id": "channel",
                "elements": [
                    {
                        "type": "conversations_select",
                        "action_id": "update_list_view",
                        "response_url_enabled": True,
                        "default_to_current_conversation": True,
                    }
                ],
            },
            {
                "type": "divider",
            },
        ]
        + (
            [
                {
                    "type": "context",
                    "elements": [{"type": "plain_text", "text": text, "emoji": True}],
                }
            ]
            if text
            else []
        ),
    }
    return view


@app.command("/list")
def post_list(ack: Ack, body: dict, client: WebClient, context: BoltContext):
    ack()
    selected_channel = context["channel_id"]
    client.views_open(
        trigger_id=body["trigger_id"], view=get_list_view(selected_channel)
    )


@app.action("update_list_view")
def update_list_view(ack: Ack, body: dict, client: WebClient):
    ack()
    selected_channel = body["actions"][0]["selected_conversation"]
    client.views_update(
        view_id=body["view"]["id"],
        hash=body["view"]["hash"],
        view=get_list_view(selected_channel),
    )


def remind(hash: str, channel: str):
    csvData = getCSV(hash)
    title, data = csv2data(csvData)
    today = datetime.date.today()
    future = list(filter(lambda d: d[0] >= today, data))
    next = future[:2]
    if not len(next):
        return False
    text = reduce(
        lambda acc, n: acc + f"{n[0]}: {', '.join(n[1])}\n", next, f"{title}\n"
    )
    app.client.chat_postMessage(text=text, channel=channel)
    return True


def runJob():
    jobs = []
    now = datetime.datetime.now()
    with open(schedule_path, mode="r", encoding="utf-8") as rf:
        reader = csv.reader(rf)
        for job in reader:
            if not len(job):
                continue
            hash, channel, weekday, hour, title = job
            if now.weekday() == int(weekday) and (
                now.hour + int(now.minute > 30)
            ) == int(hour):
                res = remind(hash, channel)
                if not res:
                    continue
            jobs.append(job)
    with open(schedule_path, mode="w", encoding="utf-8") as wf:
        writer = csv.writer(wf)
        writer.writerows(jobs)


def cron():
    schedule.every().hour.at(":00").do(runJob)
    while True:
        schedule.run_pending()
        time.sleep(10)


def slack():
    handler = SocketModeHandler(app, config["SLACK"]["APP_TOKEN"])
    handler.start()


def main():
    with open(schedule_path, mode="a", encoding="utf-8") as wf:
        wf.write("")
    thread_cron = threading.Thread(target=cron)
    thread_cron.start()
    slack()
