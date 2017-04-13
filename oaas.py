import requests, json

def pp(id, mods=0):
    try:
        request = requests.post("https://getdownon.it/better_oaas/", data={"id": id, "mods": mods, "percentages": "[96, 97, 98, 99]"})
    except requests.exceptions.RequestException as e:
        return
    return json.loads(request.text)