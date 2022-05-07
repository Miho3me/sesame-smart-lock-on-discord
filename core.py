from subprocess import Popen
import sys
import os
import threading

import json
import yaml
import time
import discord
import datetime
import requests as req
import subprocess
import signal
from logging import basicConfig, getLogger, Formatter, StreamHandler, FileHandler, DEBUG, INFO



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

logger = getLogger(__name__)
logger.setLevel(DEBUG)
os.makedirs("./logs", exist_ok=True)
basicConfig(format="""[%(asctime)s] file: "%(pathname)s", line: %(lineno)s, in function: %(funcName)s, %(levelname)s: %(message)s""",
            datefmt='%Y-%m-%d %H:%M:%S',
            filename=f'./logs/{datetime.datetime.today().date()}.log'
            )

def init():
    global com_reload_pid
    com_reload_pid = 0

def git_pull():
    cmd = "git pull"
    git_pull = subprocess.Popen("exec " + cmd, text=True, stdout=subprocess.PIPE, shell=True)
    logger.debug(git_pull.stdout.readline())
    return git_pull.stdout.readline()


def pip_install():
    cmd = "pip install -r requirements.txt"
    pip_install = os.system(cmd)
    logger.debug(pip_install)

def reload(flag_fn=False):
    global com_reload_pid
    global flag
    flag = flag_fn
    time.sleep(10)
    while True:
        if com_reload_pid == 0:
            dir_path = os.getcwd()
            cmd = f"python3 {dir_path}/sesame_discord.py"
            reload_file = subprocess.Popen("exec " + cmd, stdout=subprocess.PIPE, shell=True)
            logger.debug( "process id = %s" % reload_file.pid )
            logger.debug(reload_file.stdout.readline())
            com_reload_pid = reload_file.pid


@client.event
async def on_ready():

    logger.debug("booted")

@client.event
async def on_message(message):
    if message.guild.id != DISCORD_SERVER_ID or\
       message.channel.name != DISCORD_CHANNEL_NAME or\
       message.author == client.user:
        return
    global com_reload_pid

    if message.content.startswith('/update'):
        logger.debug("/update")
        pull_result = git_pull()
        logger.debug(pull_result)
        if pull_result != f"Already up to date.\n":
            pip_install()
            os.kill(com_reload_pid, signal.SIGTERM)
            logger.debug(com_reload_pid)
            flag = True
            com_reload_pid = 0
            logger.debug("reboot done")
            # await message.channel.send(f'[{datetime.datetime.now(JST).time().strftime("%X")}] update done')
        elif pull_result == f"Already up to date.\n":
            logger.debug("Already up to date.")
            #await message.channel.send(f'[{datetime.datetime.now(JST).time().strftime("%X")}] Already up to date')


if __name__ == '__main__':
    init()
    thread = threading.Thread(target=reload)
    thread.start()
    client.run(DISCORD_TOKEN)
