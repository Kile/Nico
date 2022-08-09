import json
import discord

from enum import Enum
from pymongo import MongoClient

from bot.utils.functions import is_dev

with open("config.json", "r") as config_file:
    config = json.loads(config_file.read())

TOKEN = config["token"]

CLUSTER = MongoClient(config['mongo'])

DB = CLUSTER['Nico']

PARTNERS = DB['partners']

DISBOARD = 302050872383242240

WELCOME_MESSAGE = \
""" Welcome to Kids In The Dark {}!
I am Nico, KITD's own bot. If you're wondering where first to go, check out <#920102551116980226> for information about the server and some roles.
Wanna check what's new? Check out <#726803975680163920> for the latest updates.
You can grab some roles by using my `/role` command such as pronouns and sexuality roles.
Did you come here to vent? To make vent, advice and other sensitive channels a safe space, you have to apply (using `/apply`) before you can grab roles to access them.
I hope you have a great time here!
"""

class KITDServer:
    ID = 710871326557995079
    
    APPLICATION_CHANNEL = 730811764652113960
    FEEDBACK_CHANNEL = 737799496712323154
    UNTRUSTED_CHANNEL = 729078073135202396
    SOS_CHANNEL = 712384341442822184
    GENERAL_CHANNEL = 710873588646936576
    POTATO_BONUS_CHANNEL = 1005608836486406254

    TRUSTED_ROLE = 716392797535469649
    VERIFIED_ROLE = 919753805174812723
    WELCOMER_ROLE = 729743673746522242
    PARTNER_MANAGER_ROLE = 1005612186875473952

    SEXUALITY_ROLES = {

    }
    PRONOUN_ROLES = {

    }
    HELP_ROLES = {

    }

class TestServer:
    ID = 843442230547054602
    
    APPLICATION_CHANNEL = 1004483813155537007
    FEEDBACK_CHANNEL = 1004483858168815616
    UNTRUSTED_CHANNEL = 1004484224113459291
    SOS_CHANNEL = 1004885079308370000
    GENERAL_CHANNEL = 843442230547054605
    POTATO_BONUS_CHANNEL = 1005608636913045504

    TRUSTED_ROLE = 1004481875085115573
    VERIFIED_ROLE = 1004481949806645359
    WELCOMER_ROLE = 1004481824438882437
    PARTNER_MANAGER_ROLE = 1005612348041609216

    SEXUALITY_ROLES = {
        "straight": 1004482324815159346,
        "questioning": 1004482347292434484,
        "gay": 1004482379676651600
    }
    PRONOUN_ROLES = {
        "he/him": 1004482233769398312,
        "she/her": 1004482261460205610,
        "they/them": 1004482293726973982,
    }
    HELP_ROLES = {
        "1": 1004482494286016553,
        "2": 1004482549017497680
    }

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