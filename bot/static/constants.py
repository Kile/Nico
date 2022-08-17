import json
import discord

from enum import Enum
from pymongo import MongoClient

from bot.utils.functions import is_dev

with open("config.json", "r") as config_file:
    config = json.loads(config_file.read())

TOKEN = config["token"]

CLUSTER = MongoClient(config['mongo'])

DB = CLUSTER["Will" if is_dev() else "Nico"]

PARTNERS = DB["partners"]
EVENT = DB["event"]
CONSTANTS = DB["constants"]

DISBOARD = 302050872383242240

ACTIVITY_EVENT = CONSTANTS.find_one({"_id": "activity_event"})["active"]

WELCOME_MESSAGE = \
""" Welcome to Kids In The Dark **{}**!
I am Nico, KITD's own bot. To ensure you are familiar with how this server works, please read through <#710941242963263638> and <#920102551116980226>. Afterwards hop into my dms and use the slash command `/join` to answer a few questions about <#710941242963263638> and <#920102551116980226> to ensure you have read them.

Your answers will be automatically checked, so make sure you write short answers as long ones might not be included in our possible answer list.

Please also make sure to open your dms to Nico before running the `/join` command, else he will not be able to respond.

Not sure what to do? Something isn't working? Need help?
Feel free to dm a staff member at any point to ask for help.

I hope you enjoy your stay!
"""

DID_INFO = "This is an explanation about the purpose of the <@466378653216014359> bot, why some people talking appear as bots and what DID is. DID is short for Dissociative Identity Disorder, a disorder that is caused by trauma and splits your personality up in different \"alters\". Those alters are their Person on their own with their interests, personality, gender, etc. This is where <@466378653216014359> comes in. One alter always has control over the body and if the control changes, that is called a \"switch\". For every alter to feel more like themselves with just one discord account, they tell the bot which alter currently has the control and depending on that, the bot resends their messages with a different name and Profile Picture. So if you do not have DID, don't use <@466378653216014359>, and also this explains why sometimes \"bots talk\".\n[Learn more about DID](https://en.wikipedia.org/wiki/Dissociative_identity_disorder)"

EVENT_EXPLANATION = \
f"""This is a short explaination going over how the event works.

**How points are awarded:**
Every message sent 10 seconds after your last one will get you points.

The base points per message are 10

The points are modified by the following factors:

```
points = 10

points = points x (1 + (0.1 x (streak - 1))
points = points x (0.1 x diminishing returns)

if it has been 10+ minutes since the last message in the channel:
points = points x 2

if you have a booster:
points = points x active boost

if you are a server booster:
points = points x 1.2
```
[Source code](https://github.com/Kile/Nico/blob/main/bot/cogs/events.py#L79-L104)

**How boosts work:**
There is a 1% chance for boosters to pop up in chat as a response to a message. If they do the first to click the "Claim" button recieves it.
You can also use `/event buy` to buy a booster.
If someone has been nice to you, every 24h you can gift someone a x1.5 booster with `/event karma <user>`.

Boosts are active for 1h

**What does karma do?**
Once every 24h you can give someone a booster with `/event karma <user>`. However karma is also counted seperately and the top karma recievers will get a prize (if they are not already in the top points earners).

**What are diminishing returns?**
As you continue to send messages, eventuall what you get out of it will be less than 100% (diminishing returns).
This is done so that people who haven't been able to send too many messages still have a chance to catch up to the leaders.

**What are streaks?**
Each consequtive day you send at least 10 messages will increase your streak. However if you miss a day it will be reset.

**What requirements do I need to meet to be in the random draw?**
Your points must be more than or equal to the average points of the server.
"""

SERVER_QUESTIONS = [
    {
        "question": "What command do you use to gain roles?",
        "answer": ["/roles", "roles", "role", "/role"]
    },
    {
        "question": "How do you get access to vent channels?",
        "answer": ["apply", "/apply", "by using /apply", "by applying", "by using apply", "with /apply", "with apply"]
    },
    {
        "question": "What is the maximum age for the server?",
        "answer": ["22", "22 years", "22 years old", "22 y", "22y", "twenty two", "twenty two years", "twenty two years old", "twentytwo", "twenty-two"]
    },
    {
        "question": "You will be tempbanned after how many warns?",
        "answer": ["3", "3 warns", "three warns", "three"]
    },
    {
        "question": "What command do you use for info about DID?",
        "answer": ["did", "/did"]
    },
    {
        "question": "What to do against troll as member?",
        "answer": ["untrust", "/untrust", "use untrust", "use /untrust", "report"]
    },
    {
        "question": "Are you allowed to swear in #general?",
        "answer": ["no", "no i am not", "not allowed", "not", "with censor", "only when censoring", "censor"]
    }
]

class KITDServer:
    ID = 710871326557995079
    
    APPLICATION_CHANNEL = 730811764652113960
    FEEDBACK_CHANNEL = 737799496712323154
    UNTRUSTED_CHANNEL = 729078073135202396
    SOS_CHANNEL = 712384341442822184
    GENERAL_CHANNEL = 710873588646936576
    POTATO_BONUS_CHANNEL = 1005608836486406254
    WELCOME_CHANNEL = 726053325623263293
    EVENT_DROP_CHANNELS = [710873588646936576, 712132952896831488, 712049873674960906, 729161403713191997, 714821065897148496, 739525325267927082, 712049825583202345, 712408301467598928, 712476683394875412, 753007572579254283, 765690813962518558]
    EVENT_EXCLUDED_CHANNELS = [739525325267927082, 714567214187020368, 739218822065815592, 1005619816775831602, 726170868924809216, 716453938966036490, 725058055275937882]
    UPDATE_CHANNEL = 726803975680163920
    INFORMATION_CHANNEL = 711707649829240972

    EVENT_EXCLUDED_MEMBERS = [582154877820600340]
    TRUSTED_ROLE = 716392797535469649
    VERIFIED_ROLE = 919753805174812723
    WELCOMER_ROLE = 729743673746522242
    PARTNER_MANAGER_ROLE = 1005612186875473952
    NEW_ROLE = 1007969193125228654
    NEED_HELP_ROLE = 712372007399849985

class TestServer:
    ID = 843442230547054602
    
    APPLICATION_CHANNEL = 1004483813155537007
    FEEDBACK_CHANNEL = 1004483858168815616
    UNTRUSTED_CHANNEL = 1004484224113459291
    SOS_CHANNEL = 1004885079308370000
    GENERAL_CHANNEL = 843442230547054605
    POTATO_BONUS_CHANNEL = 1005608636913045504
    WELCOME_CHANNEL = 1007977199153987686
    EVENT_DROP_CHANNELS = [843442230547054605]
    EVENT_EXCLUDED_CHANNELS = []
    UPDATE_CHANNEL = 843442230547054605
    INFORMATION_CHANNEL = 1008840542580379792

    EVENT_EXCLUDED_MEMBERS = [582154877820600340]
    TRUSTED_ROLE = 1004481875085115573
    VERIFIED_ROLE = 1004481949806645359
    WELCOMER_ROLE = 1004481824438882437
    PARTNER_MANAGER_ROLE = 1005612348041609216
    NEW_ROLE = 1007975948639027262
    NEED_HELP_ROLE = 1008443945308655716

class ServerInfo:
    KITD = KITDServer
    TEST = TestServer


GUILD_OBJECT = discord.Object(id=(ServerInfo.TEST.ID if is_dev() else ServerInfo.KITD.ID))

class Sexualities(Enum):
    straight = "804873516713377853"
    gay = "804861827111583802"
    questioning = "804873281634041916"
    asexual = "945774098120835113"
    bisexual = "804861743695134741"
    aromantic = "1004861489544450059"
    pansexual = "804861899090821162"
    omnisexual = "1004861344488628254"
    demisexual = "804861931901943808"


class OtherRoles(Enum):
    events = "743963214127300749"
    updates = "1004871752037453866"
    programmer = "733339593486893176"
    discussion = "727584396986810408"



QUESTIONS = [
    {
        "question": "Have you read the welcome message and rules?",
        "required": True,
        "max_length": 100,
        "placeholder": "Yes/No"
    },
    {
        "question": "Where did you find the link to join?",
        "required": True,
        "max_length": 100,
        "placeholder": "Disboard/Google/Yt/Other..."
    },
    {
        "question": "How old are you?",
        "required": False,
        "max_length": 50,
        "placeholder": "13-21"
    },
    {
        "question": "What are your preferred pronouns?",
        "required": False,
        "max_length": 50,
        "placeholder": "He/Him/They/Them..."
    },
    {
        "question": "What is your sex?",
        "required": False,
        "max_length": 50,
        "placeholder": "male/female"
    },
    {
        "question": "Where are you from?",
        "required": True,
        "max_length": 200,
        "placeholder": "America/UK/Germany..."
    },
    {
        "question": "Are you suicidal or self harm?",
        "required": True,
        "max_length": 100,
        "placeholder": "Yes/No"
    },
    {
        "question": "Are you easily triggered?",
        "required": True,
        "max_length": 50,
        "placeholder": "Yes, I am by.../No"
    },
    {
        "question": "Why do you want access to the help channels?",
        "required": True,
        "max_length": 200,
        "placeholder": "I want to help/I want to get help/..."
    },
    {
        "question": "Do you suffer from any disorders?",
        "required": False,
        "max_length": 200,
        "placeholder": "Yes I suffer from.../No"
    },
    {
        "question": "Do you have experience helping others?",
        "required": True,
        "max_length": 100,
        "placeholder": "Yes/No"
    },
    {
        "question": "Tell us a bit about yourself.",
        "required": True,
        "max_length": 200,
        "min_length": 50,
        "placeholder": "I like cookies.",
        "style": discord.TextStyle.long
    }
]