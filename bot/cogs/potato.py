import discord
import aiohttp

from discord.ext import commands, tasks

from io import BytesIO
from random import randint
from typing import Literal, List, Tuple
from datetime import timedelta, datetime

from bot.__init__ import Bot
from bot.utils.classes import PotatoMember as Member, Auction, AuctionItem, PerkType
from bot.static.constants import GUILD_OBJECT, CREATE_ROLE_WITH_COLOUR, DAILY_POTATOES
from bot.utils.paginator import Paginator
from bot.utils.interactions import Modal, View, Select, Button
from bot.utils.timeconverter import TimeConverter

class CreateRoleModal(Modal):

    def __init__(self, user_id: int, colour: bool):
        super().__init__(user_id=user_id, title="Create custom Role")
        self.add_item(discord.ui.TextInput(label="Role name", placeholder="Role name", required=True, max_length=32, min_length=2, style=discord.TextStyle.short))
        self.add_item(discord.ui.TextInput(label="Role icon", placeholder="https://images.com/some_image.jpeg", required=False, max_length=256, min_length=2, style=discord.TextStyle.short))

        if colour:
            self.add_item(discord.ui.ColorPicker(label="Role colour", default=str(discord.Color.default()), required=True))

class CreateAuctionView(View):

    def __init__(self, user_id: int, auctionable_roles: List[int], premium_roles: List[int], original_interaction: discord.Interaction):
        super().__init__(user_id)
        self.kwargs = AuctionItem.raw_kwargs()
        self.kwargs["listed_by"] = user_id
        self._ending_in = None
        self._raw_ending_in = None
        self.original_interaction = original_interaction
        self.auctionable_roles = auctionable_roles
        self.premium_roles = premium_roles
        self.guild = self.original_interaction.guild
        self.item = None

    async def _modal_edit(
        self,
        interaction: discord.Interaction, 
        title: str, 
        label: str, 
        placeholder: str, 
        max_length: int, 
        style: discord.TextStyle = discord.TextStyle.short,
        default: str = None
    ) -> Tuple[str, discord.Interaction]:

        modal = Modal(interaction.user.id, title=title)
        modal.add_item(discord.ui.TextInput(label=label, placeholder=placeholder, required=True, max_length=max_length, style=style, default=default))

        await interaction.response.send_modal(modal)

        await modal.wait()

        if modal.timed_out:
            return await self.disable(await self.original_interaction.original_response())

        return (modal.values[0], modal.interaction)

    @discord.ui.button(label="Name", style=discord.ButtonStyle.blurple)
    async def title(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        resp = await self._modal_edit(interaction, "Choose a name", "Name", "A real potato", 60, default=self.kwargs["name"])
        if not resp: return

        value, interaction = resp

        self.kwargs["name"] = value
        await interaction.response.edit_message(embed=AuctionItem(**self.kwargs).to_embed(self.guild))

    @discord.ui.button(label="Description", style=discord.ButtonStyle.blurple)
    async def description(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        resp = await self._modal_edit(interaction, "Choose a description", "Description", "Some cool description", 2000, style=discord.TextStyle.long, default=self.kwargs["description"])
        if not resp: return

        value, interaction = resp

        self.kwargs["description"] = value
        await interaction.response.edit_message(embed=AuctionItem(**self.kwargs).to_embed(self.guild))

    @discord.ui.button(label="Listing Price", style=discord.ButtonStyle.blurple)
    async def price(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        resp = await self._modal_edit(interaction, "Choose a price in potatoes", "Price", "100", 10, default=str(self.kwargs["listing_price"]) if self.kwargs["listing_price"] else None)
        if not resp: return

        value, interaction = resp

        if not value.isdigit():
            return await interaction.response.send_message("Price must be a number", ephemeral=True)

        if int(value) < 1:
            return await interaction.response.send_message("Price must be at least 1", ephemeral=True)

        self.kwargs["listing_price"] = int(value)
        await interaction.response.edit_message(embed=AuctionItem(**self.kwargs).to_embed(self.guild))

    @discord.ui.button(label="Image", style=discord.ButtonStyle.blurple)
    async def image(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        resp = await self._modal_edit(interaction, "Choose an image url", "Image url", "https://images.com/image.png", 500, default=self.kwargs["image"])
        if not resp: return

        value, interaction = resp

        self.kwargs["image"] = value
        await interaction.response.edit_message(embed=AuctionItem(**self.kwargs).to_embed(self.guild))

    @discord.ui.button(label="Ending in", style=discord.ButtonStyle.blurple)
    async def ending_at(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        resp = await self._modal_edit(interaction, "Choose an ending time", "Ending in", "10h", 10, default=self._raw_ending_in)
        if not resp: return

        value, interaction = resp

        try:
            self._ending_in = await TimeConverter().convert(value)
        except commands.BadArgument as e:
            return await interaction.response.send_message(e)

        self._raw_ending_in = value
        self.kwargs["ending_at"] = datetime.now() + self._ending_in
        await interaction.response.edit_message(embed=AuctionItem(**self.kwargs).to_embed(self.guild))

    @discord.ui.button(label="Colour", style=discord.ButtonStyle.blurple)
    async def colour(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        resp = await self._modal_edit(interaction, "Choose a colour", "Colour", "#ffffff", 8, default=str(discord.Colour(self.kwargs["colour"])) if self.kwargs["colour"] else None)
        if not resp: return

        value, interaction = resp

        try:
            self.kwargs["colour"] = int(discord.Colour.from_str(value))
        except ValueError:
            return await interaction.response.send_message("Invalid colour", ephemeral=True)

        await interaction.response.edit_message(embed=AuctionItem(**self.kwargs).to_embed(self.guild))

    @discord.ui.button(label="Amount", style=discord.ButtonStyle.blurple)
    async def amount(self, interaction: discord.Interaction, _: discord.Button) -> None:
        resp = await self._modal_edit(interaction, "Choose an amount", "Amount", "1", 5, default=str(self.kwargs["amount"]))
        if not resp: return

        value, interaction = resp

        if not value.isdigit():
            return await interaction.response.send_message("Amount must be a number", ephemeral=True)

        if int(value) < 1:
            return await interaction.response.send_message("Amount must be greater than 0", ephemeral=True)

        if self.kwargs["type"]:
            if self.kwargs["type"] in (PerkType.CUSTOM_ROLE, PerkType.CUSTOM_STICKER, PerkType.CUSTOME_EMOTE):
                if not Member(interaction.user.id).has_item(self.kwargs["type"], int(value)):
                    return await interaction.response.send_message("You don't have that amount of items", ephemeral=True)
            elif self.kwargs["type"] == PerkType.ROLE and int(value) > 1:
                return await interaction.response.send_message("You can't sell more than one role", ephemeral=True)

        self.kwargs["amount"] = int(value)
        await interaction.response.edit_message(embed=AuctionItem(**self.kwargs).to_embed(self.guild))

    @discord.ui.button(label="Type", style=discord.ButtonStyle.blurple)
    async def type(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        view = View(self.user_id)
        view.add_item(Select([discord.SelectOption(label=p.value['name'], value=p.name) for p in PerkType if not p in [PerkType.NOT_SPECIFIED]]))

        await interaction.response.send_message("Please chose the type of what you would like to auction", view=view, ephemeral=True)

        await view.wait()

        if view.timed_out:
            return await self.disable(await self.original_interaction.original_response())

        if not getattr(PerkType, view.value) in [PerkType.OTHER, PerkType.NOT_SPECIFIED]:
            if not Member(interaction.user.id).has_item(getattr(PerkType, view.value), self.kwargs["amount"]) and not interaction.user.guild_permissions.administrator:
                await view.interaction.response.send_message("You don't have the required item(s) to auction this", ephemeral=True)

            else:
                self.kwargs["type"] = getattr(PerkType, view.value)

                if self.kwargs["type"] == PerkType.ROLE:
                    roles = [discord.SelectOption(label=role.name, value=role.id) for role in interaction.guild.roles if role.id in self.auctionable_roles and (interaction.user.guild_permissions.administrator or role.id in interaction.user.roles)]

                    if not roles:
                        return await interaction.response.send_message("You don't have any roles to auction", ephemeral=True)

                    # Create a select to select the role to auction off
                    role_view = View(self.user_id)
                    role_view.add_item(Select(roles))

                    await view.interaction.response.send_message("Please chose the role you would like to auction", view=role_view, ephemeral=True)

                    await role_view.wait()

                    if role_view.timed_out:
                        return await self.disable(await self.original_interaction.original_response())

                    self.kwargs["role_id"] = int(role_view.value)

                    await role_view.disable(await view.interaction.original_response(), respond=False)
                    view.interaction = role_view.interaction # Change the used interaction to the unused one

                new_view = View(self.user_id)
                new_view.add_item(Button(label="Yes", style=discord.ButtonStyle.green, custom_id="yes"))
                new_view.add_item(Button(label="No", style=discord.ButtonStyle.red, custom_id="no"))

                await view.interaction.response.send_message("Would you like to set description and title for this item according to its type?", view=new_view, ephemeral=True)

                await new_view.wait()

                if new_view.timed_out:
                    return await self.disable(await self.original_interaction.original_response())

                if new_view.value == "yes":
                    self.kwargs["name"] = self.kwargs["type"].value["name"]
                    self.kwargs["description"] = self.kwargs["type"].value["description"]
                    await new_view.interaction.response.send_message(content=":thumbsup: automatically set name and description", ephemeral=True)
                    await new_view.disable(await view.interaction.original_response())
                else:
                    await new_view.interaction.response.send_message(content=":thumbsup: not automatically set name and description", ephemeral=True)
                    await new_view.disable(await view.interaction.original_response())

        else:
            self.kwargs["type"] = getattr(PerkType, view.value)

        await view.disable(await interaction.original_response())
        await (await self.original_interaction.original_response()).edit(embed=AuctionItem(**self.kwargs).to_embed(self.guild))

    @discord.ui.button(label="Featured", emoji="<:unchecked_box:1014279412881051668>", style=discord.ButtonStyle.grey)
    async def featured(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not interaction.user.guild_permissions.administrator and len([r for r in interaction.user.roles if r.id in self.premium_roles]):
            return await interaction.response.send_message("You must have be an admin or premium member to create a featured auction", ephemeral=True)

        self.kwargs["featured"] = button.style == discord.ButtonStyle.grey
        for child in self.children:
            if child.label == "Featured":
                child.emoji = "<:checked_box:1014279465624408214>" if self.kwargs["featured"] else "<:unchecked_box:1014279412881051668>"
                child.style = discord.ButtonStyle.green if self.kwargs["featured"] else discord.ButtonStyle.grey
                break

        await interaction.response.edit_message(embed=AuctionItem(**self.kwargs).to_embed(self.guild), view=self)

    @discord.ui.button(label="Publish", style=discord.ButtonStyle.green)
    async def publish(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        for key, value in self.kwargs.items():
            if value is None and not key in ["image", "colour", "role_id"]:
                return await interaction.response.send_message("You must fill out all fields except image and colour to publish an auction", ephemeral=True)
                
        self.kwargs["ending_at"] = datetime.now() + self._ending_in
        auction = Auction()
        final_item = AuctionItem(auction=auction, **self.kwargs)
        auction.add_item(final_item)
        self.item = final_item

        await interaction.response.send_message("Auction item published!", ephemeral=True)
        await self.disable(await self.original_interaction.original_response())
        self.stop()

class Potato(commands.Cog):

    def __init__(self, client: Bot):
        self.client = client
        self.premium_perks = { # Reuducing cost or increasing bonus of potatoes
            998348150316208244: 1.5,
            998347219126202472: 1.3,
            998346693965779018: 1.1,
        }

    potato = discord.app_commands.Group(name="potato", description="Potato commands", guild_ids=[GUILD_OBJECT.id])
    auctions = discord.app_commands.Group(name="auctions", description="Auction off your items or get them from other people", guild_ids=[GUILD_OBJECT.id], parent=potato)

    @property
    def guild(self) -> discord.Guild:
        return self.client.get_guild(GUILD_OBJECT.id)

    @property
    def potato_channel(self) -> discord.TextChannel:
        return self.guild.get_channel(self.client.server_info.POTATO_BONUS_CHANNEL)

    @commands.Cog.listener()
    async def on_ready(self):
        await self.client.wait_until_ready()
        self.auction_loop.start()

    def _intersect(self, list1: list, list2: list) -> bool:
        return set(list1).intersection(set(list2))

    @tasks.loop(minutes=1)
    async def auction_loop(self) -> None:
        """Loop that runs every minute to check if any auctions have ended"""
        for item in Auction().items:
            if item.should_end:
                bids = len(item.bidders)
                seller = self.guild.get_member(item.listed_by)

                if not bids:
                    await self.potato_channel.send(f"Nobody bid on `{item.name}` (ID: {item.id}) so it has been removed from the auction")
                    try:
                        await seller.send(f"Nobody bid on `{item.name}` (ID: {item.id}) so it has been removed from the auction")
                    except (discord.HTTPException, AttributeError):
                        pass
                    Auction().remove_item(item)
                    continue

                if item.type == PerkType.ROLE:
                    role = self.guild.get_role(item.role_id)
                    if not role in seller.roles and not seller.guild_permissions.administrator:
                        await self.potato_channel.send(f"The auction for `{item.name}` (ID: {item.id}) ended, but {seller.mention} is not in posession of the role anymore so it has been removed from the auction")
                        Auction().remove_item(item)
                        continue
                
                elif item.type != PerkType.OTHER:
                    if not Member(seller.id).has_item(item.type, item.amount) and not seller.guild_permissions.administrator:
                        await self.potato_channel.send(f"The auction for `{item.name}` (ID: {item.id}) ended, but {seller.mention} is not in posession of the item(s) anymore so it has been removed from the auction")
                        Auction().remove_item(item)
                        continue

                purchased_by, winning_bid = item.sell(self.guild)

                try:
                    await seller.send(f"Your auction for `{item.name}` (ID: {item.id}) has ended and has been sold to **{purchased_by}** (ID: {purchased_by.id}) for **{winning_bid}** potatoes")
                except (discord.HTTPException, AttributeError):
                    pass
                try:
                    await purchased_by.send(f"You have won the auction for `{item.name}` (ID: {item.id}) for **{winning_bid}** potatoes")
                except (discord.HTTPException, AttributeError):
                    pass

                await self.potato_channel.send(f"`{item.name}` has been sold to {purchased_by.mention} (ID: {item.id}) for **{winning_bid}** potatoes. There was a total of `{bids}` bids")


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
            if role_id := self._intersect([r.id for r in interaction.user.roles], list(self.premium_perks.keys())):
                bonus = int((self.premium_perks[role_id[0]] - 1) * amount)
            elif interaction.user in interaction.guild.premium_subscribers:
                bonus = int(0.3 * amount)
            else: 
                bonus = None
                bonustext = ""

            member.add_potatoes(amount)
            if bonus:
                bonustext = f" along with a bonus of {bonus} potato{'es' if bonus > 1 else ''}"
                member.add_potatoes(bonus)

            embed = discord.Embed.from_dict({
                "title": ":game_die: :potato: :game_die:",
                "description": f"Your gambling paid off, you won {amount} potato{'es' if amount > 1 else ''}{bonustext} giving you a total of {member.potatoes} potatoes\n" + ((":potato:" * member.potatoes) if member.potatoes < 50 else (":potato:" * 50)),
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
            return await interaction.response.send_message(f"You can't get daily potatoes yet, you can claim them <t:{int((member.cooldowns['daily'] + timedelta(hours=24)).timestamp())}:R>")

        if role_id := self._intersect([r.id for r in interaction.user.roles], list(self.premium_perks.keys())):
            bonus = int((self.premium_perks[role_id[0]] - 1) * DAILY_POTATOES)
        elif interaction.user in interaction.guild.premium_subscribers:
            bonus = int(0.3 * DAILY_POTATOES)
        else:
            bonus = None
            bonustext = ""

        member.add_potatoes(DAILY_POTATOES)
        if bonus:
            bonustext = f" along with a bonus of {bonus} potato{'es' if bonus > 1 else ''}"
            member.add_potatoes(bonus)

        member.add_potatoes(DAILY_POTATOES)
        member.add_cooldown("daily")
        await interaction.response.send_message(content=f"You claimed your daily {DAILY_POTATOES} potatoes{bonustext} :potato:, and now hold onto {member.potatoes} potatos")

    @potato.command()
    async def redeem(self, interaction: discord.Interaction, item: Literal["Custom emoji", "Custom role", "Custom sticker"]):
        """Redeem an item won from an auction"""
        member = Member(interaction.user.id)

        items = {
            "Custom emoji": PerkType.CUSTOM_EMOTE,
            "Custom role": PerkType.CUSTOM_ROLE,
            "Custom sticker": PerkType.CUSTOM_STICKER,
        }

        if not member.has_item(items[item]):
            return await interaction.response.send_message(f"You do not have any {item}s to redeem!")

        if item == "Custom emoji":
            modal = Modal(interaction.user.id, title="Emoji creator")
            modal.add_item(discord.ui.TextInput(label="Emoji name", placeholder="Emoji_name", required=True, max_length=25))
            modal.add_item(discord.ui.TextInput(label="Emoji URL", placeholder="https://example.com/emoji.png", required=True, max_length=255))

            await interaction.response.send_modal(modal)

            await modal.wait()

            if modal.timed_out:
                return 

            await modal.interaction.response.defer()

            # Save emoji to io bytes
            emoji_name: str = modal.values[0]
            emoji_url: str = modal.values[1]
            try:
                emoji_response = await self.client.session.get(emoji_url)
                emoji_bytes = await emoji_response.read()
            except aiohttp.ClientError as e:
                return await modal.interaction.followup.send(f"Error getting emoji: {e}")

            # Create emoji
            try:
                emoji = await interaction.guild.create_custom_emoji(name=emoji_name.replace(" ", "_"), image=emoji_bytes)
            except discord.HTTPException:
                return await modal.interaction.followup.send(f"Error creating emoji. Make sure the image url is valid and the file is not too big")

            member.remove_item(items[item])
            return await modal.interaction.followup.send(f"You created the emoji {emoji}!")

        elif item == "Custom role":
            modal = CreateRoleModal(interaction.user.id, colour = CREATE_ROLE_WITH_COLOUR)

            await interaction.response.send_modal(modal)

            await modal.wait()

            if modal.timed_out:
                return 

            await modal.interaction.response.defer()

            role_name: str = modal.values[0]
            role_icon = modal.values[1]
            
            if CREATE_ROLE_WITH_COLOUR:
                try:
                    role_colour = discord.Colour.from_str(modal.values[2])
                except ValueError:
                    return await modal.interaction.followup.send(f"Error creating role: Invalid colour")
            else:
                role_colour = discord.Color.default()

            # Save role icon
            if role_icon:
                try:
                    role_icon_response = await self.client.session.get(role_icon)
                    role_icon_bytes = await role_icon_response.read()
                except aiohttp.ClientError as e:
                    role_icon_bytes = role_icon # If the icon is an emoji

            # Create role
            try:
                role = await interaction.guild.create_role(name=role_name, colour=role_colour, reason=f"Created by {interaction.user}", display_icon=role_icon_bytes if role_icon else None)
            except discord.HTTPException:
                return await modal.interaction.followup.send(f"Error creating role. Make sure the icon url/emoji is valid and not too big")

            member.remove_item(items[item])
            await interaction.user.add_roles(role) # Adds the role to the user
            return await modal.interaction.followup.send(f"You created the role {role.name}!")

        elif item == "Custom sticker":
            modal = Modal(interaction.user.id, title="Sticker creator")
            modal.add_item(discord.ui.TextInput(label="Sticker URL", placeholder="https://example.com/sticker.png", required=True, max_length=255))
            modal.add_item(discord.ui.TextInput(label="Sticker name", placeholder="Sticker name", required=True, max_length=25))
            modal.add_item(discord.ui.TextInput(label="Sticker description", placeholder="Sticker description", required=True, max_length=255))

            await interaction.response.send_modal(modal)

            await modal.wait()

            if modal.timed_out:
                return 

            await modal.interaction.response.defer()

            sticker_url: str = modal.values[0]
            sticker_name: str = modal.values[1]
            sticker_description: str = modal.values[2]

            # Fetch sticker bytes and save them to a discord.File
            try:
                sticker_response = await self.client.session.get(sticker_url)
                sticker_bytes = await sticker_response.read()
                sticker_file = discord.File(BytesIO(sticker_bytes), filename=sticker_name)
            except aiohttp.ClientError as e:
                return await modal.interaction.followup.send(f"Error getting sticker: {e}")

            # Create sticker
            try:
                sticker = await interaction.guild.create_sticker(name=sticker_name,description=sticker_description,file=sticker_file, emoji="\U00002764")
            except discord.HTTPException:
                return await modal.interaction.followup.send(f"Error creating sticker. Make sure the image url is valid and not too big. Only png and apng are supported file types.")

            member.remove_item(items[item])
            return await modal.interaction.followup.send(f"You created the sticker {sticker.name}!")


    @auctions.command(name="list")
    async def _list(self, interaction: discord.Interaction):
        """Lists all the auctions"""
        auction = Auction()

        if not auction.items:
            return await interaction.response.send_message("There are no auctions currently running.")

        def make_embed(page, _, pages):
            embed = auction.sorted_items[page-1].to_embed(interaction.guild)
            embed.set_footer(text=f"Page {page}/{len(pages)}")

            return embed

        return await Paginator(interaction, func=make_embed, pages=auction.sorted_items, max_pages=len(auction.items)).start()

    @auctions.command()
    async def create(self, interaction: discord.Interaction):
        """Creates an auction"""
        if not self.client.server_info.VERIFIED_ROLE in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message("You must be verified to create an auction.", ephemeral=True)

        view = CreateAuctionView(interaction.user.id, self.client.server_info.AUCTIONABLE_ROLES, self.client.server_info.PREMIUM_ROLES, interaction)

        await interaction.response.send_message("Please edit this preview of your auction listing and then submit it.", embed=AuctionItem().to_embed(self.guild), view=view, ephemeral=True)

        await view.wait()

        if not view.item: return

        await self.potato_channel.send(content=f"<@&{self.client.server_info.AUCTION_PING}> A new auction has been created!", embed=view.item.to_embed(interaction.guild, dynamic_info=False))

    @auctions.command()
    @discord.app_commands.describe(item_id="The item to bid on", bid="The amount to bid", maximum_bid="Automatically overbid anyone below this amount")
    async def bid(self, interaction: discord.Interaction, item_id: int, bid: int, maximum_bid: int = None):
        """Bids on an item"""
        auction = Auction()

        if item_id not in [i.id for i in auction.items]:
            return await interaction.response.send_message("That item does not exist.", ephemeral=True)

        item = auction.item_where_id(item_id)

        if item.listed_by == interaction.user.id:
            return await interaction.response.send_message("You cannot bid on your own item.", ephemeral=True)

        if item.current_price >= bid:
            return await interaction.response.send_message("Your bid is lower than the current bid.", ephemeral=True)

        if bid > Member(interaction.user.id).potatoes:
            return await interaction.response.send_message("You do not have enough potatoes to bid that much.", ephemeral=True)

        previous_highest = item._find_first_valid_bidder()
        highest = item.bid(interaction.user, bid, maximum_bid)
        item.sync() # Sync the item with the database

        if highest:
            await self.potato_channel.send(f"{interaction.user.mention} now has the highest bid of {item.current_price} potatoes :potato:{f' , outbidding <@{previous_highest}>,' if previous_highest else ''} on `{item.name}`")
            await interaction.response.send_message("You have successfully bid on this item.", ephemeral=True)
        else:
            await self.potato_channel.send(f"{interaction.user.mention} tried to bid on `{item.name}` but was immediately outbid by <@{previous_highest[0]}> to a new price of {item.current_price} potatoes :potato:")
            await interaction.response.send_message(f"You have been outbid. The new current bid is {item.current_price}", ephemeral=True)

    @auctions.command()
    @discord.app_commands.describe(item_id="The item to remove")
    async def remove(self, interaction: discord.Interaction, item_id: int):
        """Removes an item from the auction"""
        auction = Auction()

        if item_id not in [i._index for i in auction.items]:
            return await interaction.response.send_message("That item does not exist.", ephemeral=True)

        item = auction.item_where_id(item_id)

        if item.listed_by != interaction.user.id and self.client.server_info.TRUSTED_ROLE not in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message("You cannot remove an item that you do not own or without being a moderator.", ephemeral=True)

        auction.remove_item(item)
        await interaction.response.send_message("You have successfully removed this item from the auction.", ephemeral=True)

    @auctions.command()
    @discord.app_commands.describe(item_id="The item to view")
    async def view(self, interaction: discord.Interaction, item_id: int):
        """View infos about an item being auctioned by its id"""
        auction = Auction()

        if item_id not in [i.id for i in auction.items]:
            return await interaction.response.send_message("That item does not exist.", ephemeral=True)

        item = auction.item_where_id(item_id)

        await interaction.response.send_message(embed=item.to_embed(interaction.guild))

Cog = Potato