import asyncio
import logging
import os
from datetime import datetime

from dotenv import load_dotenv

from client import DiscordClient
from schema.services import Service
from schema.server import Server
from schema.user import User
from schema.parcel import Parcel
from embed import create_package_embeds


class ParcelChecking:
    def __init__(self):
        self.enabled_services = [Service.CORREIOS]

        load_dotenv()
        self.minutes_delay = int(os.getenv("UPDATE_DELAY_MINUTES"))

    async def main_loop(self):
        remaining_time = 60 * self.minutes_delay
        logging.info(f"Parcel auto-check will start in {remaining_time} seconds.")
        while True:
            await asyncio.sleep(remaining_time)
            start_time = datetime.utcnow()
            for service in self.enabled_services:
                logging.debug("Checking for updates.")
                parcels = await Parcel.find(Parcel.service == service).to_list()
                tasks = [parcel.update_and_notify() for parcel in parcels]
                await asyncio.gather(*tasks)
            finish_time = datetime.utcnow()
            remaining_time = (self.minutes_delay * 60) - (finish_time - start_time).seconds
            logging.debug(f"Finished update cycle. Will sleep for {remaining_time} seconds.")


async def notify_users(parcel: Parcel, n_events: int):
    client = DiscordClient.instance()
    list_users = parcel.list_users
    logging.debug(f"Will update the users {list_users} about {parcel.tracking_code.upper()}.")
    list_users = [(await User.find(User.discord_id == uid).first_or_none()) for uid in list_users]
    list_calls = []
    for user in list_users:
        if user is None:
            continue

        embeds = create_package_embeds(parcel, n_events, user.mostrar_rastreio, all_in_one_page=True)
        for server in user.server_list_to_update:
            guild = client.get_guild(server)
            if guild is None:
                logging.error(f"Guild {server} not found on the Discord side.")
                continue

            server_db = await Server.find(Server.server_id == server).first_or_none()
            if server_db is None:
                logging.error(f"Guild {server} not found on database.")
                continue

            channel = guild.get_channel(server_db.updates_channel)
            if channel is None:
                logging.error(f"Channel {server_db.updates_channel} not found on the guild {server}.")
                continue

            if not user.mostrar_rastreio:
                list_calls.append(
                    channel.send(
                        content=f"<@{user.discord_id}>, o seu pacote **{user.get_parcel_name(parcel)}** foi atualizado!",
                        embed=embeds[0],
                    )
                )
            else:
                list_calls.append(
                    channel.send(
                        content=f"<@{user.discord_id}>, o seu pacote **{user.get_parcel_name(parcel)}** - **{parcel.tracking_code.upper()}** foi atualizado!",
                        embed=embeds[0],
                    )
                )

    await asyncio.gather(*list_calls)
    logging.debug(f"All users were notified about {parcel.tracking_code.upper()}.")
