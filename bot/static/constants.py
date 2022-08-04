import json

from enum import Enum

with open("config.json", "r") as config_file:
    config = json.loads(config_file.read())

TOKEN = config["token"]

class KITDServer:
    ID = 710871326557995079
    
    APPLICATION_CHANNEL = 730811764652113960
    FEEDBACK_CHANNEL = 737799496712323154
    UNTRUSTED_CHANNEL = 1
    SOS_CHANNEL = 712384341442822184

    TRUSTED_ROLE = 716392797535469649
    VERIFIED_ROLE = 919753805174812723
    WELCOMER_ROLE = 729743673746522242
    UNTRUSTED_ROLE = 1

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

    TRUSTED_ROLE = 1004481875085115573
    VERIFIED_ROLE = 1004481949806645359
    WELCOMER_ROLE = 1004481824438882437
    UNTRUSTED_ROLE = 1004482401910669414

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
        "placeholder": "I like cookies."
    }
]