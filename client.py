import os
import sys
from datetime import datetime

import discord
import aiohttp
import json
import logging


class CustomFormatter(logging.Formatter):

    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(levelname)s | %(asctime)s | %(message)s"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


if not os.path.exists("./logs"):
    os.mkdir("logs")
file_handler = logging.FileHandler(f"logs/pacotes_{datetime.utcnow().isoformat()}.log")
file_handler.setFormatter(logging.Formatter("%(levelname)s | %(asctime)s | %(message)s"))
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(CustomFormatter())
logging.basicConfig(level=10, handlers=[file_handler, console_handler])


class DiscordClient:
    _instance = None

    def __init__(self):
        self.client = discord.Bot()

    @classmethod
    def instance(cls) -> discord.Bot:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance.client


all_emojis = {
    "revisao-tributos-cor.png": "revisaotributoscor",
    "aguardando-pagamento.png": "aguardandopagamento",
    "enviar-encomenda-cor.png": "enviarencomendacor",
    "img": "correiossf",
    "smile.png": "receberencomendacor",
    "receber-encomenda-cor.png": "receberencomendacor",
    "pre-atendimento-cor.png": "preatendimentocor",
    "verificar-documento-cor.png": "verificardocumentocor",
    "brazil.png": "brazil",
    "agencia-cor.png": "agenciacor",
    "caminhao-cor.png": "caminhaocor",
    "fatura-paga.png": "faturapaga",
    "devolucao-encomenda-cor.png": "devolucaoencomendacor",
    "logistica-reversa-cor.png": "logisticareversacor",
    "cdd-cor.png": "cddcor",
    "not_found": "misterio",
}


async def add_emojis(client: discord.Bot):
    n_emojis = len(all_emojis)
    guilds = client.guilds
    available_guilds = []
    for guild in guilds:
        if guild.emoji_limit - len(guild.emojis) >= n_emojis:
            available_guilds.append(guild)

    logging.info("Selecione um servidor para adicionar os emojis:")
    logging.info(f"São necessários {n_emojis} para o funcionamento completo do bot.")
    for i, guild in enumerate(available_guilds):
        logging.info(f"[{i}] - {guild.name} | {len(guild.emojis)}/{guild.emoji_limit} emojis")

    while True:
        logging.info("Selecione o ID do servidor: ")
        server_index = input()
        try:
            selected_guild = available_guilds[int(server_index)]
            break
        except (IndexError, ValueError):
            logging.warning("Selecione um índice existente.")

    session = aiohttp.ClientSession()
    created_emojis = {
        "revisao-tributos-cor.png": "",
        "aguardando-pagamento.png": "",
        "enviar-encomenda-cor.png": "",
        "img": "",
        "smile.png": "",
        "receber-encomenda-cor.png": "",
        "pre-atendimento-cor.png": "",
        "verificar-documento-cor.png": "",
        "brazil.png": "",
        "agencia-cor.png": "",
        "caminhao-cor.png": "",
        "fatura-paga.png": "",
        "devolucao-encomenda-cor.png": "",
        "logistica-reversa-cor.png": "",
        "cdd-cor.png": "",
        "not_found": "",
    }
    for emoji, name in all_emojis.items():
        if emoji == "not_found":
            icon_url = "https://nekoraw.s-ul.eu/EmFkykmZ"
        elif emoji != "img":
            icon_url = f"https://rastreamento.correios.com.br/static/rastreamento-internet/imgs/{emoji}"
        else:
            icon_url = "https://rastreamento.correios.com.br/static/rastreamento-internet/imgs/correios-sf.png"

        response = await session.get(url=icon_url)
        data = await response.read()
        added_emoji = await selected_guild.create_custom_emoji(name=name, image=data)
        created_emojis[emoji] = f"<:{added_emoji.name}:{added_emoji.id}>"

    await session.close()
    with open("emojis.json", "w") as f:
        json.dump(created_emojis, f, indent=4)

    logging.info("Emojis adicionados. Você pode omitir o argumento `emojis` na próxima vez que abrir o bot.")
    logging.warning("Os emojis serão exibidos somente após a próxima inicialização do bot.")
