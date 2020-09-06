import aiohttp

class Response():
    def __init__(self, status, content):
        self.status = status
        self.content = content


async def getJsonResponse(url):
    
    content = None
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:                 
            status = r.status
            
            if r.status == 200:   
                content = await r.json()

   
    return Response(status, content)

async def getStringResponse(url):
    content = None

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            status = r.status
            
            if r.status == 200:
                content = await r.text()
    
    return Response(status, content)



async def postJson(url, **kwargs):
    content = None

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=kwargs) as r:
            status = r.status

            if r.status == 200:
                content = await r.json()

    
    return Response(status, content)