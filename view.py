import discord.ui


class DeleteMessageView(discord.ui.View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(label="Deletar Mensagem", style=discord.ButtonStyle.red)
    async def callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.message.interaction.user != interaction.user:
            if not interaction.channel.permissions_for(interaction.user).manage_messages:
                await interaction.response.send_message("Você não pode deletar essa mensagem.", ephemeral=True)
                return

        await interaction.message.delete()
