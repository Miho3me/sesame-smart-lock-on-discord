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
    url = f'https://api.candyhouse.co/public/sesame/{SESAME_DEVICE_ID}'
    res = req.get(url=url,
                  headers={"Authorization": SESAME_TOKEN}
                  )
    return res


def check_sesame_task(task_id):
    url = f'https://api.candyhouse.co/public/action-result?task_id={task_id}'
    res = req.get(url=url,
                  headers={"Authorization": SESAME_TOKEN}
                  )
    return res


def turn_sesame(task_command="lock", discord_message=None):
    sesame_status = check_sesame_status().json()
    # sesame_status["locked"]
    # sesame_status["battery"]
    # sesame_status["battery"]

    # 10秒ほどおかないとDEVICE_IS_BUSYになり判定がバグる そうでもない？
    time.sleep(1)

    # print(sesame_status)
    if sesame_status["locked"] is True and task_command != "lock" or\
       sesame_status["locked"] is False and task_command != "unlock":
        url = f'https://api.candyhouse.co/public/sesame/{SESAME_DEVICE_ID}'
        res = req.post(url=url,
                       headers={"Authorization": SESAME_TOKEN},
                       data=json.dumps({"command": task_command})
                       )

        loop_count = 0
        while check_sesame_task(res.json()["task_id"]).json()["status"] == "processing":
            loop_count = loop_count + 1
            # print(f"Retry: {loop_count}")
            if loop_count > 11:
                return {"res_result": "loop", "status": None, "task_result": None}
            time.sleep(1)

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
        return {"res_result": dict_result, "status": sesame_status, "task_result": dict_task_result}
    return {"res_result": None, "status": None, "task_result": None}


@client.event
async def on_ready():
    url = "https://api.candyhouse.co/public/sesames"
    headers = {"Authorization": SESAME_TOKEN}
    response = req.get(url, headers=headers)
    return response


@client.event
async def on_message(message):
    if message.guild.id != DISCORD_SERVER_ID or\
       message.channel.name != DISCORD_CHANNEL_NAME or\
       message.author == client.user:
        return

    if message.content.startswith('/lock') or\
       message.content.startswith('/unlock'):

        task_command = message.content[1:]
        result = turn_sesame(task_command)
        print(result)
        now_time = datetime.datetime.now(JST).time().strftime('%X')
        if result["res_result"] is not None:
            if result["res_result"] == "success" and\
               result["task_result"]["successful"] is True:
                await message.channel.send(f'[{now_time}] [{result["status"]["battery"]}%] {task_command} success!')

            elif result["res_result"] == "failed" or\
                 result["task_result"]["successful"] is False:
                await message.channel.send(f'[{now_time}] [{result["status"]["battery"]}%] {task_command} failed.')
                await message.channel.send(f'[{now_time}] {result["task_result"]["error"]}')

            elif result["res_result"] == "loop":
                await message.channel.send(f'[{now_time}] [{result["status"]["battery"]}%] {task_command} failed.')
                await message.channel.send(f'[{now_time}] sesameサーバーが混み合っている可能性があります。再試行して同様のエラーが発生するならばsesameアプリからの操作をお勧めします')

            if result["status"]["battery"] <= 40:
                await message.channel.send(f'バッテリー残量警告[{result["status"]["battery"]}%]: バッテリーの交換をおすすめします')


client.run(DISCORD_TOKEN)
