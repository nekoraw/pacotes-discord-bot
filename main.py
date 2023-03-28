import sys
import discord
from beanie import init_beanie
from discord.ext import pages
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from client import DiscordClient, add_emojis
from events import ParcelChecking
from schema.services import Service
from schema.server import Server
from schema.user import User
from schema.parcel import Parcel
import re
import os
from embed import create_package_embeds, get_all_parcels_embeds
from view import DeleteMessageView
import logging

if not os.path.exists("./emojis.json"):
    if len(sys.argv) < 2:
        logging.warning(f"Execute o bot com `{sys.executable} {sys.argv[0]} emojis` para adicionar os emojis ao bot.")
        exit()
client = DiscordClient.instance()
load_dotenv()


def get_service_from_tracking_number(code: str):
    if re.findall(r"[A-Za-z]{2}[0-9]{9}[A-Za-z]{2}", code):
        return Service.CORREIOS
    else:
        return None


@client.event
async def on_ready() -> None:
    """Function that determines what to do when the bot is ready."""
    b_client = AsyncIOMotorClient(os.getenv("MONGODB_CONNECTION_URI"))
    await init_beanie(database=getattr(b_client, os.getenv("DATABASE_NAME")), document_models=[User, Server, Parcel])

    logging.info("We have logged in as {0.user}".format(client))
    logging.info(
        "Invite the bot: https://discord.com/api/oauth2/authorize?client_id="
        "{0.user.id}&permissions=1074022400&scope=bot%20applications.commands".format(client)
    )
    if len(sys.argv) > 1:
        if sys.argv[1] == "emojis":
            if os.path.exists("./emojis.json"):
                logging.warning("Emojis já adicionados. Delete emojis.json caso quiser reconfigurar os emojis.")
            else:
                await add_emojis(client)
    parcel_autocheck = ParcelChecking()
    await parcel_autocheck.main_loop()


@client.event
async def on_guild_join(guild: discord.Guild) -> None:
    server = await Server.find(Server.server_id == guild.id).first_or_none()

    channel = guild.system_channel
    if channel is None:
        channel = guild.text_channels[0]

    if channel.can_send():
        await channel.send(f"Obrigado por convidar o {client.user.name}!")
        if not server:
            await channel.send(
                "Para começar a usar o bot, primeiro é necessário que algum administrador configure um canal para receber atualizações de pacotes usando o comando `/canal_de_pacotes`."
            )
        else:
            if server.updates_channel not in guild.channels:
                await server.delete()
                await channel.send(
                    "Aparentemente o canal antigo de atualizações não existe mais. É necessário que algum administrador configure um canal para receber atualizações de pacotes usando o comando `/canal_de_pacotes`."
                )


@client.slash_command(description="Define o canal atual como o canal de atualização de pacotes.", guild_only=True)
@discord.default_permissions(administrator=True)
async def canal_de_pacotes(ctx: discord.ApplicationContext):
    await ctx.defer()
    server = await Server.find(Server.server_id == ctx.guild.id).first_or_none()

    if server is None:
        server = Server(server_id=ctx.guild_id, updates_channel=ctx.channel_id)
    else:
        server.updates_channel = ctx.channel_id
    await server.save()
    await ctx.respond(
        "Canal definido. Atualizações de pacotes chegarão aqui.\n\nVerifique se o bot possui as seguintes permissões neste canal:\n- Enviar Mensagens\n- Enviar Links\n- Usar emojis externos.\nCaso não ter essas permissões, algumas funcionalidades podem não funcionar corretamente."
    )


@client.slash_command(description="Rastreia um pacote.")
@discord.option(
    "nome",
    str,
    required=False,
    autocomplete=User.get_parcels_autocomplete,
    description="O nome do pacote que você adicionou anteriormente.",
)
@discord.option("codigo", str, required=False, description="O código de rastreio da encomenda.")
@discord.option(
    "visivel",
    str,
    choices=["Sim", "Não"],
    default="Não",
    description="O seu código de rastreio também será visível caso a mensagem for.",
)
async def rastreia(ctx: discord.ApplicationContext, nome, codigo, visivel):
    us = await User.get_user(ctx.user.id)
    ephemeral = False if visivel == "Sim" else True
    await ctx.defer(ephemeral=ephemeral)

    if not nome and not codigo:
        await ctx.respond("Você deve preencher ao menos uma opção.")
        return

    if nome and codigo:
        await ctx.respond("Não é necessário preencher as duas opções. Somente o nome ou somente o código de rastreio.")
        return

    page_buttons = [
        pages.PaginatorButton("prev", label="<-", style=discord.ButtonStyle.green),
        pages.PaginatorButton("page_indicator", style=discord.ButtonStyle.gray, disabled=True),
        pages.PaginatorButton("next", label="->", style=discord.ButtonStyle.green),
    ]

    if codigo:
        service = get_service_from_tracking_number(codigo)
        rastreio = await Parcel.update_parcel_without_save(service, codigo)
        embeds = create_package_embeds(rastreio, show_tracking_number=True)
        if len(embeds) == 0:
            await ctx.respond(content="Nenhum dado? Que estranho.")
        elif len(embeds) == 1:
            await ctx.respond(embed=embeds[0])
        else:
            paginator = pages.Paginator(
                pages=embeds, custom_buttons=page_buttons, use_default_buttons=False, show_indicator=True
            )
            await paginator.respond(ctx.interaction, ephemeral=ephemeral)
    elif nome:
        package = await Parcel.find(Parcel.internal_id == us.parcels[nome]).first_or_none()
        embeds = create_package_embeds(package, show_tracking_number=True)
        if len(embeds) == 0:
            await ctx.respond(content="Nenhum dado? Que estranho.")
        elif len(embeds) == 1:
            await ctx.respond(embed=embeds[0])
        else:
            paginator = pages.Paginator(
                pages=embeds, custom_buttons=page_buttons, use_default_buttons=False, show_indicator=True
            )
            await paginator.respond(ctx.interaction, ephemeral=ephemeral)


@client.slash_command(description="Adiciona um pacote ao rastreio de encomendas.")
@discord.option("nome", str, description="O nome do pacote que você quer adicionar.")
@discord.option("codigo", str, description="O código de rastreio da encomenda.")
async def adiciona(ctx: discord.ApplicationContext, nome, codigo):
    codigo = codigo.lower()
    us = await User.get_user(ctx.user.id)
    ephemeral = not us.mostrar_rastreio
    await ctx.defer(ephemeral=ephemeral)

    if nome in us.parcels.keys():
        await ctx.respond("Você já adicionou um pacote com esse nome.")
        return

    for k, v in us.parcels.items():
        parcel = await Parcel.find(Parcel.internal_id == v).first_or_none()
        if k == nome and parcel.tracking_code == codigo:
            await ctx.respond("Você já adicionou um pacote com esse número de rastreio.")
            return

    service = get_service_from_tracking_number(codigo)
    if service is None:
        await ctx.respond("Código no formato incorreto.")
        return

    parcel = await Parcel.find({"$and": [{"tracking_code": codigo}, {"service": service}]}).first_or_none()
    if parcel is None:
        parcel = await Parcel.update_parcel_without_save(service, codigo)
    else:
        await ctx.respond("Pacote já adicionado anteriormente.")
        return

    if ctx.user.id not in parcel.list_users:
        parcel.list_users.append(ctx.user.id)
    await parcel.save()

    us.parcels[nome] = parcel.internal_id
    await us.save()

    await ctx.respond(
        "Pacote adicionado com sucesso! Envie `/lista` para ver todos os seus pacotes. Caso desejar receber atualizações de pacotes nesse servidor, envie `/me_atualize_aqui`."
    )


@client.slash_command(description="Remove um pacote do rastreio de encomendas.")
@discord.option(
    "nome",
    str,
    autocomplete=User.get_parcels_autocomplete,
    description="O nome do pacote que você adicionou anteriormente.",
)
async def remove(ctx: discord.ApplicationContext, nome):
    us = await User.get_user(ctx.user.id)
    ephemeral = not us.mostrar_rastreio
    await ctx.defer(ephemeral=ephemeral)

    if nome not in us.parcels.keys():
        await ctx.respond("Você não adicionou esse pacote ao rastreio.")
        return

    parcel = await Parcel.find(Parcel.internal_id == us.parcels[nome]).first_or_none()
    if parcel is None:
        await ctx.respond("Pacote não encontrado. Ele deveria ter sido. Algo errado aconteceu.")
        return

    parcel.list_users.remove(ctx.user.id)
    if len(parcel.list_users) == 0:
        await parcel.delete()
    else:
        await parcel.save()

    us.parcels.pop(nome)
    await us.save()

    await ctx.respond("Pacote removido com sucesso. Envie `/lista` para ver todos os seus pacotes.")


@client.slash_command(
    description="Adiciona esse servidor à lista de servidores em que você quer receber atualização de pacotes.",
    guild_only=True,
)
async def me_atualize_aqui(ctx: discord.ApplicationContext):
    us = await User.get_user(ctx.user.id)
    await ctx.defer(ephemeral=True)

    if ctx.guild_id in us.server_list_to_update:
        await ctx.respond("Você já está recebendo atualizações nesse servidor!")
        return

    us.server_list_to_update.append(ctx.guild_id)
    await us.save()
    await ctx.respond(
        "A partir de agora você irá receber atualização de encomendas aqui. Por padrão, o seu código de rastreio não irá aparecer, mas você pode mudar isso com o `/mostrar_codigo_rastreio`."
    )


@client.slash_command(
    description="Remove esse servidor da lista de servidores em que você quer receber atualização de pacotes.",
    guild_only=True,
)
async def nao_me_atualize_aqui(ctx: discord.ApplicationContext):
    us = await User.get_user(ctx.user.id)
    await ctx.defer(ephemeral=True)

    if ctx.guild_id not in us.server_list_to_update:
        await ctx.respond("Você não está recebendo atualizações nesse servidor!")
        return

    us.server_list_to_update.remove(ctx.guild_id)
    await us.save()
    await ctx.respond("Você não irá mais receber atualizações de encomendas nesse servidor.")


@client.slash_command(
    description="Faz com que as mensagens do bot contenham os seus códigos de rastreio visível a todos.",
    guild_only=True,
)
async def mostrar_codigo_rastreio(ctx: discord.ApplicationContext):
    us = await User.get_user(ctx.user.id)
    await ctx.defer(ephemeral=True)

    if us.mostrar_rastreio:
        await ctx.respond("O seu código de rastreio já está sendo exibido!")
        return

    us.mostrar_rastreio = True
    await us.save()
    await ctx.respond("O seu código de rastreio agora é sempre visível em mensagens do bot.")


@client.slash_command(
    description="Faz com que as mensagens do bot não mostrem os seus códigos de rastreio.", guild_only=True
)
async def nao_mostrar_codigo_rastreio(ctx: discord.ApplicationContext):
    us = await User.get_user(ctx.user.id)
    await ctx.defer(ephemeral=True)

    if not us.mostrar_rastreio:
        await ctx.respond("O seu código de rastreio já está escondido!")
        return

    us.mostrar_rastreio = False
    await us.save()
    await ctx.respond("O seu código de rastreio não aparecerá em mensagens futuras do bot..")


@client.slash_command(description="Mostra todas as encomendas que você possui.")
@discord.option(
    "mostrar_entregues",
    str,
    choices=["Sim", "Não"],
    default="Sim",
    description="Irá mostrar os pacotes entregues na lista.",
)
async def lista(ctx: discord.ApplicationContext, mostrar_entregues):
    us = await User.get_user(ctx.user.id)
    await ctx.defer()

    if mostrar_entregues == "Sim":
        mostrar_entregues = True
    else:
        mostrar_entregues = False

    a_pages = await get_all_parcels_embeds(us, ctx, mostrar_entregues)
    if len(a_pages) == 0:
        await ctx.respond(
            content="Nenhuma encomenda encontrada! Você pode adicionar uma nova com `/adicionar`",
            view=DeleteMessageView(),
        )
    elif len(a_pages) == 1:
        await ctx.respond(embed=a_pages[0], view=DeleteMessageView())
    else:
        page_buttons = [
            pages.PaginatorButton("prev", label="<-", style=discord.ButtonStyle.green),
            pages.PaginatorButton("page_indicator", style=discord.ButtonStyle.gray, disabled=True),
            pages.PaginatorButton("next", label="->", style=discord.ButtonStyle.green),
        ]
        paginator = pages.Paginator(
            pages=a_pages,
            custom_view=DeleteMessageView(),
            custom_buttons=page_buttons,
            use_default_buttons=False,
            show_indicator=True,
        )
        await paginator.respond(ctx.interaction)


client.run(os.getenv("DISCORD_TOKEN"))
