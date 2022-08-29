import discord

from discord.ext import commands

from random import randint
from typing import Literal, List
from datetime import timedelta

from bot.utils.classes import PotatoMember as Member
from bot.static.constants import GUILD_OBJECT

class Potato(commands.Cog):

    def __init__(self, client: commands.Bot):
        self.client = client

    potato = discord.app_commands.Group(name="potato", description="Potato commands", guild_ids=[GUILD_OBJECT.id])

    @potato.command()
    @discord.app_commands.describe(other="The member to inspect the potatoes of")
    async def inspect(self, interaction: discord.Interaction, other: discord.Member = None):
        """Inspect a member's potato balance"""
        if not other: other = interaction.user

        member = Member(other.id)

        if member.potatoes == 0:
            return await interaction.response.send_message("This member has no potatoes.")

        embed = discord.Embed.from_dict({
            "title": f":potato: potato count :potato:",
            "description": f"{other}'s has {member.potatoes} potatoes\n" + ((":potato:" * member.potatoes) if member.potatoes < 50 else (":potato:" * 50)),
            "color": 0x2f3136,
            "thumbnail": {"url": other.display_avatar.url if other.display_avatar else None}
        })

        await interaction.response.send_message(embed=embed)

    @potato.command()
    @discord.app_commands.describe(amount="The amount of potatoes to gamble")
    async def gamble(self, interaction: discord.Interaction, amount: discord.app_commands.Range[int, 1, 20]):
        """Gamble your potatoes"""
        member = Member(interaction.user.id)

        if member.has_valid_cooldown("gamble", minutes=10):
            return await interaction.response.send_message(":no_entry_sign: Gambling addiction is a serious problem. Regulations require a wait.")

        if amount > member.potatoes:
            return await interaction.response.send_message(f"You don't have enough potatoes to gamble {amount}")
        elif amount < 1:
            return await interaction.response.send_message(f"You can't gamble less than 1 potato")

        if randint(0, 100) < 50:
            member.add_potatoes(amount)
            embed = discord.Embed.from_dict({
                "title": ":game_die: :potato: :game_die:",
                "description": f"Your gambling paid off, you won {amount} potato{'es' if amount > 1 else ''} giving you a total of {member.potatoes} potatoes\n" + ((":potato:" * member.potatoes) if member.potatoes < 50 else (":potato:" * 50)),
                "color": 0x2f3136,
            })
        else:
            member.remove_potatoes(amount)
            embed = discord.Embed.from_dict({
                "title": ":game_die: :potato: :game_die:",
                "description": f"Your gambling sucked, you lost {amount} potato{'es' if amount > 1 else ''} leaving you with a total of {member.potatoes} potatoes\n" + ((":potato:" * member.potatoes) if member.potatoes < 50 else (":potato:" * 50)),
                "color": 0x2f3136,
            })
        
        member.add_cooldown("gamble")
        await interaction.response.send_message(embed=embed)

    @potato.command()
    @discord.app_commands.describe(other="The person to steal from", amount="The amount of potatoes to steal")
    async def steal(self, interaction: discord.Interaction, other: discord.Member, amount: discord.app_commands.Range[int, 1, 20]):
        """Steal potatoes from another member"""

        member = Member(interaction.user.id)
        other_member = Member(other.id)

        if member.has_valid_cooldown("steal", minutes=20):
            return await interaction.response.send_message(f":police_officer: Your potato thief actions are being currently scrutinized. Lay low for a while.!")

        if member.potatoes < amount:
            return await interaction.response.send_message(f"You need to have at least as many potatoes as you are trying to steal!")

        elif other_member.potatoes < amount:
            return await interaction.response.send_message(f"{other} doesn't have that many potatoes!")

        if randint(0, 100) < 25:
            member.add_potatoes(amount)
            other_member.remove_potatoes(amount)
            embed = discord.Embed.from_dict({
                "title": ":gloves: :potato: :gloves:",
                "description": f"{interaction.user.mention} stole {amount} potato{'es' if amount > 1 else ''} from {other.mention} giving {interaction.user.display_name} a total of {member.potatoes}\n" + ((":potato:" * member.potatoes) if member.potatoes < 50 else (":potato:" * 50)) + ":chart_with_upwards_trend:",
                "color": 0x2f3136,
            })
        else:
            new_amount = randint(1, amount)
            member.remove_potatoes(new_amount)
            other_member.add_potatoes(new_amount)
            embed = discord.Embed.from_dict({
                "title": ":gloves: :potato: :gloves:",
                "description": f"{interaction.user.mention} tried to steal {amount} potato{'es' if amount > 1 else ''} from {other.mention} but failed instead giving {new_amount} to {other} leaving {interaction.user.display_name} with {member.potatoes}\n" + ((":potato:" * member.potatoes) if member.potatoes < 50 else (":potato:" * 50)) + ":chart_with_downwards_trend:",
                "color": 0x2f3136,
            })

        member.add_cooldown("steal")
        await interaction.response.send_message(embed=embed)

    @potato.command()
    @discord.app_commands.describe(other="Who to give the potatoes to", amount="The amount of potatoes to give")
    async def give(self, interaction: discord.Interaction, other: discord.Member, amount: int):
        """Give potatoes to another member"""
            
        member = Member(interaction.user.id)
        other_member = Member(other.id)
    
        if member.potatoes < amount:
            return await interaction.response.send_message(f"You do not have that many potatoes!")

        if amount < 1:
            return await interaction.response.send_message(f"You can't give less than 1 potato")
    
        member.remove_potatoes(amount)
        other_member.add_potatoes(amount)
    
        await interaction.response.send_message(content=f"You gave {other} {amount} potato{'es' if amount > 1 else ''}, how nice of you.")

    @potato.command()
    async def top(self, interaction: discord.Interaction):
        """Shows the top 10 potato collectors"""
        members: List[Member] = Member.get_top_members()

        embed = discord.Embed.from_dict({
            "title": ":potato: Top 10 potato collectors :potato:",
            "description": "\n".join([f"{i + 1}. {interaction.guild.get_member(member.id).display_name if interaction.guild.get_member(member.id) else 'NAME UNAVAILABLE'} - {member.potatoes}" for i, member in enumerate(members)]),
            "color": 0x2f3136,
        })

        await interaction.response.send_message(embed=embed)

    @potato.command()
    async def drop(self, interaction: discord.Interaction):
        """Drops a potato in the chat"""
        member = Member(interaction.user.id)

        if member.potatoes < 1:
            return await interaction.response.send_message(f"You do not have any potatoes!")

        member.remove_potatoes(1)

        await interaction.response.send_message(content=":potato:")

        Member.potato = await interaction.original_response()

    @potato.command()
    @discord.app_commands.describe(other="Who to modify the potatoes of", type="The type of modification", amount="The amount of potatoes")
    async def modify(self, interaction: discord.Interaction, other: discord.Member, type: Literal["+", "-", "set"], amount: int):
        """Modify another member's potatoes"""
        # Check if the user is an admin
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(f"You are not an admin, you cannot use this command!")

        member = Member(other.id)

        if type == "+":
            member.add_potatoes(amount)
            await interaction.response.send_message(content=f"You added {amount} potato{'es' if amount > 1 else ''} to {other}'s balance.", ephemeral=True)
        elif type == "-":
            member.remove_potatoes(amount)
            await interaction.response.send_message(content=f"You removed {amount} potato{'es' if amount > 1 else ''} from {other}'s balance.", ephemeral=True)
        elif type == "set":
            member.set_potatoes(amount)
            await interaction.response.send_message(content=f"You set {other}'s potato count to {amount}.", ephemeral=True)

    @potato.command()
    async def daily(self, interaction: discord.Interaction):
        """Gives you daily potatoes"""
        member = Member(interaction.user.id)
        if member.has_valid_cooldown("daily", hours=24):
            return await interaction.response.send_message(f"You can't get daily potatoes yet, you can claim them <t:{int((member.cooldowns['daily'] + timedelta(hours=14)).timestamp())}:R>")

        member.add_potatoes(5)
        member.add_cooldown("daily")
        await interaction.response.send_message(content=f"You claimed your daily 5 potatoes :potato:, and now hold onto {member.potatoes} potatos")

Cog = Potato