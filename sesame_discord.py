import discord
import requests as req
import json
import datetime
import yaml
import time

with open('token.yml') as file:
    yml = yaml.safe_load(file)
    DISCORD_TOKEN = yml["discord"]["token"]
    DISCORD_SERVER_ID = yml["discord"]["server"]
    DISCORD_CHANNEL_NAME = yml["discord"]["channel"]
    SESAME_TOKEN = yml["sesame"]["token"]
    SESAME_DEVICE_ID = yml["sesame"]["device_id"]

client = discord.Client()
t_delta = datetime.timedelta(hours=9)
JST = datetime.timezone(t_delta, 'JST')


def check_sesame_status():
    res = req.get(url=f'https://api.candyhouse.co/public/sesame/{SESAME_DEVICE_ID}',
                  headers={"Authorization": SESAME_TOKEN}
                  )
    return res


def turn_sesame(task_command="lock", discord_message=None):
    sesame_status = check_sesame_status().json()
    lock_status = sesame_status["locked"]
    battery_status = sesame_status["battery"]
    responsive = sesame_status["responsive"]

    # 10秒ほどおかないとDEVICE_IS_BUSYになり判定がバグる
    time.sleep(10)
    if lock_status is True and task_command != "lock" or lock_status is False and task_command != "unlock":
    #if True:
        res = req.post(url=f'https://api.candyhouse.co/public/sesame/{SESAME_DEVICE_ID}',
                       headers={"Authorization": SESAME_TOKEN},
                       data=json.dumps({"command": task_command})
                       )
        if "task_id" in res.json():
            return True, sesame_status
        elif "error" in res.json():
            return False, sesame_status
        else:
            return res.json(), sesame_status
    return "identical"


@client.event
async def on_ready():
    url = f"https://api.candyhouse.co/public/sesames"
    headers = {"Authorization": SESAME_TOKEN}
    res = req.get(url, headers=headers)
    return res


@client.event
async def on_message(message):
    if message.guild.id != DISCORD_SERVER_ID or message.channel.name != DISCORD_CHANNEL_NAME or message.author == client.user:
        return

    if message.content.startswith('/lock') or message.content.startswith('/unlock'):
        task_command = message.content[1:]
        result, sesame_status = turn_sesame(task_command)
        now_time = datetime.datetime.now(JST).time().strftime('%X')
        if result is True:
            await message.channel.send(f'[{now_time}] [{sesame_status["battery"]}%] {task_command} success!')
        elif result is False:
            await message.channel.send(f'[{now_time}] [{sesame_status["battery"]}%] {task_command} failed.')
            await message.channel.send(f'[{now_time}] sesame本体は他の端末で使用中か、インターネット接続に問題があるため、WiFiモジュールが青点滅しているか確認してください。')
        else:
            await message.channel.send(f'[{now_time}] [{sesame_status["battery"]}%] {result}')
        if sesame_status["battery"] <= 40:
            await message.channel.send(f'バッテリー残量警告[{battery_percent}%]: 交換をおすすめします')


client.run(DISCORD_TOKEN)
