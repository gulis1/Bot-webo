import aiohttp

async def getJsonResponse(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            if r.status == 200:
                lista = await r.json()
    
    return lista

async def getStringResponse(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            if r.status == 200:
                lista = await r.text()
                a = open("xD.text", mode="w")
                for x in lista:
                    try:
                        a.write(x)
                    except:
                        pass
    
    return lista
