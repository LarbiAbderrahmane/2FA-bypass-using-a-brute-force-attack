import httpx
from classes.CConsole import CConsole

class Client(httpx.AsyncClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    async def get(self, *args, **kwargs):
        r = await super().get(*args, **kwargs)
        assert r.status_code != 504, "make sure the Lab's URL hasn't EXPIRED !"

        return r
    
    async def post(self, *args, **kwargs):
        r = await super().post(*args, **kwargs)
        assert r.status_code != 504, "make sure the Lab's URL hasn't EXPIRED !"

        return r