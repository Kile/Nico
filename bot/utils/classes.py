import discord

from random import sample
from enum import Enum, auto
from datetime import datetime, timedelta
from typing import Dict, Union, List, Tuple

from bot.static.constants import EVENT, POTATO, CONSTANTS

class HelloAgain:
    cache: "HelloAgain" = None

    def __new__(cls):
        if cls.cache:
            return cls.cache
        return super().__new__(cls)

    def __init__(self):
        if self.cache:
            return 
        
        self.list: Dict[int, Dict[str, Union[int, datetime]]] = CONSTANTS.find_one({"_id": "hello_again"})["list"]

        self.cache = self

    def add_user(self, user_id: int):
        """Adds a user to the list"""
        if user_id in self.list:
            return 
        self.list[str(user_id)] = {"time": datetime.now(), "count": 0}
        CONSTANTS.update_one({"_id": "hello_again"}, {"$set": {"list": self.list}})

    def remove_user(self, user_id: int):
        """Removes a user from the list"""
        if user_id not in self.list:
            return 
        del self.list[str(user_id)]
        CONSTANTS.update_one({"_id": "hello_again"}, {"$set": {"list": self.list}})

    def add_message(self, user_id: int):
        """Adds a message to the user's count"""
        if user_id not in self.list:
            return 
        self.list[str(user_id)]["count"] += 1
        if self.list[str(user_id)]["count"] >= 10:
            del self.list[str(user_id)]
        CONSTANTS.update_one({"_id": "hello_again"}, {"$set": {"list": self.list}})

    def needs_hello_again(self) -> List[int]:
        """Returns a list of user ids that need to be greeted again because the time is more than a week ago"""
        users = [user_id for user_id, val in self.list.items() if datetime.now() - val["time"] > timedelta(days=7)]
        for user in users:
            del self.list[str(user)]
        CONSTANTS.update_one({"_id": "hello_again"}, {"$set": {"list": self.list}})
        return [int(u) for u in users]

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
        self.karma : int = data["karma"]
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
        all = [x["_id"] for x in self.top_karma(10000, mirror_number=False)] # Slightly hacky but I cannot access guild members from here
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
    def top_karma(cls, amount: int = 3, mirror_number: bool = True):
        """Returns the top amount of karma"""
        top_members = [m["_id"] for m in cls.top_members(amount if mirror_number else 3)]
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
            
            if time_diff > timedelta(days=1) and time_diff < timedelta(days=2) and list(self.messages_a_day.values())[::-1][pos + 1] > self.REQUIRED_MESSAGES_A_DAY:
                if val > self.REQUIRED_MESSAGES_A_DAY:
                    count += 1 # Streak is going
                    continue
                # Streak is still going, but not enough messages were sent yet to increase it
            else:
                break

        return count

    @property
    def diminishing_returns(self) -> float:
        """Calculates a number by which a users points are multiplied which decreases as they get more points"""
        C = -1.46218 * (10 ** -9)
        return 1 if self.points == 0 else (self.points/10)**(C*((self.points/10)**2)) # This works out to 0.9 when user points are 30 000

    @property
    def can_gamble(self) -> bool:
        """Returns whether the user can gamble"""
        return True if not self.gamble_cooldown else datetime.now() - self.gamble_cooldown > timedelta(minutes=20)

    @property
    def last_message_at(self) -> Union[datetime, None]:
        """Returns the time of the last message the user sent"""
        return self.last_messages[max(self.last_messages.keys())] if self.last_messages else None

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

class PerkType(Enum):
    CUSTOM_ROLE = {"name": "Custom Role", "description": "Gives you a custom role you can design yourself", "item": "custom_role"}
    CUSTOM_EMOTE = {"name": "Custom Emote", "description": "Allowes you to design and add a custom emote", "item": "emote"}
    CUSTOM_STICKER = {"name": "Custom Sticker", "description": "Allows you to design and add a custom sticker", "item": "sticker"}
    ROLE = {"name": "Role", "description": "Gives you a role", "item": "role"}

    OTHER = {"name": "Other"}
    NOT_SPECIFIED = auto()

class PotatoMember:
    cache: Dict[int, "Member"] = {}
    potato: Union[discord.Message, None] = None

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
            return 

        data = POTATO.find_one({"_id": user_id})

        if not data:
            POTATO.insert_one({"_id": user_id, "potatoes": 0, "cooldowns": {}, "items": {}})
            data = POTATO.find_one({"_id": user_id})

        self.id = user_id
        self.potatoes: int = data["potatoes"]
        self.cooldowns: Dict[str, datetime] = data["cooldowns"]
        self.items: Dict[str, int] = data["items"] if "items" in data else {}

    @classmethod
    def get_top_members(cls, amount: int = 10) -> List["Member"]:
        """Returns the top members"""
        return [PotatoMember(m["_id"]) for m in POTATO.find().sort("potatoes", -1).limit(amount)]

    def add_potatoes(self, amount: int) -> None:
        """Adds potatoes to the user"""
        self.potatoes += amount
        POTATO.update_one({"_id": self.id}, {"$inc": {"potatoes": amount}})

    def remove_potatoes(self, amount: int) -> None:
        """Removes potatoes from the user"""
        self.potatoes -= amount
        POTATO.update_one({"_id": self.id}, {"$inc": {"potatoes": -amount}})

    def set_potatoes(self, amount: int) -> None:
        """Sets the amount of potatoes the user has"""
        self.potatoes = amount
        POTATO.update_one({"_id": self.id}, {"$set": {"potatoes": amount}})

    def add_cooldown(self, name: str) -> None:
        """Adds a cooldown to the user"""
        self.cooldowns[name] = datetime.now()
        POTATO.update_one({"_id": self.id}, {"$set": {"cooldowns": self.cooldowns}})
    
    def has_valid_cooldown(self, name: str, **kwargs) -> bool:
        """Returns whether the user has a cooldown"""
        return name in self.cooldowns and datetime.now() - self.cooldowns[name] < timedelta(**kwargs)

    def add_item(self, type: PerkType, amount: int = 1) -> None:
        """Adds an item to the user"""
        if type == PerkType.OTHER or type == PerkType.NOT_SPECIFIED:
            raise ValueError("Cannot add an item of type OTHER or NOT_SPECIFIED")

        self.items[type.value['item']] = amount
        POTATO.update_one({"_id": self.id}, {"$set": {"items": self.items}})

    def has_item(self, type: PerkType, amount: int = 1) -> bool:
        """Returns whether the user has an item the specified amount of times"""
        if type == PerkType.OTHER or type == PerkType.NOT_SPECIFIED:
            raise ValueError("Cannot check an item of type OTHER or NOT_SPECIFIED")
        
        return type.value['item'] in self.items and self.items[type.value['item']] >= amount

    def remove_item(self, item: PerkType, amount: int = 1) -> None:
        """Removes an item from the user"""
        if item.value["item"] not in self.items:
            raise ValueError("User does not have this item")

        self.items[item.value["item"]] -= amount
        if self.items[item.value["item"]] == 0:
            del self.items[item.value["item"]]

        POTATO.update_one({"_id": self.id}, {"$set": {"items": self.items}})

class AuctionItem:
    """Represents an item in an auction"""
    def __init__(self, auction = None, index: int = None, **kwargs):
        self.auction = auction
        self._index = index
        
        self.id = kwargs.get("id")
        # Setting self.id to the first id to the lowest possible number not yet in auction.items
        if self.id is None and auction and auction.items:
            self.id = min([i for i in range(max([item.id for item in auction.items])+2) if i not in [item.id for item in auction.items]])
        elif self.id is None:
            self.id = 0

        self.name: str = kwargs.get("name")
        self.description: str = kwargs.get("description")
        self.image: str = kwargs.get("image")
        self.type: PerkType = getattr(PerkType, kwargs.get("type") or "NOT_SPECIFIED") if isinstance(kwargs.get("type"), str) else (kwargs.get("type") or PerkType.NOT_SPECIFIED)
        self.colour: int = kwargs.get("colour") or 0x2f3136
        self.amount: int = kwargs.get("amount") or 1
        self.bidders: Dict[int, Dict[str, int]] = kwargs.get("bidders", {})
        self.listing_price: bool = kwargs.get("listing_price") or 1
        self.current_price: bool = kwargs.get("current_price") or self.listing_price
        self.featured: bool = kwargs.get("featured") or False
        self.listed_by: int = kwargs.get("listed_by")
        self.ending_at: datetime = kwargs.get("ending_at") or datetime.now() + timedelta(minutes=1)

        if self.type == PerkType.ROLE:
            self.role_id: int = kwargs.get("role_id")

    @classmethod
    def raw_kwargs(cls) -> dict:
        """Returns a dictionary of editable kwargs with default values"""
        return {
            "name": None,
            "description": None,
            "image": None,
            "type": None,
            "amount": 1,
            "listing_price": None,
            "featured": False,
            "ending_at": None,
            "role_id": None,
            "colour": None,
            "amount": 1
        }

    @property
    def includes_discord_perks(self) -> bool:
        """Returns whether the item includes discord perks"""
        return self.type in (PerkType.CUSTOM_ROLE, PerkType.CUSTOM_EMOTE, PerkType.CUSTOM_STICKER, PerkType.ROLE)

    @property
    def should_end(self) -> bool:
        """Returns whether the item should end"""
        return self.ending_at < datetime.now()

    def to_embed(self, guild: discord.Guild, dynamic_info: bool = True) -> discord.Embed:
        """Returns the item as an embed"""
        embed = discord.Embed(title=self.name or "Not named", description=(self.description or "No description"), color=self.colour)
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/843442230547054605/1014678566732038235/3460-verified.png" if self.featured else None)
        embed.set_image(url=self.image)
        embed.add_field(name="Listing Price", value=f"{self.listing_price} potatoes")
        embed.add_field(name="Ending", value="<t:" + str(int(self.ending_at.timestamp())) + ":R>")
        embed.add_field(name="Is discord perk", value=((f"Yes:\n{self.type.value['item']}" + (f"\n<@&{self.role_id}>" if self.type == PerkType.ROLE else "")) if self.includes_discord_perks else "No") if self.type != PerkType.NOT_SPECIFIED else "Not specified")
        embed.add_field(name="Amount", value=f"{self.amount}")
        embed.add_field(name="Listed by", value=guild.get_member(self.listed_by).mention if guild.get_member(self.listed_by) else "Unknown")
        embed.add_field(name="Item ID", value=f"{self.id}" if not self.id is None else "Not yet listed")

        if dynamic_info: # We do not want this posted when the auction is created as it is not relevant
            embed.add_field(name="Current Price", value=f"{self.current_price} potatoes")
            embed.add_field(name="Highest bidder", value=guild.get_member(self._find_first_valid_bidder()) if self._find_first_valid_bidder() else "None yet")
            embed.add_field(name="Bidders", value=f"{len(self.bidders)}")
        return embed

    def to_dict(self) -> dict:
        """Returns the item as a dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "image": self.image,
            "type": self.type.name,
            "colour": self.colour,
            "amount": self.amount,
            "bidders": self.bidders,
            "listing_price": self.listing_price,
            "current_price": self.current_price,
            "featured": self.featured,
            "listed_by": self.listed_by,
            "ending_at": self.ending_at,
            "role_id": self.role_id if hasattr(self, "role_id") else None
        }

    def _real_bids(self) -> List[Tuple[int, int]]:
        """Returns a list with the real bids"""
        result = []

        def sort(item: dict) -> int:
            if "max_bid" in item and not item["max_bid"] is None:
                return item["max_bid"]

            else:
                return item["bid"]

        sorted_bidders = sorted(self.bidders, key=lambda x: sort(self.bidders[x]), reverse=True)

        maximum_bids = [self.bidders[v]["max_bid"] if "max_bid" in self.bidders[v] and self.bidders[v]["max_bid"] else self.bidders[v]["bid"] for v in sorted_bidders]

        for position, bidder in enumerate(sorted_bidders):
            if position == len(sorted_bidders) - 1:
                result.append((int(bidder), sort(self.bidders[bidder])))
            else:
                second_highest = max(filter(lambda x: x not in maximum_bids[:position+1], maximum_bids)) + 1
                result.append((int(bidder), second_highest))

        return result

    def _find_first_valid_bidder(self) -> Union[int, None]:
        """Goes through all bids in descending order until finding a bidder that actually has the potatoes they bid"""
        # First we put all the bidders in a list and the lowest amount they could pay if they were on top to bid more than the person with less

        for bidder, amount in self._real_bids():
            if PotatoMember(bidder).potatoes >= amount:
                return bidder
        return None

    def _find_first_valid_bid(self) -> Union[int, None]:
        """Looks through the bids and returns the first valid bid"""
        valid_bidder = self._find_first_valid_bidder()
        real_bids = self._real_bids()

        for pos, (bidder, amount) in enumerate(real_bids):
            if bidder == valid_bidder:
                if len(real_bids) == pos + 1:
                    return self.bidders[str(bidder)]["bid"]
                else:
                    next_amount = real_bids[pos + 1][1]
                    data = self.bidders[str(bidder)]

                    if data["max_bid"] and next_amount > data["bid"]: # In this case a max bid from the one below was higher than the bid here, so the lowest max bid is taken
                        return amount
                    elif next_amount < data["bid"]: # The first bid is enough to outbid the second
                        return data["bid"]
                    else:
                        raise ValueError("User has not bid more than the one below")
        return None

    def sell(self, guild: discord.Guild) -> Tuple[discord.Member, int]:
        """Sells the item to the highest bidder at that time and returns who it was and the winning bid"""
        highest_bidder = self._find_first_valid_bidder()
        winning_bid = self._find_first_valid_bid()
        highest_bidder = guild.get_member(highest_bidder)

        # Removing the price the bidder paid for it
        potato_bidder = PotatoMember(highest_bidder.id)
        potato_bidder.remove_potatoes(winning_bid)

        # Adding that money to the seller
        potato_seller = PotatoMember(self.listed_by)
        potato_seller.add_potatoes(winning_bid)

        if self.includes_discord_perks:
            if self.type == PerkType.ROLE:
                role = guild.get_role(self.role_id)
                seller = guild.get_member(self.listed_by)
                # Swaps out the role
                seller.remove_roles(role)
                highest_bidder.add_roles(role)

            potato_bidder.add_item(self.type, amount=self.amount)

        # Remove the item from the auction
        self.auction.remove_item(self)

        return highest_bidder, winning_bid

    def bid(self, bidder: discord.Member, bid: int, maximum_bid: int = None) -> bool:
        """Places a bid on the item and returns wether or not the bidder now has the highest bid"""

        self.bidders[str(bidder.id)] = {"max_bid": maximum_bid, "bid": bid} # Even though the bid might be lower than the maximum bid, we still want to keep the data
        # If there is a higher maximum bid from someone else than the supplied bid, the highest maximum bid wins
        real_bids = self._real_bids()
        highest_bidder, current_highest_bid = real_bids[0]

        if highest_bidder == bidder.id and (len(real_bids) > 1 and bid > real_bids[1][1]) or (len(real_bids) == 1 and bid > self.listing_price):
            self.current_price = bid # If the standart bid succeeds we want the new price to be the bid
        else:
            self.current_price = current_highest_bid

        return highest_bidder == bidder.id

    def sync(self) -> None:
        """Syncs the item with the database"""
        self.auction.items[self._index] = self
        CONSTANTS.update_one({"_id": "auction"}, {"$set": {"items": [i.to_dict() for i in self.auction.items]}})

class Auction:

    def __init__(self) -> None:
        
        data = CONSTANTS.find_one({"_id": "auction"})

        self.raw_items = data["items"] if "items" in data else [] # Set the raw data first so it can be accessed from inside the AuctionItem constructor
        self.items = [AuctionItem(auction=self,index=p, **i) for p, i in enumerate(self.raw_items)]

    @property
    def sorted_items(self) -> List[AuctionItem]:
        """Returns the items sorted by current price and by wether they are featured or not, always preferring featured ones"""
        featured = [i for i in self.items if i.featured]
        featured.extend(sorted([i for i in self.items if not i.featured], key=lambda x: x.current_price, reverse=True))
        return featured

    def item_where_id(self, id: int) -> AuctionItem:
        """Returns the item with the supplied id"""
        return next(filter(lambda i: i.id == id, self.items), None)

    def remove_item(self, item: AuctionItem) -> None:
        """Removes an item from the auction"""
        self.items.pop(item._index)
        CONSTANTS.update_one({"_id": "auction"}, {"$set": {"items": [i.to_dict() for i in self.items]}})

    def add_item(self, item: AuctionItem) -> None:
        """Adds an item to the auction"""
        self.items.append(item)
        CONSTANTS.update_one({"_id": "auction"}, {"$set": {"items": [i.to_dict() for i in self.items]}})