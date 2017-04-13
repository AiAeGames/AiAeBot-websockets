# ripple!api
# https://docs.ripple.moe/docs

import requests
import json

with open("./config.json", "r") as f:
    config = json.load(f)

def user(id=None, name=None):
    try:
        request = requests.get("https://ripple.moe/api/v1/users/full", params={"name" : name, "id" : id})
    except requests.exceptions.RequestException as e:
        return
    return json.loads(request.text)

def recent(id=None, limit=1):
    try:
        request = requests.get("https://ripple.moe/api/v1/users/scores/recent", params={"id" : id, "l" : limit})
        return json.loads(request.text)
    except requests.exceptions.RequestException as e:
        return

def isonline(id=None, name=None):
    try:
        request = requests.get("https://c.ripple.moe/api/v1/isOnline", params={"id" : id})
        return json.loads(request.text)
    except requests.exceptions.RequestException as e:
        return

def bid(id):
    try:
        request = requests.get("https://storage.ripple.moe/api/b/%s" % id)
        return json.loads(request.text)
    except requests.exceptions.RequestException as e:
        return

def sid(id):
    try:
        request = requests.get("https://storage.ripple.moe/api/s/%s" % id,)
        return json.loads(request.text)
    except requests.exceptions.RequestException as e:
        return

def md5(id):
    try:
        request = requests.get("https://ripple.moe/api/v1/get_beatmaps", params={"h" : id})
        return json.loads(request.text)
    except requests.exceptions.RequestException as e:
        return

def webdata():
    try:
        request = requests.get("https://pi.aiaegames.xyz/api/users/")
        return request.text
    except requests.exceptions.RequestException:
        return

def findLastDiff(js):
    i = 0
    arr = []
    arr2 = []
    for n in js["ChildrenBeatmaps2"]:
        arr.append(js["ChildrenBeatmaps2"][i]["DifficultyRating"])
        i = i + 1
        order = arr.index(max(arr))
        max_star = max(arr)
        id = js["ChildrenBeatmaps2"][order]["BeatmapID"]
    arr2.append(order)
    arr2.append(id)
    return arr2