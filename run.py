#!/usr/bin/env python
# -*- coding: utf-8 -*-

import irc.bot
import irc.strings
import json, time, re, random, websocket, ripple, ConvertMods, mysql, oaas, logging
from cooldown import cooldown
from threading import Thread

logging.disable(logging.CRITICAL)

with open("config.json", "r") as f:
    config = json.load(f)

class Reconnect(irc.bot.ReconnectStrategy):
    def run(self, bot):
        if not bot.connection.is_connected():
            print("Trying to reconnect...")
            bot.jump_server()

class RippleBot(irc.bot.SingleServerIRCBot):
    def __init__(self):
        irc.bot.SingleServerIRCBot.__init__(self, [(config["ripple_irc"], 6667, config["ripple_password"])], config["ripple_user"], config["ripple_user"], recon=Reconnect())

    def on_privmsg(self, c, e):
        self.do_command(None, e)
        print(e)

    def do_command(self, c, e):
        nick = e.source.nick
        c = self.connection
        args = e.arguments[0].split(" ")
        cmd = args[0]
        if cmd == "login" or cmd == "!login":
            c.privmsg(nick, "Soon it will be back for now add @AiAe#7396 in discord if you want to use the bot.")
        elif cmd == "help" or cmd == "!help":
            c.privmsg(nick, "If you want to use the bot add me on discord @AiAe#7396.")

bot = RippleBot()

class TwitchBot(irc.bot.SingleServerIRCBot):
    connection, cursor = mysql.connect()

    def __init__(self):
        irc.bot.SingleServerIRCBot.__init__(self, [(config["twitch_irc"], 6667, config["twitch_password"])], config["twitch_user"], config["twitch_user"], recon=Reconnect())

    def on_welcome(self, c, e):
        quarry = mysql.execute(self.connection, self.cursor, "SELECT twitch_username FROM ripple WHERE twitch_username IS NOT NULL")
        for row in quarry:
            c.join("#" + row["twitch_username"])

    def on_pubmsg(self, c, e):
        self.do_command(e)

    @cooldown(20)
    def beatmap_request(self, groups, e):
        channel = e.target
        quarry = mysql.execute(self.connection, self.cursor, "SELECT user_id, username, twitch_bot FROM ripple WHERE twitch_username=%s", [channel.replace("#", "")])
        result = quarry.fetchone()
        if result["twitch_bot"] == 1:
            idtype, bid, modsg = groups
            mods = re.findall("(HR|DT|NC|FL|HD|SD|PF|NF|EZ|HT)", modsg.upper())
            api = api2 = None
            if idtype == "s":
                api = ripple.sid(bid)
            else:
                api2 = ripple.bid(bid)
                if api2 != None:
                    api = ripple.sid(api2["ParentSetID"])
                else:
                    self.connection.privmsg(channel, "Error can't load API... sending link only...")
                    bot.connection.privmsg(result["username"], "https://osu.ppy.sh/" + idtype + "/" + bid)
                    return

            if api == None and api2 == None:
                self.connection.privmsg(channel, "Error can't load API... sending link only...")
                bot.connection.privmsg(result["username"], "https://osu.ppy.sh/" + idtype + "/" + bid)
                return
            Mode = 0
            if api:
                lastDiff = ripple.findLastDiff(api)
                beatmapsetid = api["SetID"]
                Mode = api["ChildrenBeatmaps2"][lastDiff[0]]["Mode"]
                bid = api["ChildrenBeatmaps2"][lastDiff[0]]["BeatmapID"]
            elif api2:
                beatmapsetid = api2["ParentSetID"]
                Mode = api2["Mode"]

            gimme_that_pp = oaas.pp(id=bid, mods=ConvertMods.Mods(mods))
            if gimme_that_pp == None:
                self.connection.privmsg(channel, "Error can't load API... sending link only...")
                bot.connection.privmsg(result["username"],
                                       "https://osu.ppy.sh/" + idtype + "/" + bid)
                return
            formatter = {
                "sender": e.source.nick,
                "beatmapsetid": beatmapsetid,
                "artist": gimme_that_pp["artist"],
                "title": gimme_that_pp["title"],
                "bpm": gimme_that_pp["bpm"],
                "version": gimme_that_pp["diff"],
                "stars": gimme_that_pp["stars"],
                "all_mods": ''.join(mods)
            }
            p = ""
            if Mode == 0:
                pp = {
                    "p96": gimme_that_pp["pp"]["96"],
                    "p97": gimme_that_pp["pp"]["97"],
                    "p98": gimme_that_pp["pp"]["98"],
                    "p99": gimme_that_pp["pp"]["99"]
                }
                p = "(97% {p97}pp, 98% {p98}pp, 99% {p99}pp)".format(**pp)
            f = "{artist} - {title} [{version}] {all_mods} {bpm}BPM {stars}★ ".format(**formatter)
            s = "{sender}: [osu://dl/{beatmapsetid} {artist} - {title} [{version}]] {all_mods} {bpm}BPM {stars}★ ".format(**formatter)

            self.connection.privmsg(channel, f + p)
            bot.connection.privmsg(result["username"], s + p)

    @cooldown(10)
    def commands(self, groups, e):
        channel = e.target
        quarry = mysql.execute(self.connection, self.cursor, "SELECT np FROM ripple WHERE twitch_username=%s", [channel.replace("#", "")])
        result = quarry.fetchone()
        self.connection.privmsg(channel, result["np"])

    def do_command(self, e):
        c = self.connection
        message = e.arguments[0]
        regexes = [
            ('https?:\/\/osu\.ppy\.sh\/([bs])\/([0-9]+)(.*)', self.beatmap_request),
            ('np', self.commands),
            ('!np', self.commands)
        ]

        for regex in regexes:
            reg = re.match(regex[0], message)
            if reg:
                regex[1](reg.groups(), e)

tbot = TwitchBot()

def on_message(ws, message):
    connection, cursor = mysql.connect()
    ajson = json.loads(message)
    if ajson["type"] == "new_score":
        beatmap_info = ripple.md5(ajson["data"]["beatmap_md5"])
        formatter = {
            "id": ajson["data"]["id"],
            "beatmapid": beatmap_info[0]["beatmap_id"],
            "song": beatmap_info[0]["artist"] + " - " + beatmap_info[0]["title"] + " [" + beatmap_info[0]["version"] + "]",
            "stars": float(beatmap_info[0]["difficultyrating"]),
            "score": ajson["data"]["score"],
            "mods": ConvertMods.ModsRev(ajson["data"]["mods"]),
            "play_mode": ajson["data"]["play_mode"],
            "accuracy": ajson["data"]["accuracy"],
            "pp": ajson["data"]["pp"],
            "combo": ajson["data"]["max_combo"],
            "max_combo": beatmap_info[0]["max_combo"]
        }
        id = ajson["data"]["user_id"]
        mode = ajson["data"]["play_mode"]
        user = ripple.user(id=id)
        quarry = mysql.execute(connection, cursor, "SELECT twitch_username, std_pp, std_rank FROM ripple WHERE user_id=%s", [id])
        result = quarry.fetchone()
        r = ripple.user(id=id)
        if mode == 0:
            if r["std"]["pp"] != result["std_pp"]:
                rank = r["std"]["global_leaderboard_rank"]
                pp = r["std"]["pp"]
                msg = "Rank %+d (%+d pp)" % ((result["std_rank"] - rank), (pp - result["std_pp"]))
                mysql.execute(connection, cursor, "UPDATE ripple SET std_pp=%s, std_rank=%s WHERE user_id=%s", [pp, rank, r["id"]])
                bot.connection.privmsg(user["username"].replace(" ", "_"), msg)
            bot.connection.privmsg(user["username"].replace(" ", "_"), "[https://osu.ppy.sh/b/{beatmapid} {song}] {mods} | {accuracy:.2f}% | {pp:.2f}pp | {combo}/{max_combo} | {stars:.2f}★".format(**formatter))
        elif mode == 1:
            bot.connection.privmsg(user["username"].replace(" ", "_"), "[https://osu.ppy.sh/b/{beatmapid} {song}] {mods} | {accuracy:.2f}% | {score:,d} score | {combo}/{max_combo} | {stars:.2f}★".format(**formatter))
        elif mode == 2:
            bot.connection.privmsg(user["username"].replace(" ", "_"), "[https://osu.ppy.sh/b/{beatmapid} {song}] {mods} | {accuracy:.2f}% | {score:,d} score | {combo}/{max_combo} | {stars:.2f}★".format(**formatter))
        elif mode == 3:
            bot.connection.privmsg(user["username"].replace(" ", "_"), "[https://osu.ppy.sh/b/{beatmapid} {song}] {mods} | {accuracy:.2f}% | {pp:.2f}pp | {combo}/{max_combo} | {stars:.2f}★".format(**formatter))
        if result["twitch_username"] != "":
            if mode == 0 or mode == 3:
                tbot.connection.privmsg("#" + result["twitch_username"], "{song} {mods} | {accuracy:.2f}% | {pp:.2f}pp | {combo}/{max_combo} | {stars:.2f}★".format(**formatter))
            else:
                tbot.connection.privmsg("#" + result["twitch_username"], "{song} {mods} | {accuracy:.2f}% | {score:,d} score | {combo}/{max_combo} | {stars:.2f}★".format(**formatter))

def on_error(ws, error):
    exit()

def on_close(ws):
    exit()

def on_open(ws):
    ws.send(ripple.webdata())

websocket.enableTrace(True)
ws = websocket.WebSocketApp("wss://api.ripple.moe/api/v1/ws", on_message=on_message, on_error=on_error, on_close=on_close)
ws.on_open = on_open

Thread(target=bot.start).start()
Thread(target=tbot.start).start()
time.sleep(5)
Thread(target=ws.run_forever, kwargs={"ping_interval": 10}).start()