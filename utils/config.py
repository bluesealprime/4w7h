from dotenv import load_dotenv 
import os
load_dotenv(os.path.join(os.getcwd(), '.env'))
TOKEN =os.environ.get ("TOKEN")
NAME ="4w7h"
server ="https://discord.gg/JxCFmz9nZP"
ch ="https://discord.com/channels/1324668335069331477/1324668336470102143"
OWNER_IDS = [int(x.strip()) for x in os.environ.get("OWNER_IDS", "").split(",") if x.strip()]
DEV_IDS = [int(x.strip()) for x in os.environ.get("DEV_IDS", "").split(",") if x.strip()]
BotName ="4w7h"
serverLink ="https://discord.gg/JxCFmz9nZP"

invite_link = "https://discord.com/invite/example"
website_link = "https://example.com"
support_link = "https://discord.gg/JxCFmz9nZP"
