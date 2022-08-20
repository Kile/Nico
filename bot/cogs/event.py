import discord

from discord.ext import commands

from datetime import timedelta, datetime
from random import randint
from typing import Literal

from bot.static.constants import GUILD_OBJECT, EVENT_EXPLANATION, CONSTANTS
from bot.utils.classes import Member
from bot.utils.interactions import View, Button

class Event(commands.Cog):

    def __init__(self, client: commands.Bot):
        self.client = client
        self.prices = {
            2: 5000,
            3: 10000,
            4: 15000
        }
        self.english = { # Why is the English language like this
            1: "st",
            2: "nd",
            3: "rd",
            4: "th",
            5: "th",
        }

        self.emotes = {
            1: ":crown: ",
            2: ":second_place: ",
            3: ":third_place: ",
        }

    @property
    def guild(self) -> discord.Guild:
        return self.client.get_guild(self.client.server_info.ID)

    async def cog_load(self):
        print("Loaded event cog")

    event = discord.app_commands.Group(name="event", description="Commands relating to the ongoing activity event", guild_ids=[GUILD_OBJECT.id])

    @event.command()
    async def stats(self, interaction: discord.Interaction):
        """Gives you the stats for the ongoing activity event"""
        participants = Member.participants()
        average = Member.average_points()

        embed = discord.Embed.from_dict({
            "title": "Activity Event Stats",
            "description": "The current stats for the ongoing activity event are as follows:",
            "color": 0x2f3136,
            "fields": [
                {
                    "name": "Total Participants",
                    "value": "**{}**".format(participants),
                    "inline": False
                },
                {
                    "name": "Average Points",
                    "value": "**{}**".format(average),
                    "inline": False
                }
            ]
        })

        await interaction.response.send_message(embed=embed)

    @event.command()
    async def leaderboard(self, interaction: discord.Interaction):
        """Gives you the top 5 members in terms of points of the ongoing activity event"""
        top_members = Member.top_members(5)

        embed = discord.Embed.from_dict({
            "title": "Activity Event Leaderboard",
            "description": "The current leaderboard for the ongoing activity event is as follows:",
            "color": 0x2f3136,
            "fields": [
                {
                    "name": f"{self.emotes[pos+1] if pos+1 in self.emotes else ''}{pos+1}{self.english[pos+1]} Place",
                    "value": f"**{self.guild.get_member(member['_id'])}** with **{member['points']}** points",
                    "inline": False
                } for pos, member in enumerate(top_members)
            ]
        })

        await interaction.response.send_message(embed=embed)

    @event.command()
    @discord.app_commands.describe(member="The member to get infos about")
    async def member(self, interaction: discord.Interaction, member: discord.Member = None):
        """Gives information about a member like their points"""
        if member is None: member = interaction.user

        if member.bot:
            return await interaction.response.send_message("Bots don't have points. However they do have feelings. When was the last time you hugged a bot?", ephemeral=True)

        if member.id in self.client.server_info.EVENT_EXCLUDED_MEMBERS:
            return await interaction.response.send_message("This member is nor participating in the event!", ephemeral=True)

        member_info = Member(member.id)

        points_rank = ("#" + str(member_info.points_rank)) if member_info.points_rank else "Not ranket yet"
        karma_rank = ("#" + str(member_info.karma_rank)) if member_info.karma_rank else "Not ranket yet"

        embed = discord.Embed.from_dict({
            "title": f"{member.name}'s Stats",
            "fields": [
                {
                    "name": "Points",
                    "value": f"**{round(member_info.points, 2)}**",
                    "inline": False
                },
                {
                    "name": "Diminishing returns",
                    "value": "**{}**%".format(round(100*member_info.diminishing_returns)),
                },
                {
                    "name": "Last message sent",
                    "value": "<t:{}:R>".format(int(member_info.last_message_at.timestamp())) if member_info.last_message_at else "Never",
                },
                {
                    "name": "Day of messaging streak :fire:",
                    "value": "**{}**".format(member_info.streak+1),
                },
                {
                    "name": "Current booster",
                    "value": ("`x" + str(member_info.booster["times"]) + "` ending <t:" + str(int((member_info.booster["time"]+timedelta(hours=1)).timestamp())) + ":R>") if member_info.booster else "None",
                },
                {
                    "name": "Karma recieved",
                    "value": "**{}**".format(member_info.karma),
                },
                {
                    "name": "Karma given",
                    "value": "**{}**".format(len(member_info.karma_given_to)),
                },
                {
                    "name": "Ranks",
                    "value": "**Points**: {}\n**Karma**: {}".format(points_rank, karma_rank),
                }
            ],
            "color": 0x2f3136,
            "thumbnail": {"url": (member.guild_avatar or member.avatar).url}
        })

        await interaction.response.send_message(embed=embed)

    @event.command()
    @discord.app_commands.describe(points="How many points to gamble")
    async def gamble(self, interaction: discord.Interaction, points: int):
        """Gamble for points with this command! 50% Chance of winning, 20 minute cooldown."""
        member = Member(interaction.user.id)

        if points < 1:
            return await interaction.response.send_message("You can't gamble less than 1 point!", ephemeral=True)

        if points > int(member.points*0.05):
            return await interaction.response.send_message(f"You can't gamble more than 5% of your points! ({int(member.points*0.05)} points)", ephemeral=True)

        if member.points < points:
            return await interaction.response.send_message("You don't have enough points to gamble that much!")

        if not member.can_gamble:
            return await interaction.response.send_message("Gambling is a serious addiction, you can only gamble once every 20 minutes. You can gamble again <t:{}:R>".format(int((member.gamble_cooldown+timedelta(minutes=20)).timestamp())))

        if randint(1, 2) == 1:
            member.add_points(points)
            return await interaction.response.send_message(f"You won! :tada: That is {points} added to your balance")
        else:
            await interaction.response.send_message(f"You lost! :sob: Say goobye to your {points} points")

        member.refresh_cooldown()

    @event.command()
    @discord.app_commands.describe(member="The member to give the boost to")
    async def karma(self, interaction: discord.Interaction, member: discord.Member):
        """Once every 24 hours you can give someone a x1.5 point boost"""
        if member.id == interaction.user.id:
            return await interaction.response.send_message("You can't give yourself a boost!", ephemeral=True)

        if member.bot:
            return await interaction.response.send_message("You can't give a bot a boost!", ephemeral=True)

        if member.id in self.client.server_info.EVENT_EXCLUDED_MEMBERS:
            return await interaction.response.send_message("This member is nor participating in the event!", ephemeral=True)

        member_info = Member(interaction.user.id)
        other = Member(member.id)

        if member_info.karma_cooldown and datetime.now() - member_info.karma_cooldown < timedelta(days=1):
            return await interaction.response.send_message(f"You can't give someone a boost yet! You can give someone a boost every 24 hours. You can do it the next time <t:{int((member_info.karma_cooldown+timedelta(days=1)).timestamp())}:R>", ephemeral=True)

        if other.karma_given_to and interaction.user.id == other.karma_given_to[-1]:
            return await interaction.response.send_message("You can't give someone karma who has last given you karma as karma trading or karma to thank for karma is not allowed!", ephemeral=True)

        if other.better_booster_active(1.5):
            return await interaction.response.send_message(f"{member.name} already has a better boost active! You have to wait until their boost runs out <t:{int((other.booster['time']+timedelta(hours=1)).timestamp())}:R>", ephemeral=True)

        member_info.give_karma(other.id)
        other.add_booster(1.5, karma=True)
        await interaction.response.send_message(f"{member.mention} has been given a `x1.5` points booster for the next hour")

    @event.command()
    @discord.app_commands.describe(booster="The booster to buy")
    async def buy(self, interaction: discord.Interaction, booster: Literal[2, 3, 4]):
        """Buy a temporary points booster with this command"""
        member = Member(interaction.user.id)

        if member.better_booster_active(booster):
            view = View(member.id)
            continue_button = Button(label="Continue anyways", lable=discord.ButtonStyle.green, custom_id="continue")
            cancel_button = Button(label="Cancel", lable=discord.ButtonStyle.red, custom_id="cancel")

            view.add_item(continue_button)
            view.add_item(cancel_button)

            await interaction.response.send_message(f"You currently have a better (`x{member.booster['times']}`) booster active! It will end <t:{int((member.booster['time'] + timedelta(hours=1)).timestamp())}:R>. Do you want to continue anyways?", view=view)

            await view.wait()

            if view.timed_out:
                return await view.disable(await view.interaction.original_message())

            if view.value == "cancel":
                await view.interaction.response.send_message("Successfully cancelled")
                return await view.disable(await view.interaction.original_message())

            await view.disable(respond=False)
    
            interaction = view.interaction

        if self.prices[booster] > member.points:
            return await interaction.response.send_message(f"You don't have enough points to buy that booster! The booster costs {self.prices[booster]} points and you have only {member.points}", ephemeral=True)

        member.remove_coins(self.prices[booster])
        member.add_booster(booster)

        await interaction.response.send_message(f"Success! Bought `x{booster}` points booster for {self.prices[booster]} points. It is active for the next hour!")

    @event.command()
    async def shop(self, interaction: discord.Interaction):
        """See what items are for sale in the shop"""

        embed = discord.Embed.from_dict({
            "title": "Shop",
            "fields": [{"name": f"x{k} 1h booster", "value": f"Cost: {v} points"} for k, v in self.prices.items()],
            "color": 0x2f3136
        })

        await interaction.response.send_message(embed=embed)

    @event.command()
    async def info(self, interaction: discord.Interaction):
        """Gives you some info about the event"""
            
        embed = discord.Embed.from_dict({
            "title": "Information on how points are calculated",
            "description": EVENT_EXPLANATION,
            "color": 0x2f3136,
            "thumbnail": {"url": self.client.user.avatar.url}
        })
    
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @event.command()
    async def end(self, interaction: discord.Interaction):
        """Ends the event"""
        if not self.guild.owner_id == interaction.user.id:
            return await interaction.response.send_message("You can't end the event!", ephemeral=True)

        top_members = Member.top_members(3)
        most_karma_recieved = Member.top_karma(3)
        try:
            random_winners = Member.random_winners()
        except IndexError:
            return await interaction.response.send_message("Could not determine a random winner!", ephemeral=True)

        await interaction.response.defer()

        embed = discord.Embed.from_dict({
            "title": "Activity event ended!",
            "fields": [
                {"name": "Top 3 members with points", "value": "\n".join(f"{self.emotes[p+1]}{p+1}{self.english[p+1]} <@{m['_id']}> - **{int(m['points'])}** points" for p, m in enumerate(top_members))},
                {"name": "Top 3 members with karma", "value": "\n".join(f"{self.emotes[p+1]}{p+1}{self.english[p+1]} <@{m['_id']}> - **{int(m['karma'])}** karma" for p, m in enumerate(most_karma_recieved))},
                {"name": "Random winners", "value": "\n".join([f"<@{m['_id']}> - **{int(m['points'])}** p \| **{int(m['karma'])}** k" for m in random_winners])},
            ],
            "color": 0x2f3136,
            "thumbnail": {"url": self.client.user.avatar.url},
            "footer": {"text": "Thank you for participating!"}
        })

        # Member.clear_all() Not deleting the data just in case something goes wrong
        CONSTANTS.update_one({"_id": "event"}, {"$set": {"active": False}})

        await self.client.remove_cog("Event")
        await self.client.tree.sync(guild=GUILD_OBJECT)

        await interaction.followup.send(embed=embed)
        message = await interaction.original_message()
        await message.add_reaction("\U0001f389") # 🎉

Cog = Event