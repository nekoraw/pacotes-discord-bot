from beanie import Document, Indexed


class Server(Document):
    server_id: Indexed(int, unique=True)
    updates_channel: int
