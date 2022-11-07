import discord

from typing import Union, List
from bot.static.constants import ServerInfo, CONSTANTS

class View(discord.ui.View):
    """Subclassing this for buttons enabled us to not have to define interaction_check anymore, also not if we want a select menu"""
    def __init__(self, user_id: Union[int, List[int]] = None, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id
        self.value = None
        self.timed_out = False
        self.interaction = None

    async def on_timeout(self) -> None:
        self.timed_out = True

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not self.user_id: return True 
        
        if isinstance(self.user_id, int):
            if not (val := interaction.user.id == self.user_id):
                await interaction.response.defer()
        else:
            if not (val := (interaction.user.id in self.user_id)):
                await interaction.response.defer()
        self.interaction = interaction # So we can respond to it anywhere
        return val

    async def disable(self, msg: discord.Message, respond: bool = True) -> Union[discord.Message, None]:
        """"Disables the children inside of the view"""
        if not [c for c in self.children if not c.disabled]: # if every child is already disabled, we don't need to edit the message again
            return

        for c in self.children:
            c.disabled = True

        if self.interaction and not self.interaction.response.is_done() and respond:
            await self.interaction.response.edit_message(view=self)
        else:
            await msg.edit(view=self)

class Modal(discord.ui.Modal):
    """A modal for various usages"""
    def __init__(self, user_id: Union[int, List[int]], **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id
        self.values = []
        self.timed_out = False
        self.interaction = None

    async def on_timeout(self) -> None:
        self.timed_out = True

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if isinstance(self.user_id, int):
            if not (val := interaction.user.id == self.user_id):
                await interaction.response.defer()
        else:
            if not (val := (interaction.user.id in self.user_id)):
                await interaction.response.defer()
        return val

    async def disable(self, msg: discord.Message) -> Union[discord.Message, None]:
        """"Disables the children inside of the view"""
        if not [c for c in self.children if not c.disabled]: # if every child is already disabled, we don't need to edit the message again
            return

        for c in self.children:
            c.disabled = True

        await msg.edit(view=self)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """Called when the modal is submitted"""
        for child in self.children:
            self.values.append(child.value)
            
        self.interaction = interaction

class Button(discord.ui.Button):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def callback(self, interaction: discord.Interaction):
        self.view.value = self.custom_id
        self.view.interaction = interaction
        self.view.stop()

class Select(discord.ui.Select):
    """Creates a select menu to view the command groups"""
    def __init__(self, options, **kwargs):
        super().__init__( 
            min_values=1, 
            max_values=1, 
            options=options,
            **kwargs
        )

    async def callback(self, interaction: discord.Interaction):
        self.view.value = interaction.data["values"][0]
        for opt in self.options:
            if opt.value == str(self.view.value):
                opt.default = True
        self.view.stop()

class PersistentVerificationView(discord.ui.View):
    """A view for persistent verification"""
    def __init__(self, applicant: int, **kwargs):
        super().__init__(timeout=None, **kwargs)

        button_verify = discord.ui.Button(label="Verify", custom_id=f"verify:{applicant}", style=discord.ButtonStyle.green)
        button_verify.callback = self.verify_callback

        button_deny = discord.ui.Button(label="Deny", custom_id=f"deny:{applicant}", style=discord.ButtonStyle.red)
        button_deny.callback = self.deny_callback

        self.add_item(button_verify)
        self.add_item(button_deny)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        verifier_role = interaction.guild.get_role(ServerInfo.NSS.WELCOMER_ROLE if interaction.guild.id == ServerInfo.NSS.ID else ServerInfo.TEST.WELCOMER_ROLE) 
        if not (val := verifier_role in interaction.user.roles):
            await interaction.response.send_message("You don't have the permissions to do that!", ephemeral=True)
        return val

    async def verify_callback(self, interaction: discord.Interaction):
        applicant = interaction.guild.get_member(int(interaction.data["custom_id"].split(":")[1]))

        role = interaction.guild.get_role(ServerInfo.NSS.VERIFIED_ROLE if interaction.guild.id == ServerInfo.NSS.ID else ServerInfo.TEST.VERIFIED_ROLE) 
        # Workaround for not being able to access wether it is a testing evironment or not

        await applicant.add_roles(role)
        await interaction.response.send_message(f"✅ Verified {applicant.mention}", ephemeral=True)
        try:
            await applicant.send(f"Your application in Nico's Safe Space has been approved and you can now pick up roles (with `/roles help`) to access sensitive channels! ")
        except discord.HTTPException:
            pass # Ignore closed dms

        # Edit the buttons
        verified_button = discord.ui.Button(style=discord.ButtonStyle.green, label=f"Verified by {interaction.user}", disabled=True)
        self.clear_items()
        self.add_item(verified_button)

        await interaction.message.edit(view=self)

        # Clear pending application status
        new_pending_apps = [x for x in CONSTANTS.find_one({"_id": "pending_applications"})["ids"] if x["applicant"] != applicant.id]
        CONSTANTS.update_one({"_id": "pending_applications"}, {"$set": {"ids": new_pending_apps}})

    async def deny_callback(self, interaction: discord.Interaction):
        applicant = interaction.guild.get_member(int(interaction.data["custom_id"].split(":")[1]))

        # save applicant id to denied database
        existing = CONSTANTS.find_one({"_id": "denied"})

        if not existing:
            CONSTANTS.insert_one({"_id": "denied", "ids": [applicant.id]})
        else:
            CONSTANTS.update_one({"_id": "denied"}, {"$push": {"ids": applicant.id}})

        await interaction.response.send_message(f"✅ Denied {applicant.mention}", ephemeral=True)

        try:
            await applicant.send(f"Your application in Nico's Safe Space has been denied. If you think this is a mistake, please contact a staff member.")
        except discord.HTTPException:
            pass

        # Edit the buttons
        denied_button = discord.ui.Button(style=discord.ButtonStyle.grey, label=f"Denied by {interaction.user}", disabled=True)
        self.clear_items()
        self.add_item(denied_button)

        await interaction.message.edit(view=self)

        # Clear pending application status
        new_pending_apps = [x for x in CONSTANTS.find_one({"_id": "pending_applications"})["ids"] if x["applicant"] != applicant.id]
        CONSTANTS.update_one({"_id": "pending_applications"}, {"$set": {"ids": new_pending_apps}})