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

def check_sesame_task(return_task_id):
    res = req.get(url=f'https://api.candyhouse.co/public/action-result?task_id={return_task_id}',
                  headers={"Authorization": SESAME_TOKEN}
                  )
    return res

def turn_sesame(task_command="lock", discord_message=None):
    sesame_status = check_sesame_status().json()
    lock_status = sesame_status["locked"]
    battery_status = sesame_status["battery"]
    responsive = sesame_status["responsive"]

    # 10秒ほどおかないとDEVICE_IS_BUSYになり判定がバグる
    time.sleep(1)
    #print(sesame_status)
    if lock_status is True and task_command != "lock" or lock_status is False and task_command != "unlock":
        res = req.post(url=f'https://api.candyhouse.co/public/sesame/{SESAME_DEVICE_ID}',
                       headers={"Authorization": SESAME_TOKEN},
                       data=json.dumps({"command": task_command})
                       )
        time.sleep(3)

        if "task_id" in res.json():
            task_result = check_sesame_task(res.json()["task_id"])
            if "error" not in task_result.json():
                dict_result = "success"
            elif "error" in task_result.json():
                dict_result = "failed"
            dict_task_result = task_result.json()
        elif "error" in res.json():
            dict_result = "failed"
            dict_task_result = None
        return {"response_result":dict_result, "status":sesame_status, "task_result":dict_task_result}

    return


@client.event
async def on_ready():
    url = "https://api.candyhouse.co/public/sesames"
    headers = {"Authorization": SESAME_TOKEN}
    response = req.get(url, headers=headers)
    return response


@client.event
async def on_message(message):
    if message.guild.id != DISCORD_SERVER_ID or message.channel.name != DISCORD_CHANNEL_NAME or message.author == client.user:
        return

    if message.content.startswith('/lock') or message.content.startswith('/unlock'):
        task_command = message.content[1:]
        result = turn_sesame(task_command)
        #print(result)
        now_time = datetime.datetime.now(JST).time().strftime('%X')
        if result["response_result"] == "success" and result["task_result"]["successful"] is True:
            await message.channel.send(f'[{now_time}] [{result["status"]["battery"]}%] {task_command} success!')
        elif result == "failed" or result["task_result"]["successful"] is False:
            await message.channel.send(f'[{now_time}] [{result["status"]["battery"]}%] {task_command} failed.')
            await message.channel.send(f'[{now_time}] {result["task_result"]["error"]}')
        if result["status"]["battery"] <= 40:
            await message.channel.send(f'バッテリー残量警告[{result["status"]["battery"]}%]: 交換をおすすめします')


client.run(DISCORD_TOKEN)
