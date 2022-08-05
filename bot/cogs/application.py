import discord
from discord.ext import commands

from typing import Union

from bot.utils.interactions import Modal, View, Button
from bot.static.constants import QUESTIONS

class ApplicationModal(Modal):

    def __init__(self, user_id: int, page: int):
        super().__init__(user_id, title="Application")
        if page == 1:
            questions = QUESTIONS[:5]
        elif page == 2:
            questions = QUESTIONS[5:10]
        else:
            questions = QUESTIONS[-2:]

        for question in questions:
            self.add_item(discord.ui.TextInput(label=question["question"], placeholder=question["placeholder"], required=question["required"], max_length=question["max_length"], min_length=question["min_length"] if "min_length" in question else 0, style=discord.TextStyle.short if "style" not in question else question["style"]))

class Application(commands.Cog):

    def __init__(self, client):
        self.client = client

    async def cog_load(self):
        print("Loaded application cog")

    def _to_embed(self, user: Union[discord.Member, discord.User], responses: list) -> discord.Embed:
        embed = discord.Embed.from_dict({
            "title": f"Application of {user.name}",
            "description": user.mention,
            "fields": [{"name": QUESTIONS[i]["question"], "value": responses[i] or "N/A"} for i in range(len(responses))],
            "color": 0x2f3136,
            "thumbnail": {
                "url": user.avatar.url if user.avatar else None
            }
        })
        return embed

    @discord.app_commands.command()
    async def apply(self, interaction: discord.Interaction):
        """Apply for the verified role with this command"""

        if self.client.server_info.VERIFIED_ROLE in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message("You are already verified!", ephemeral=True)

        answers = []

        for i in range(1, 4):
            modal = ApplicationModal(interaction.user.id, i)
            await interaction.response.send_modal(modal)
            await modal.wait()

            if modal.timed_out:
                return
            else:
                answers = [*answers, *modal.values]

                if i < 3:
                    button = Button(label="Continue", style=discord.ButtonStyle.green)
                    view = View(interaction.user.id)
                    view.add_item(button)
                    await modal.interaction.response.send_message(f"Application completed {i}/3. Press continue to continue.", view=view, ephemeral=True)
                    await view.wait()
                    
                    view.children[0].disabled = True
                    await modal.interaction.edit_original_message(view=view)

                    if view.timed_out:
                        return
                    else:
                        interaction = view.interaction

        channel = self.client.get_channel(self.client.server_info.APPLICATION_CHANNEL)
        await channel.send(embed=self._to_embed(interaction.user, answers))
        await modal.interaction.response.send_message("✅ Application submitted. Please be patient while it is reviewed. You will be dmed in case of a decision.", ephemeral=True)


Cog = Application

async def setup(client):
    await client.add_cog(Application(client))