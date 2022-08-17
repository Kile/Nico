import discord

from random import sample
from datetime import datetime, timedelta
from typing import Dict, Union, List

from bot.static.constants import EVENT

class Member:
    cache: Dict[int, "Member"] = {}
    REQUIRED_MESSAGES_A_DAY = 10

    @classmethod 
    def __get_cache(cls, user_id: int):
        """Returns a cached object"""
        return cls.cache[user_id] if user_id in cls.cache else None

    def __new__(cls, user_id: int):
        existing = cls.__get_cache(user_id)
        if existing:
            return existing
        return super().__new__(cls)

    def __init__(self, user_id: int):
        if user_id in self.cache:
            if self.cache[user_id].booster and datetime.now() - self.cache[user_id].booster["time"] > timedelta(hours=1):
                self.cache[user_id].booster = {}
                EVENT.update_one({"_id": self.cache[user_id].id}, {"$set": {"booster": self.cache[user_id].booster}})
            return 

        data = EVENT.find_one({"_id": user_id})

        if not data:
            EVENT.insert_one({"_id": user_id, "messages_a_day": {}, "last_messages": {}, "points": 0, "gamble_cooldown": None, "booster": {}, "karma_cooldown": None, "karma": 0, "karma_given_to": []})
            data = EVENT.find_one({"_id": user_id})

        self.id = user_id
        self.messages_a_day : Dict[str, int] = data["messages_a_day"]
        self.last_messages : Dict[int, datetime] = data["last_messages"]
        self.points : int = data["points"]
        self.karma : int = 0 
        self.karma_given_to : List[int] = data["karma_given_to"]
        self.gamble_cooldown : datetime = data["gamble_cooldown"]
        self.karma_cooldown : datetime = data["karma_cooldown"]

        if data["booster"] and datetime.now() - data["booster"]["time"] < timedelta(hours=1):
            self.booster : Dict[str, Union[datetime, int]]  = data["booster"]
        else:
            self.booster : Dict[str, Union[datetime, int]]  = {}
            EVENT.update_one({"_id": self.id}, {"$set": {"booster": self.booster}})

        self.cache[user_id] = self

    @property
    def karma_rank(self) -> int:
        """Returns the current position the user is at in the server in terms of karma"""
        all = [x["_id"] for x in self.top_karma(10000)] # Slightly hacky but I cannot access guild members from here
        return (all.index(self.id) + 1) if self.id in all else 0

    @property
    def points_rank(self) -> int:
        """Returns the current position the user is at in the server in terms of points"""
        all = [x["_id"] for x in self.top_members(10000)] # Slightly hacky but I cannot access guild members from here
        return (all.index(self.id) + 1) if self.id in all else 0

    @classmethod
    def clear_all(cls):
        """Removes all entries from the database"""
        EVENT.delete_many({})
        cls.cache = {}

    @classmethod
    def average_points(cls):
        """Returns the average amount of points members have collected"""
        return sum([m["points"] for m in EVENT.find()]) / EVENT.count_documents({})

    @classmethod
    def top_members(cls, amount: int = 3):
        """Returns the top amount of members"""
        return EVENT.find().sort("points", -1).limit(amount)

    @classmethod
    def top_karma(cls, amount: int = 3):
        """Returns the top amount of karma"""
        top_members = [m["_id"] for m in cls.top_members(amount)]
        return [m for m in EVENT.find().sort("karma", -1) if not  m["_id"] in top_members][:amount]

    @classmethod
    def participants(cls):
        """Returns the amount of participants"""
        return EVENT.count_documents({})

    @classmethod
    def random_winners(cls) -> List[int]:
        """Returns the id of one random member whos points are more than or equal to the average"""
        average = cls.average_points()
        top = [m["_id"] for m in cls.top_members(2)]
        karma_top = [m["_id"] for m in cls.top_karma(2)]

        return sample([member for member in EVENT.find() if (member["points"] >= average) and (not member["_id"] in top) and (not member["_id"] in karma_top)], k=3)

    @property
    def streak(self) -> int:
        """Returns an integer of the number of days in a row a message was sent"""
        count = 0

        for pos, (key, val) in enumerate(list(self.messages_a_day.items())[::-1]):
            if len(self.messages_a_day) == pos+1: # last element in list
                break

            time_diff = datetime.fromisoformat(key) - datetime.fromisoformat(list(self.messages_a_day)[::-1][pos + 1])

            if time_diff > timedelta(days=1) and time_diff < timedelta(days=2):
                if val > self.REQUIRED_MESSAGES_A_DAY:
                    count += 1 # Streak is going
                    continue

            break

        return count

    @property
    def diminishing_returns(self) -> float:
        """Calculates a number by which a users points are multiplied which decreases as they get more points"""
        return 1 if self.points == 0 else (self.points/10) ** (-1.46218 * (10 ** -9)) # This works out to 0.9 when user points are 30 000

    @property
    def can_gamble(self) -> bool:
        """Returns whether the user can gamble"""
        return True if not self.gamble_cooldown else datetime.now() - self.gamble_cooldown > timedelta(minutes=20)

    def better_booster_active(self, booster: int) -> Union[bool, int]:
        """Returns whether the user has a better booster active"""
        return self.booster["times"] if self.booster and self.booster["times"] <= booster else False

    def add_points(self, amount: int):
        """Adds points to the user"""
        self.points += amount
        EVENT.update_one({"_id": self.id}, {"$inc": {"points": amount}})

    def remove_coins(self, amount: int):
        """Removes coins from the user"""
        self.points -= amount
        EVENT.update_one({"_id": self.id}, {"$inc": {"points": -amount}})

    def refresh_cooldown(self):
        """Refreshes the gamble cooldown"""
        self.gamble_cooldown = datetime.now()
        EVENT.update_one({"_id": self.id}, {"$set": {"gamble_cooldown": self.gamble_cooldown}})

    def give_karma(self, user: int):
        """Resets the karma cooldown"""
        self.karma_cooldown = datetime.now()
        self.karma_given_to.append(user)
        EVENT.update_one({"_id": self.id}, {"$set": {"karma_cooldown": self.karma_cooldown, "karma_given_to": self.karma_given_to}})

    def add_booster(self, booster: int, karma=False):
        """Adds a booster to the user"""
        self.booster["times"] = booster
        self.booster["time"] = datetime.now()
        if karma:
            self.karma += 1
        EVENT.update_one({"_id": self.id}, {"$set": {"booster": self.booster, "karma": self.karma}})

    def add_message(self, message: discord.Message):
        """Records a message was sent by that user"""
        self.last_messages[str(message.channel.id)] = datetime.now()

        time_diff = (datetime.now() - datetime.fromisoformat(list(self.messages_a_day)[-1:][0])) if self.messages_a_day else timedelta(days=2)

        if time_diff > timedelta(days=1):
            self.messages_a_day[datetime.now().isoformat()] = 1
        else:
            self.messages_a_day[list(self.messages_a_day)[-1:][0]] += 1

        EVENT.update_one({"_id": self.id}, {"$set": {"last_messages": self.last_messages, "messages_a_day": self.messages_a_day}})