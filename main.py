import discord
from discord.voice_client import VoiceClient
from discord.ext import commands
from discord.ext.commands import Bot
import asyncio

from lib.danbooru import sendDanbooruIm, getTagList
from lib.sauce import getSauce
from lib.music import player, sendYtRresults, getVidInfo, video, retrievePlaylist, spotifyPlaylist
from lib.httpRequests import getStringResponse
from os import listdir, remove, system, path, mkdir
from random import shuffle
from json import load as loadJson

if not path.isdir("serverAudio"):
    mkdir("serverAudio")
    
data = {}
client = commands.Bot("/")
client.remove_command("help")

with open("tokens.json") as tokens:
    token = loadJson(tokens)["discord"]

system("youtube-dl --rm-cache-dir")

MAX_SONGS = 30

@client.event
async def on_ready():
    print("Succesfully connected to Discord.")


def checkChannel(context):
    ok = True
    serverID = context.message.guild.id
    
    try:
        if context.message.author.voice.channel.guild.id != serverID:
            ok = False
    
    except AttributeError:
        ok = False
    
    return ok

@client.command(pass_context = True)
async def help(context, part = None):
    
    if part == "music":
       text = """
            •  /play <url/nombre/numero> 
            •  /playlist <playlistURL> (r)
            •  /lista
            •  /vaciar
            •  /loop <off/single/all>
            •  /skip (ind)
            •  /leave 
       """

    elif part == "danbooru":
        text = """
            •  /danbooru <tags>
            •  /tags <tags>
       """

    elif part == "sauces":
        text = """
            •  /sauce <url> 
            (Tambien se puede pasar una foto con comentario /sauce)
       """

    else:

        text = """
            •  /help music
            •  /help danbooru
            •  /help sauces
        """
    
    embed = discord.Embed(title="Help:", description = text, colour = discord.Color.green())
    await context.message.channel.send(embed=embed)

@client.command(pass_context = True)
async def danbooru(context):
    print("Command (danbooru) received.")
    channel = context.channel
    await sendDanbooruIm(context.message.content[10:], channel)

@client.command(pass_context=True)
async def tags(context):
    print("Command (danbooru) received.")
    channel = context.channel
    await getTagList(context.message.content[6:], channel)

@client.command(pass_context = True)
async def sauce(context):
    print("Command (source) received.")
    message = context.message
    channel = message.channel

    if len(message.attachments) == 0:
        await getSauce(message)
    else:
        message.content = "/sauce " + message.attachments[0].proxy_url
        await getSauce(message)
   
@client.command(pass_context = True)
async def play(context, url):
    global data
    global MAX_SONGS
    
    serverID = str(context.message.guild.id)

    if not checkChannel(context):
        embed = discord.Embed(title="Tienes que estar en un canal de voz.", colour = discord.Color.green())
        await context.message.channel.send(embed=embed)
        return

    if not str(serverID) in data.keys():
        template = {
                    "voiceClient": None,
                    "playlist": [
                        
                    ],
                    "search":[

                    ],
                    "loop": 0,
                    "currentSong": None
                }
                
    
        data[serverID] = template

    if len(data[str(serverID)]["playlist"]) > MAX_SONGS - 1:
        embed = discord.Embed(title="Ya hay 30 canciones en la playlist.", colour = discord.Color.green())
        await context.message.channel.send(embed=embed)
    
    else:
  
        if url.startswith("http"):
            # Aqui se mete si se le pasa directamente una enlace
            videoID = url[32:]
            title = await getYtTitle(videoID)

            if title == None:
                embed = discord.Embed(title="Wrong URL.", colour = discord.Color.green())
                await context.message.channel.send(embed=embed)
                return
            
            else:
                data[str(serverID)]["playlist"].append(video(videoID, title))
        
        else:
                
            try:   # Aqui se si se pone un numero para seleccionar de una busqueda
                num = int(url) - 1
                videoID = data[str(serverID)]["search"][num].id
                title = data[str(serverID)]["search"][num].title
                data[str(serverID)]["playlist"].append(video(videoID, title))
        
            except ValueError:  # Aqui se mete si se pone un nombre de una cancion
                await sendYtRresults(context, data)
                return
        
            except IndexError:
                return

        await context.message.channel.send("Cancion añadida a la playlist")

        if data[serverID]["voiceClient"] == None:
            await player(context, data)

@client.command(pass_context = True)
async def leave(context):
    serverID = str(context.message.guild.id)

    if not checkChannel(context):
        embed = discord.Embed(title="Tienes que estar en un canal de voz.", colour = discord.Color.green())
        await context.message.channel.send(embed=embed)
        return
    
    await data[serverID]["voiceClient"].disconnect()
    data[serverID]["voiceClient"] = None

@client.command(pass_context = True)
async def loop(context, msg):
    global data
    serverID = str(context.message.guild.id)

    if not checkChannel(context):
        embed = discord.Embed(title="Tienes que estar en un canal de voz.", colour = discord.Color.green())
        await context.message.channel.send(embed=embed)
        return


    if str(serverID) in data.keys():
            
        if msg == "off":
            data[serverID]["loop"] = 0
            await context.message.channel.send("Loop off.")

        elif msg == "single":
            data[serverID]["loop"] = 1           
            await context.message.channel.send("Loop set to single")
                
        elif msg == "all":
            data[serverID]["loop"] = 2
            await context.message.channel.send("Loop set to all")

@client.command(pass_context = True)
async def skip(context, ind = None):

    global data
    serverID = str(context.message.guild.id)
    
    if not checkChannel(context):
        embed = discord.Embed(title="Tienes que estar en un canal de voz.", colour = discord.Color.green())
        await context.message.channel.send(embed=embed)
        return


    if data[serverID]["loop"] == 1:
        data[serverID]["loop"] = 0
                 
    if ind != None:
     
        try:
            ind = int(ind) - 1
        except:
            return

        if ind >= 0 and ind < len(data[serverID]["playlist"]):        
            copy = video(data[str(serverID)]["playlist"][ind].id, data[serverID]["playlist"][ind].title)
            data[serverID]["playlist"].pop(ind)
            data[serverID]["playlist"].insert(0, copy)


    data[serverID]["voiceClient"].stop()
    await context.message.channel.send("Song skipped.")

@client.command(pass_context = True)
async def lista(context):
    global data

    if not checkChannel(context):
        embed = discord.Embed(title="Tienes que estar en un canal de voz.", colour = discord.Color.green())
        await context.message.channel.send(embed=embed)
        return

    serverID = str(context.message.guild.id)

    if not str(serverID) in data.keys():
        embed = discord.Embed(title="Todavía no he entrado aqui nunca", colour = discord.Color.green()) 
        await context.message.channel.send(embed=embed)
        return
    
    if data[serverID]["loop"] == 0:
        loopSetting = "off"

    elif data[serverID]["loop"] == 1:
        loopSetting = "single"

    else:
        loopSetting = "all"

       
    text = "• **Actual**: {0} \n• **Loop**: {1}\n \n".format(data[serverID]["currentSong"].title, loopSetting)
    for num, video in enumerate(data[serverID]["playlist"]):
        text += '**' + str(num+1) + ")  "  + '**' + video.title + "\n \n"
    
    embed = discord.Embed(title="Playlist:", description = text, colour = discord.Color.green()) 

    await context.message.channel.send(embed=embed)

@client.command(pass_context = True)
async def playlist(context, url, order=None):
    global MAX_SONGS
    
    textChannel = context.message.channel  
    serverID = str(context.message.guild.id)

    if not checkChannel(context):
        embed = discord.Embed(title="Tienes que estar en un canal de voz.", colour = discord.Color.green())
        await textChannel.send(embed=embed)
        return

    if not serverID in data.keys():
        template = {
                    "voiceClient": None,
                    "playlist": [
                        
                    ],
                    "search":[

                    ],
                    "loop": 0,
                    "currentSong": None
                }

        data[str(serverID)] = template
    
    if "spotify" in url:
        lista = await spotifyPlaylist(url[-22:], order)
    else:
        lista = retrievePlaylist(url[38:])
  
    cont = 0
  
    for vid in lista:
   
        if len(data[serverID]["playlist"]) < MAX_SONGS:
            vidID = vid.id
            title = vid.title
            
            data[serverID]["playlist"].append(video(vidID, title))
            cont += 1
        else:
            break


    
    embed = embed = discord.Embed(title="Se han añadido " + str(cont) + " canciones a la playlist.", colour = discord.Color.green())
    await textChannel.send(embed=embed)   

    if data[serverID]["voiceClient"] == None:
        await player(context, data)

@client.command(pass_context = True)
async def quitar(context, numero):
    global data
    
    textChannel = context.message.channel
    serverID = str(context.message.guild.id)

    if not checkChannel(context):
        embed = discord.Embed(title="Tienes que estar en un canal de voz.", colour = discord.Color.green())
        await textChannel.send(embed=embed)
        return

    try:
        numero =  int(numero)
        try:
            data[serverID]["playlist"].pop(numero-1)
            embed = embed = discord.Embed(title="Cancion quitada de la playlist", colour = discord.Color.green())
            await textChannel.send(embed=embed)
        
        except IndexError:
            await textChannel.send("Eso no esta en la playlist")

    except:
        await textChannel.send("What")

@client.command(pass_context = True)
async def vaciar(context):
    global data

    textChannel = context.message.channel
    serverID = str(context.message.guild.id)

    if not checkChannel(context):
        embed = discord.Embed(title="Tienes que estar en un canal de voz.", colour = discord.Color.green())
        await context.message.channel.send(embed=embed)
        return

    data[serverID]["playlist"].clear()

    embed = discord.Embed(title="Se ha vaciado la playlist", colour = discord.Color.green())
    await textChannel.send(embed=embed)


client.run(token)
