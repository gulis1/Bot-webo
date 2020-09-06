from .httpRequests import postJson
import discord
import aiohttp
import asyncio
import json
from datetime import timedelta

url = 'https://graphql.anilist.co'

async def timeUntilAiring(title, channel):
    global url

    query = '''
    query($name: String) {
    Media (search: $name, type: ANIME) {
    id
    episodes
    nextAiringEpisode{
        timeUntilAiring
        episode
    }
    title {
    romaji
    }

    }
    }
    '''


    variables = {
        'name': title
    }

    response = await postJson(url, query=query, variables=variables)

    embed = discord.Embed(colour = discord.Color.green(), description="asds")
    embed.description = "sss"

    if response.status == 200:

        if response.content["data"]["Media"] is None:
            embed.title = "No existe ese anime."

        elif response.content["data"]["Media"]["nextAiringEpisode"] is None:
            embed.title = response.content["data"]["Media"]["title"]["romaji"]
            embed.description = "Ese anime ya ha terminado. ({0} episodios)".format(response.content["data"]["Media"]["episodes"])

        else:
            embed.title = response.content["data"]["Media"]["title"]["romaji"]
            time = timedelta(seconds = response.content["data"]["Media"]["nextAiringEpisode"]["timeUntilAiring"])
            embed.description = "El episodio **{0}** sale en **{1}**".format(response.content["data"]["Media"]["nextAiringEpisode"]["episode"], time)

    await channel.send(embed=embed)
