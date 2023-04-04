# slack-chouseisan-remind-bot

## 使用方法

### 依存関係のインストール

Poetry がインストールされている場合

```sh
poetry install
```

そうでない場合

```sh
pip install .
```

### アプリの準備

[Slack API: Applications](https://api.slack.com/apps) からアプリを作成 (From Scratch) する

Basic Information の App-Level Tokens に
`connections:write`を追加した Token を生成する  
(これを`APP_TOKEN`として扱う)

OAuth & Permissions の Scopes の Bot Token Scopes に
`chat:write` `chat:write.public` `commands`を追加する

OAuth & Permissions の OAuth Tokens for Your Workspace からワークスペースにインストールする  
インストール後に Bot User OAuth Token が生成される  
(これを`BOT_TOKEN`として扱う)

以下のような`config.ini`を`README.md`と同じフォルダ内に作成し

```ini
[SLACK]
APP_TOKEN=xapp-XXXXXXXXXXXXXXXX
BOT_TOKEN=xoxb-XXXXXXXXXXXXXXXX
```

のようにそれぞれ対応した Token を入れる

### 実行

```sh
python app
```
