import discord
import requests
from .httpRequests import getJsonResponse

async def sendRandIm(tag, channel):
    tag = tag.replace(" ", "_")

    response = await getJsonResponse("https://danbooru.donmai.us/posts/random.json?tags=" + tag)

    try:
        url = response.content["file_url"]
    except KeyError:
        await sendRandIm(tag, channel)
        return
    
    embed = discord.Embed(colour=discord.Color.green())
    embed.set_image(url=url)
    
    await channel.send(embed=embed)


async def getTagList(tag, channel):
    
    response = await getJsonResponse("https://danbooru.donmai.us/tags.json?search[order]=count&search[name_or_alias_matches]="+tag+"*")
    lista = response.content
    mensaje = ""
    
    for elem in lista:
        mensaje += "  - " + elem["name"] + "\n"

    embed = discord.Embed(title="Lista de tags:", colour=discord.Color.green())
    embed.description = mensaje
    
    await channel.send(embed=embed)
    print("Tag not found, possible matches list sent.")

async def sendDanbooruIm(tag, channel):

    response = await getJsonResponse("https://danbooru.donmai.us/tags.json?search[name_or_alias_matches]="+tag)
    
    lista = response.content

    if len(lista) == 0:
        await getTagList(tag, channel)
    
    else:
        await sendRandIm(tag, channel)