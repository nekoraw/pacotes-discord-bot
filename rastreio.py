import logging
import hashlib
import aiohttp
from datetime import datetime, timedelta

REQUEST_TOKEN = "YW5kcm9pZDtici5jb20uY29ycmVpb3MucHJlYXRlbmRpbWVudG87RjMyRTI5OTc2NzA5MzU5ODU5RTBCOTdGNkY4QTQ4M0I5Qjk1MzU3ODs1LjEuMTQ="


class CorreiosAPI:
    _instance = None

    def __init__(self):
        self.client = aiohttp.ClientSession()
        self.token = None
        self.last_update = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def get_token(self):
        if self.last_update is not None:
            if datetime.utcnow().replace(tzinfo=None) - self.last_update < timedelta(minutes=2):
                return self.token

        request_date = (datetime.utcnow() - timedelta(hours=3)).strftime("%d/%m/%Y %H:%M:%S")
        request_sign = hashlib.md5(f"requestToken{REQUEST_TOKEN}data{request_date}".encode('ascii')).hexdigest()

        response = await self.client.request(
            "POST",
            "https://proxyapp.correios.com.br/v1/app-validation",
            headers={"content-type": "application/json", "user-agent": "Dart/3.0 (dart:io)"},
            json={"requestToken": REQUEST_TOKEN, "data": request_date, "sign": request_sign},
        )

        if response.status != 201:
            logging.error(f"Algo deu errado na requisição dos Correios:\n{response.status}: {response.content}")
            return None

        self.token = (await response.json()).get("token", None)
        self.last_update = datetime.utcnow().replace(tzinfo=None)
        return self.token

    async def get_pacote(self, code: str):
        code = code.upper()
        token = await self.get_token()

        response = await self.client.request(
            "GET",
            f"https://proxyapp.correios.com.br/v1/sro-rastro/{code}",
            headers={"content-type": "application/json", "user-agent": "Dart/2.18 (dart:io)", "app-check-token": token},
        )

        if response.status != 200:
            logging.error(f"Algo deu errado na requisição dos Correios:\n{response.status}: {response.content}")
            return None

        return (await response.json())["objetos"][0]
