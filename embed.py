import asyncio
import json
import logging
import math
import os

import discord
import discord.utils
from datetime import datetime

from dotenv import load_dotenv

from schema.services import Service
from schema.user import User
from schema.parcel import Parcel

load_dotenv()
parcels_per_page = int(os.getenv("PARCELS_PER_PAGE"))
updates_per_page = int(os.getenv("UPDATES_PER_PAGE"))

all_emojis = {}
if os.path.exists("./emojis.json"):
    with open("emojis.json", "r") as f:
        all_emojis = json.load(f)


def parse_correios_evento(event: dict):
    logging.debug(event)
    title = f"**{event['descricao']}**"
    emoji = all_emojis.get(event["urlIcone"].split("/")[-1], None)
    if emoji is not None:
        title = f"{emoji} - {title}"
    else:
        logging.error(f"emoji {event['urlIcone'].split('/')[-1]} nao encontrado.")

    if "unidadeDestino" in event:
        description = (
            f"de {parse_correios_unidade(event['unidade'])} para {parse_correios_unidade(event['unidadeDestino'])}"
        )
    else:
        description = f"em {parse_correios_unidade(event['unidade'])}"

    time = discord.utils.format_dt(datetime.fromisoformat(event["dtHrCriado"]))

    return title, description + "\n" + time


def parse_correios_unidade(unidade: dict):
    if unidade["tipo"] == "País":
        if unidade["endereco"]:
            return f"{unidade['nome']}/{unidade['endereco']['uf']}"
        return unidade["nome"]
    elif unidade["tipo"] == "IPS":
        return f"{unidade['tipo']}: {unidade['nome']} em {unidade['endereco']['uf']}"
    else:
        return f"{unidade['tipo']} em {unidade['endereco']['cidade']}/{unidade['endereco']['uf']}"


def create_package_embeds(
    parcel: Parcel, n_events: int = 0, show_tracking_number: bool = False, all_in_one_page: bool = False
):
    if parcel is not None:
        service = parcel.service
    else:
        service = None
    match service:
        case Service.CORREIOS:
            if "eventos" not in parcel.data:
                embed = discord.Embed(
                    color=discord.Color.from_rgb(255, 212, 0),
                    title="Objeto não encontrado.",
                    description=parcel.data["mensagem"],
                )
                embed.set_thumbnail(url="https://nekoraw.s-ul.eu/EmFkykmZ")
                return [embed]

            if n_events == 0:
                n_events = len(parcel.data["eventos"])

            n_pages = math.ceil(n_events / updates_per_page)
            if all_in_one_page:
                n_pages = 1
            list_pages = []

            for page in range(n_pages):
                if show_tracking_number:
                    embed = discord.Embed(
                        color=discord.Color.from_rgb(255, 212, 0),
                        title=parcel.data["codObjeto"],
                        url=f"https://www.muambator.com.br/pacotes/{parcel.data['codObjeto']}/detalhes/",
                    )
                else:
                    embed = discord.Embed(color=discord.Color.from_rgb(255, 212, 0), title="Encomenda dos Correios")

                icon_name = parcel.data["eventos"][0]["urlIcone"].split("/")[-1]
                if icon_name != "img":
                    icon_url = f"https://rastreamento.correios.com.br/static/rastreamento-internet/imgs/{icon_name}"
                else:
                    icon_url = "https://rastreamento.correios.com.br/static/rastreamento-internet/imgs/correios-sf.png"

                embed.set_thumbnail(url=icon_url)
                date = datetime.fromisoformat(parcel.last_update).strftime("%d/%m/%Y %H:%M")
                embed.set_footer(
                    text=f"Última atualização do bot: {date}",
                    icon_url="https://rastreamento.correios.com.br/static/rastreamento-internet/imgs/receber-encomenda-cor.png",
                )

                if all_in_one_page:
                    for event in parcel.data["eventos"][: max(min(n_events, updates_per_page), 1)]:
                        title, description = parse_correios_evento(event)
                        embed.add_field(name=title, value=description, inline=False)
                else:
                    for event in parcel.data["eventos"][
                        updates_per_page * page : (updates_per_page * page) + updates_per_page
                    ]:
                        title, description = parse_correios_evento(event)
                        embed.add_field(name=title, value=description, inline=False)

                list_pages.append(embed)

            return list_pages
        case _:
            embed = discord.Embed(
                color=discord.Color.from_rgb(255, 212, 0),
                title="Objeto não encontrado.",
                description="Verifique se o código que você providenciou está correto.",
            )
            embed.set_thumbnail(url="https://nekoraw.s-ul.eu/EmFkykmZ")
            return [embed]


async def get_all_parcels_embeds(us: User, ctx: discord.ApplicationContext, mostrar_entregues: bool = True):
    n_pages = math.ceil(len(us.parcels.items()) / parcels_per_page)
    list_pages = []
    for page in range(n_pages):
        possible_names = []
        if hasattr(ctx.user, "name"):
            possible_names.append(ctx.user.name)
        if hasattr(ctx.user, "nick"):
            possible_names.append(ctx.user.nick)
        username = "Usuário"
        for name in possible_names:
            if name is not None:
                username = name
                break
        embed = discord.Embed(color=discord.Color.from_rgb(255, 212, 0), title=f"Encomendas de {username}")

        embed.set_thumbnail(url=ctx.user.avatar.url)

        footer_text = f"Somente uma encomenda." if len(us.parcels) == 1 else f"Total de {len(us.parcels)} encomendas."
        embed.set_footer(
            text=footer_text,
            icon_url="https://rastreamento.correios.com.br/static/rastreamento-internet/imgs/receber-encomenda-cor.png",
        )

        if mostrar_entregues:
            list_parcels = [
                await Parcel.find({"internal_id": parcel_uid}).first_or_none()
                for parcel_uid in list(us.parcels.values())
            ]
        else:
            list_parcels = [
                    await Parcel.find(
                        {"$and": [{"internal_id": parcel_uid}, {"is_delivered": mostrar_entregues}]}
                    ).first_or_none()
                for parcel_uid in list(us.parcels.values())
            ]

        available_parcels = []
        for parcel in list_parcels:
            if parcel is None:
                continue
            available_parcels.append(parcel)

        for parcel in available_parcels[parcels_per_page * page : (parcels_per_page * page) + parcels_per_page]:
            match parcel.service:
                case Service.CORREIOS:
                    await parcel.update_parcel()
                    parcel_name = us.get_parcel_name(parcel=parcel)
                    if "eventos" not in parcel.data:
                        if us.mostrar_rastreio:
                            embed.add_field(
                                name=f"**{parcel_name} - {parcel.tracking_code.upper()} - Correios**",
                                value=f"**{all_emojis['not_found']} - Objeto não encontrado.**\n"
                                + parcel.data["mensagem"],
                                inline=False,
                            )
                        else:
                            embed.add_field(
                                name=f"**{parcel_name} - Correios**",
                                value=f"**{all_emojis['not_found']} - Objeto não encontrado.**\n"
                                + parcel.data["mensagem"],
                                inline=False,
                            )
                        continue
                    logging.debug(parcel.tracking_code)
                    title, description = parse_correios_evento(parcel.data["eventos"][0])
                    if us.mostrar_rastreio:
                        embed.add_field(
                            name=f"**{parcel_name} - {parcel.tracking_code.upper()} - Correios**",
                            value=title + "\n" + description,
                            inline=False,
                        )
                    else:
                        embed.add_field(
                            name=f"**{parcel_name} - Correios**", value=title + "\n" + description, inline=False
                        )
                case _:
                    embed.add_field(
                        name=f"{all_emojis['not_found']} - Objeto não encontrado.",
                        value="Verifique se o código que você providenciou está correto.",
                        inline=False,
                    )
        list_pages.append(embed)

    return list_pages
