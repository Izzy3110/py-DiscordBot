from __future__ import unicode_literals
import os
import json
import discord

from wyl.mongo import update_object, find_some, do_insert_weather, get_latest_weather
from wyl.mail_listener import Mail
from wyl.weather import Weather
from datetime import datetime

client = discord.Client()
owm_token = os.environ["OPENWEATHERMAP_TOKEN"]

admin_users = ["Izzy3110"]

loc_set = False
tries_remaining = 3
yn_set = False
users_lat_lon = {}
users_lat_lon_tmp = {}
weather_data_requests = {}
Weather_ = Weather(owm_token)


def process_message(message, category=None):
    print(message.content.split(" ")[0])
    if category is not None:
        print(category)
        if category == "Weather":
            Weather_.process_message(message)


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


@client.event
async def on_message(message):
    global admin_users, loc_set, tries_remaining, yn_set, users_lat_lon
    is_admin = message.author.name in admin_users
    if message.author == client.user:
        return
    if yn_set:
        lat_, lon_ = users_lat_lon_tmp[str(message.author.name)]
        if message.content == "y" or message.content == "Y":
            await message.channel.send("Setting location: Lat: " + str(lat_) + " Lon: " + str(lon_))
            users_lat_lon = users_lat_lon_tmp
            for user in users_lat_lon.keys():
                print(user)

                results = await find_some({})
                for entry in results:
                    print(entry["_id"])
                    print(users_lat_lon)
                    if user in users_lat_lon.keys():
                        lat_, lon_ = users_lat_lon[user]
                        updated = update_object(entry["_id"], user, lat_, lon_)
                        print(updated)
                    #print(users_lat_lon[user]["lat"])
                    #print(users_lat_lon[user]["lon"])
                    # updated = update_object(entry["_id"], user, users_lat_lon[user]["lat"], users_lat_lon[user]["lon"])
                    #print(updated)
                # inserted = insert_object(user)
                # updated = update_object(user, users_lat_lon[user]["lat"], users_lat_lon[user]["lon"])
                # print(inserted)
                # print(updated)
            loc_set = False
            await message.channel.send("-> deactivating")
        elif message.content == "n" or message.content == "N":
            await message.channel.send("Lets try again")

        else:
            await message.channel.send("not a valid answer - aborting")
            loc_set = False
            await message.channel.send("-> deactivating")
        yn_set = False
        return

    if loc_set:
        # print(message.content)
        try:
            lat, lon = message.content.split(" ")

            # print(lat)
            # print(lon)
            try:
                lat_ = float(lat)
                lon_ = float(lon)
                if message.author.name not in users_lat_lon_tmp.keys():
                    users_lat_lon_tmp[str(message.author.name)] = [lat_, lon_]
                # print("lat: " + str(lat_))
                # print("lon: " + str(lon_))
                await message.channel.send("Lat: " + str(lat_) + " Lon: " + str(lon_))
                await message.channel.send("is this correct? (y/n)")
                yn_set = True
            except ValueError:
                print("not a valid value")
                if tries_remaining == 0:
                    loc_set = False
                    await message.channel.send("-> deactivating")
                else:
                    tries_remaining -= 1

        except ValueError:
            print("got: "+message.content)

        return

    if message.content.startswith('$hello'):
        if is_admin:
            await message.channel.send("Hello Admin!")
        else:
            await message.channel.send('Hello!')

    if message.content.startswith('$weather'):
        process_message(message, category="Weather")
        if "set location" in message.content:
            print("setting location")
            loc_set = True
            await message.channel.send("<- activating")
        else:
            if message.content == '$weather get':
                await message.channel.send("getting user lat lon")
                results = await find_some({})
                for entry in results:
                    # print(entry["_id"])
                    for k in entry.keys():
                        if k == message.author.name:
                            lat_ = entry[k]["lat"]
                            lon_ = entry[k]["lon"]

                            """
                            print("lat: " + str(lat_) + " lon: " + str(lon_))
                            weather_data = Weather_.get_weather_data(lat_, lon_)
                            print(weather_data)
                            result_ = await do_insert_weather(weather_data)
                            print(result_)
                            await message.channel.send(json.dumps(weather_data,indent=4))
                            """
                            times, results = await get_latest_weather()
                            secs_ = []
                            for uuid in times.keys():
                                seconds = times[uuid]
                                secs_.append(seconds)

                            if min(secs_) > 300:
                                print("getting new ( over 300 )")
                                weather_data = Weather_.get_weather_data(lat_, lon_)
                                result_ = await do_insert_weather(weather_data)
                                await message.channel.send(json.dumps(weather_data, indent=4))
                            else:
                                print("returning result")
                                current_uuid = None
                                for uuid_ in times:
                                    if times[uuid_] == min(secs_):
                                        current_uuid = uuid_
                                        break
                                if current_uuid is not None:
                                    print("uuid: "+current_uuid)
                                    for document in results:
                                        for k in document.keys():
                                            if k == current_uuid:
                                                weather_data = document[current_uuid]["data"]

                                                await message.channel.send(datetime.fromtimestamp(document[current_uuid]["t"]).strftime("%d.%m.%Y %H:%M:%S")+"\n"+json.dumps(weather_data, indent=4)+"\n"+"Data from: "+datetime.fromtimestamp(document[current_uuid]["t"]).strftime("%d.%m.%Y %H:%M:%S"))
                                                break

                            break
                            break
                """
                if len(list(users_lat_lon.keys())) > 0:
                    if message.author.name in list(users_lat_lon.keys()):
                        lat_ = users_lat_lon[message.author.name][0]
                        lon_ = users_lat_lon[message.author.name][1]
                        
                   
                else:
                    await message.channel.send("no user lat-lon detected")
                    await message.channel.send('usage: $weather set location')
                    await message.channel.send('> Follow instructions')
                 """
    if message.content.startswith('$mails'):
        if not is_admin:
            await message.channel.send("Error: not an Admin!")
        else:
            print("getting unseen mails")
            await message.channel.send("[PROCESSING]: getting unread mails")
            Mail_ = Mail()
            Mail_.login()
            messages = Mail_.get_unseen_messages()
            unread_mails_len = len(Mail_.filter_results.keys())
            await message.channel.send(
                "[RESULT]: found " + str(unread_mails_len) + " unread mails for " + Mail_.email_account)
            for mail_id in Mail_.filter_results.keys():
                mail_ = Mail_.filter_results[mail_id]
                subject_ = mail_["subject"]
                from_ = mail_["from"]
                await message.channel.send(" - "+subject_+" ( "+from_+" )")

            # print(json.dumps(Mail_.filter_results, indent=4))
            Mail_.shutdown()


client.run(os.environ["DC_BOT_TOKEN"])
