import logging
from datetime import datetime, timedelta
from uuid import uuid4

from beanie import Document, Indexed

from schema.services import Service
from rastreio import CorreiosAPI


class Parcel(Document):
    internal_id: Indexed(str, unique=True)
    tracking_code: Indexed(str)
    service: Service
    data: dict
    n_updates: int = 0
    last_update: str
    is_delivered: bool
    list_users: list = []

    async def update_and_notify(self):
        logging.debug(f"Updating parcel {self.tracking_code.upper()}.")
        if self.is_delivered:
            logging.debug(f"No need to update {self.tracking_code.upper()} because it's delivered.")
            return
        from events import notify_users

        n_updates_before = self.n_updates
        await self.update_parcel()
        diff = self.n_updates - n_updates_before
        if diff <= 0:
            logging.debug(f"No new updates for {self.tracking_code.upper()}.")
            return
        await notify_users(self, diff)

    async def update_parcel(self):
        match self.service:
            case Service.CORREIOS:
                correios_api = CorreiosAPI.instance()
                package = await correios_api.get_pacote(self.tracking_code)
                if package is not None:
                    if "eventos" in package:
                        self.data = package
                        self.n_updates = len(package["eventos"])
                        self.last_update = (datetime.utcnow() - timedelta(hours=3)).isoformat()
                        if "Objeto entregue ao destinatário".lower() in package["eventos"][0]["descricao"].lower():
                            self.is_delivered = True
                    await self.save()
                return self
            case _:
                return None

    @staticmethod
    async def update_parcel_without_save(service: Service | None, code: str):
        code = code.lower()
        match service:
            case Service.CORREIOS:
                correios_api = CorreiosAPI.instance()
                package = await correios_api.get_pacote(code)
                result = None
                if package is None:
                    result = await Parcel.find(
                        Parcel.tracking_code == code and Parcel.service == Service.CORREIOS
                    ).first_or_none()
                if result is None:
                    delivered = False
                    n_updates = 0
                    if package is not None:
                        if "eventos" in package:
                            n_updates = len(package["eventos"])
                            if "Objeto entregue ao destinatário".lower() in package["eventos"][0]["descricao"].lower():
                                delivered = True
                    result = Parcel(
                        internal_id=str(uuid4()),
                        tracking_code=code,
                        service=service,
                        data=package,
                        last_update=(datetime.utcnow() - timedelta(hours=3)).isoformat(),
                        is_delivered=delivered,
                        n_updates=n_updates
                    )
                return result
            case _:
                return None
