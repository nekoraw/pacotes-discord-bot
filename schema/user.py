from typing import Dict

import discord
from beanie import Document, Indexed

from schema.parcel import Parcel


class User(Document):
    discord_id: Indexed(int, unique=True)
    parcels: Dict[str, str]
    mostrar_rastreio: bool = False
    server_list_to_update: list = []

    @staticmethod
    async def get_user(discord_id):
        user = await User.find(User.discord_id == discord_id).first_or_none()
        if user is None:
            user = User(discord_id=discord_id, parcels={})
            await user.save()

        return user

    @staticmethod
    async def get_parcels_autocomplete(ctx: discord.AutocompleteContext):
        user = await User.get_user(ctx.interaction.user.id)
        return [v for v in user.parcels.keys() if ctx.value.lower() in v.lower()]

    def get_parcel_name(self, parcel: Parcel):
        for k, v in self.parcels.items():
            if v == parcel.internal_id:
                return k
        return None
