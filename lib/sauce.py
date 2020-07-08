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

    err = 0

    try:
        prueba = response["results"][0].keys()
    except:
        err = 1

    embed = discord.Embed(title="Sources:", colour = discord.Color.green())

    
    if err == 0:
        try:
            
            counter = 1
            for ocurrence in response["results"]:
                
                msg = ""      
                if float(ocurrence["header"]["similarity"]) >= 65:
                    
                    keys = ocurrence["data"].keys()
                    for tag in keys:
                        if type(ocurrence["data"][tag]) == list:
                            msg += tag + ": " + str(ocurrence["data"][tag][0]) + "\n"
                        else:
                            msg += tag + ": " + str(ocurrence["data"][tag]) + "\n"
                    embed.add_field(name=str(counter) +")", value=msg, inline=False)                
                    counter += 1

        
            
            await channel.send(embed=embed)
            print("Succesfully found source. Message sent.")
            
       

        except KeyError:
            err = 2


    if err == 1:
        embed.clear_fields()
        embed.description = "Invalid image."       
        await channel.send(embed=embed)
        print("Unsuccesfully found source (Invalid image). Message sent.")
        
    elif err == 2:
        embed.clear_fields()
        embed.description = "No relevant results."
        await channel.send(embed=embed)
        print("Unsuccesfully found source (No relevant results). Message sent.")