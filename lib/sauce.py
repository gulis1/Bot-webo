import discord
from .httpRequests import getJsonResponse
from json import load as loadJson

#SauceNao api info

with open("tokens.json") as tokens:
    api_key = loadJson(tokens)["sauceNao"]

api_call = "https://saucenao.com/search.php?output_type=2&api_key={0}&url={1}"

async def getSauce(message):

    channel = message.channel

    url = message.content[7:]

    response = await getJsonResponse(api_call.format(api_key, url))

    if response.status != 200:
        embed = discord.Embed(title="Error desconocido.", colour = discord.Color.green())
        await message.channel.send(embed=embed)
        return
    
    elif response.content["header"]["status"] == -3:
        embed = discord.Embed(title="Eso no parece una imagen.", colour = discord.Color.green())
        await message.channel.send(embed=embed)
        return

    elif response.content["header"]["status"] == 0:
        embed = discord.Embed(title="Sources:", colour = discord.Color.green())
        cont = 1
        for ocurrence in response.content["results"]:        
            msg = ""      
            if float(ocurrence["header"]["similarity"]) >= 65:
                
                keys = ocurrence["data"].keys()
                for tag in keys:
                    if type(ocurrence["data"][tag]) == list:
                        msg += tag + ": " + str(ocurrence["data"][tag][0]) + "\n"
                    else:
                        msg += tag + ": " + str(ocurrence["data"][tag]) + "\n"
                
                embed.add_field(name=str(cont) +")", value=msg, inline=False)
                cont += 1
        
        if cont > 1:
            await channel.send(embed=embed)

        else:
            embed = discord.Embed(title="No se ha encontrado nada relevante.", colour = discord.Color.green())
            await message.channel.send(embed=embed)
            return

    

    else:
        embed = discord.Embed(title="No se ha encotrado nada", colour = discord.Color.green())
        await message.channel.send(embed=embed)
        return