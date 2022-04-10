# sesame-smart-lock-on-discord
初代セサミとsesame miniのみ対応
sesame3とsesame4については対応外
また、使用にはWiFiモジュール(別売)とdiscordが必要です

# Installation
```bash
pip install -r requirements.txt
```

# Usage
```bash
git clone https://github.com/Miho3me/sesame-smart-lock-on-discord.git
cd sesame-smart-lock-on-discord
vi token.yml
python sesame_discord.py
```

# discord
```bash
discord上で管理者権限を持ったbotを作成し、対象サーバーに招待すること、token.ymlにて指定したchannel nameと同じチャンネルを作成してください
```

# token.yml
```bash
sesame:
  token: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX_XXXXXXXXXXXXXXXXX_XXXXXXXXXXXXXXXXXXXXXXX # sesame's api key
  device_id: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx #sesame device ID
discord:
  token: XXXXXXXXXXXXXXXXXXXXXXXX.XXXXXX.XXXXXXXXXXXXXXXXXX_XXXXXXXX # discord bot's token
  server: 123456789012345678 # server ID
  channel: sesame # channel name
```
