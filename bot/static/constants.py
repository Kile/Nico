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
POTATO = DB["potato"]
MOTM = DB["motm"]

DISBOARD = 302050872383242240
KILE = 606162661184372736
KILLUA_SERVER = 715358111472418908
KILLUA_BOOSTER_ROLE = 769622564648648744

IMAGE_QUESTION_REGEX = r"(no|can'?t|cannot|how|why|give).*(send|upload|post).*(image|gif|attachment|pic(s|ture)?|img).*\??"

TAG_QUESTION_REGEX = r"(how|where|why|what|give?).+ (tag|vip)( |$|\?)"

TAG_INTERACTIONAL_REGEX = r"(^| )(tag|vip).+\?"

WHO_PINGED_ME_REGEX = r"(who|what|where|why|how).*(ping|pings|pinger|pinged).*\??"

TRANSLATE_EMOJI = "<:translate:1364363045438099466>"

DAILY_POTATOES = 3

MOTM_VOTE_LIMIT = 3

CREATE_ROLE_WITH_COLOUR = False # Wether users can create their custom roles with a custom colour or not

ACTIVITY_EVENT = CONSTANTS.find_one({"_id": "activity_event"})["active"]

TRIALS = CONSTANTS.find_one({"_id": "trials"})["active"] if CONSTANTS.find_one({"_id": "trials"}) else False

WELCOME_MESSAGE = \
""" Welcome to Nico's Safe Space **{}**!

Due to us getting tags, you can **ignore the rest of this message** until you have full access to the server through <#1362726898685317220>. YOU DO NOT NEED FULL ACCESS TO USE THE TAG. If you are just here for the tag, you already have it.

I am Nico and I am watching over this server. To ensure you are familiar with how this server works, please read through <#710941242963263638> and <#711707649829240972>. Afterwards hop into my dms and use the slash command `/join` to answer a few questions about what is explained in those channels to ensure you have read them.

Your answers will be automatically checked, so make sure you write short answers as long ones might not be included in our possible answer list.

Please also make sure to open your dms to Nico before running the `/join` command, else he will not be able to respond.

New to discord? Not sure what to do? Something isn't working? Need help?
Check out these youtube videos for a detailed showcase of how to fully join this server: 
[Mobile](https://youtu.be/5aIx2ETB3r4) 
[Desktop](https://youtu.be/57RNJyFa24k)
If you still have trouble feel free to dm a staff member at any point to ask for help.
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
    },
    {
        "question": "Are we mental health professionals?",
        "answer": ["no", "no you are not", "no you aren't"]
    },
    {
        "question": "What role do all staff members have?",
        "answer": ["staff", "staff role", "<@&738317128930689055>", "@staff"]
    },
    {
        "question": "What is our bot channel?",
        "answer": ["training-area", "training area", "#training-area", "#trainin area", "<#739525325267927082>", ":target:training-area", ":target:training area", ]
    }
]

class NSSServer:
    ID = 710871326557995079
    
    APPLICATION_CHANNEL = 730811764652113960
    FEEDBACK_CHANNEL = 737799496712323154
    UNTRUSTED_CHANNEL = 729078073135202396
    SOS_CHANNEL = 1019916074294194196
    GENERAL_CHANNEL = 710873588646936576
    POTATO_BONUS_CHANNEL = 1005608836486406254
    WELCOME_CHANNEL = 726053325623263293
    EVENT_DROP_CHANNELS = [710873588646936576, 712132952896831488, 712049873674960906, 729161403713191997, 714821065897148496, 739525325267927082, 712049825583202345, 712408301467598928, 712476683394875412, 753007572579254283, 765690813962518558]
    EVENT_EXCLUDED_CHANNELS = [739525325267927082, 714567214187020368, 739218822065815592, 1005619816775831602, 726170868924809216, 716453938966036490, 725058055275937882]
    UPDATE_CHANNEL = 726803975680163920
    INFORMATION_CHANNEL = 711707649829240972
    TRIAL_APS_CHANNEL = 1012672061296091156
    THREAD_HELP_CHANNELS = [1019655006766497882, 1019916074294194196, 1019651891589820487]
    MOTM_SUGGESTION_CHANNEL = 1058529621525659678
    MOD_CHANNEL = 714567214187020368
    BOOSTER_CHANNEL = 1010323093991985183

    MOTM = 1058526586955104348
    WELCOMER_ROLE = 1125067902802989156
    EVENT_EXCLUDED_MEMBERS = [582154877820600340]
    MEMBER_ROLE = 712376001782349896
    TRUSTED_ROLE = 716392797535469649
    VERIFIED_ROLE = 919753805174812723
    VERIFIER = 729743673746522242
    PARTNER_MANAGER_ROLE = 1005612186875473952
    NEW_ROLE = 1007969193125228654
    NEED_HELP_ROLE = 712372007399849985
    WILL_HELP_ROLE = 712375696642801854
    CHAT_REVIVE_ROLE = 1011764789128744970
    PREMIUM_ROLES = [717054751778275378, 1012105688140492912, 1019651891589820487]
    VOTED_ROLE = 738118004994342940
    AUCTIONABLE_ROLES = [1015369303257776140]
    AUCTION_PING = 1015370996464767058
    STAFF_ROLE = 738317128930689055
    SANCTIONED = 1246609965209092198
    VALENTINES_CHANNEL = 1074116947370840166
    LEVEL_ROLES = {
        813789401146327070: {"id": 1028767978516402296, "icon": "<:Apollo:1030894624979566612>"}, # Level 10: Apollo
        813789725722673154: {"id": 1028767931812823080, "icon": "<:Aphrodite:1030895869232427058>"}, # Level 15: Aphrodite
        813789854861230121: {"id": 1028767710680727592, "icon": "<:Artemis:1030894771872481412>"}, # Level 20: Artemis
        813790065654366228: {"id": 1028767667491971183, "icon": "<:Hermes:1030894892265779220>"}, # Level 50: Hermes
        1377335406185676830: {"id": 1028767616564744252, "icon": "<:Hera:1377996165060100096>"}, # Level 75: Cabin of Hera
        1377761921553535076: {"id": 1377356087149203476, "icon": "<:Hephaestus:1377996163801677834>"}, # Level 90: Cabin of Hephaestus
        997254017002512435: {"id": 1377762708237324359, "icon": "<:Poseidon:1377996166729306195>"}, # Level 100: Cabin of Poseidon
        712375696642801854: {"id": 1029665470179188746, "icon": "<:Soteria:1030894946883993755>"}, # will help role: Soteria
        756512273001873458: {"id": 1029665250380873728, "icon": "<:Plutus:1030894925828599859>"} # giveaway role: Plutus
    }
    JOINED_FOR_TAG_ROLE = 1362726731768922205
    TRIAL_MOD_ROLE = 919779739068166164
    KILLUA_BOOSTER_ROLE = 1365332662704668753

"""
Apollo level 10
Aphrodite level 15
Artemis level 20
Demeter level 25
Hermes level 50
Hera level 75
Hephaestus level 90
Poseidon level 100
"""

class TestServer:
    ID = 843442230547054602
    
    APPLICATION_CHANNEL = 1004483813155537007
    FEEDBACK_CHANNEL = 1004483858168815616
    UNTRUSTED_CHANNEL = 1004484224113459291
    SOS_CHANNEL = 1023315472176926791
    GENERAL_CHANNEL = 843442230547054605
    POTATO_BONUS_CHANNEL = 1005608636913045504
    WELCOME_CHANNEL = 1007977199153987686
    EVENT_DROP_CHANNELS = [843442230547054605]
    EVENT_EXCLUDED_CHANNELS = []
    UPDATE_CHANNEL = 843442230547054605
    INFORMATION_CHANNEL = 1008840542580379792
    TRIAL_APS_CHANNEL = 1004483813155537007
    THREAD_HELP_CHANNELS = [1023315472176926791]
    MOTM_SUGGESTION_CHANNEL = 1004483813155537007
    MOD_CHANNEL = 1027946252647809035
    BOOSTER_CHANNEL = 1005608636913045504

    MOTM = 1007975948639027262
    WELCOMER_ROLE = 1004481824438882437
    EVENT_EXCLUDED_MEMBERS = [582154877820600340]
    MEMBER_ROLE = 1004481875085115573
    TRUSTED_ROLE = 1004481875085115573
    VERIFIED_ROLE = 1004481949806645359
    VERIFIER = 1004481824438882437
    PARTNER_MANAGER_ROLE = 1005612348041609216
    NEW_ROLE = 1007975948639027262
    NEED_HELP_ROLE = 1008443945308655716
    WILL_HELP_ROLE = 1004481875085115573
    CHAT_REVIVE_ROLE = 1011766709172043906
    PREMIUM_ROLES = []
    VOTED_ROLE = 1012113772464316428
    AUCTIONABLE_ROLES = [1012113772464316428]
    AUCTION_PING = 1015370148615561348
    STAFF_ROLE = 1
    VALENTINES_CHANNEL = 1004483858168815616
    SANCTIONED = 1246606351036190832
    LEVEL_ROLES = {
        1027946396801843252: {"id": 1027946473398218752, "icon": "<:IronMan:1030896994891337838>"}, # Iron man
        1027946442431672412: {"id": 1027946539508846653, "icon": "<:DoctorStrange:1030897207953608826>"} # Dr Strange
    }
    JOINED_FOR_TAG_ROLE = 1015376452868378735
    TRIAL_MOD_ROLE = 1
    KILLUA_BOOSTER_ROLE = 1015376452868378735

class ServerInfo:
    NSS = NSSServer
    TEST = TestServer


GUILD_OBJECT = discord.Object(id=(ServerInfo.TEST.ID if is_dev() else ServerInfo.NSS.ID))

class Sexualities(Enum):
    straight = "804873516713377853"
    gay = "804861827111583802"
    questioning = "804873281634041916"
    asexual = "945774098120835113"
    bisexual = "804861743695134741"
    pansexual = "804861899090821162"
    omnisexual = "1004861344488628254"
    demisexual = "804861931901943808"

class Romantic(Enum):
    heteroromantic = "1011760051138072617"
    homoromantic = "1011760223981158420"
    aromantic = "1004861489544450059"
    biromantic = "1011760508262690847"
    panromantic = "1011760372627275858"
    omniromantic = "1011760649149358200"


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