#!/usr/bin/python3
import discord
from discord.voice_client import VoiceClient
from discord.ext import commands
from discord.ext.commands import Bot
import asyncio

from lib.danbooru import sendDanbooruIm, getTagList
from lib.sauce import getSauce
from lib.music import player, sendYtRresults, getVidInfo, video, retrievePlaylist, spotifyPlaylist, template, spotifyAlbum
from os import listdir, remove, system, path, mkdir
from json import load as loadJson
import re
from lib.animeStuff import timeUntilAiring


data = {}

with open("tokens.json") as tokens:
    token = loadJson(tokens)["discord"]

client = commands.Bot("/")
client.remove_command("help")

system("youtube-dl --rm-cache-dir")

MAX_SONGS = 30

async def userConnectedToGuildVoice(context):
    serverID = context.message.guild.id

    if context.message.author.voice != None and context.message.author.voice.channel.guild.id == serverID:
        return True

    else:
        embed = discord.Embed(title="Tienes que estar en un canal de voz de este server.", colour = discord.Color.green())
        await context.message.channel.send(embed=embed)
        return False

async def botIsConnectedToGuildVoice(context):
    global data
    serverID = str(context.message.guild.id)

    if serverID not in data.keys() or data[serverID]["voiceClient"] == None:
        embed = discord.Embed(title="Ahora mismo no estoy metido aquí.", colour = discord.Color.green())
        await context.message.channel.send(embed=embed)
        return False

    else:
        return True

# Image commands
@client.event
async def on_ready():
    print("Succesfully connected to Discord.")

@client.command()
async def ping(ctx):
    await ctx.send(f'pong {round(client.latency * 1000)}ms')

@client.command(pass_context = True)
async def help(context, part = None):
    
    if part == "music":
       text = """
            •  /play <url/nombre/numero> (r) (Funciona con videos y playlists de youtube, y albumes y playlists de spotify)
            •  /lista
            •  /song
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

    elif part == "anime":
        text = """
        •  /anime <nombre>
    """

    else:

        text = """
            •  /help music
            •  /help danbooru
            •  /help sauces
            •  /help anime
        """
    
    embed = discord.Embed(title="Help:", description = text, colour = discord.Color.green())
    await context.message.channel.send(embed=embed)

@client.command(pass_context = True)
async def danbooru(context):

    channel = context.channel
    await sendDanbooruIm(context.message.content[10:], channel)

@client.command(pass_context=True)
async def tags(context):

    channel = context.channel
    await getTagList(context.message.content[6:], channel)

@client.command(pass_context = True)
async def sauce(context):
    message = context.message

    if len(message.attachments) == 0:
        await getSauce(message)
    else:
        message.content = "/sauce " + message.attachments[0].proxy_url
        await getSauce(message)

#Anime commands

@client.command(pass_context = True)
async def anime(context):
    channel = context.message.channel
    title = context.message.content[6:]
    try: 
        await timeUntilAiring(title, channel)
    except:
        pass

# Music commands
@commands.guild_only()
@commands.check(userConnectedToGuildVoice)
@client.command(pass_context = True)
async def play(context, arg, order = None):
    global data
    global MAX_SONGS

    serverID = str(context.message.guild.id)
 
    if not str(serverID) in data.keys():  
        data[serverID] = template


    if len(data[str(serverID)]["playlist"]) > MAX_SONGS - 1:
        embed = discord.Embed(title="Ya hay 30 canciones en la playlist.", colour = discord.Color.green())
        await context.message.channel.send(embed=embed)
    
    else:

        if arg.startswith("http"):
            # Aqui se mete si se le pasa directamente un enlace
            videoID = re.search("(youtu\.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=)([^#\&\?]*)", arg)
            if videoID != None:
            
                vidInfo = await getVidInfo(videoID[2])      
                
                if vidInfo == None:
                    embed = discord.Embed(title="Wrong URL.", colour = discord.Color.green())
                    await context.message.channel.send(embed=embed)
                    return
                
                else:               
                    title = vidInfo["title"]
                    duration = vidInfo["duration"]          
                    data[str(serverID)]["playlist"].append(video(videoID[2], title, duration=duration))

            else:
                await playlist(context, arg, order=order)
                return
        
        elif arg.isnumeric():
            num = int(arg) - 1
            try:
                videoID = data[str(serverID)]["search"][num].id
                title = data[str(serverID)]["search"][num].title
                duration = data[str(serverID)]["search"][num].duration
                data[str(serverID)]["playlist"].append(video(videoID, title, duration=duration))
            
            except IndexError:
                return

        else:  # Aqui se mete si se pone un nombre de una cancion
            await sendYtRresults(context, data)
            return
        
        
        await context.message.channel.send("Cancion añadida a la playlist")

        if data[serverID]["voiceClient"] == None:
            await player(context, data)


async def playlist(context, url, order=None):
    global data
    global MAX_SONGS
    
    textChannel = context.message.channel  
    serverID = str(context.message.guild.id)
    
    if "spotify" in url:
        listID  = re.search("(https:\/\/open.spotify.com)(\/user\/spotify\/playlist\/|\/playlist\/)(\w+)", url)
        albumID = re.search("(https:\/\/open.spotify.com)(\/user\/spotify\/playlist\/|\/album\/)(\w+)", url)

        if listID != None:
            lista = await spotifyPlaylist(listID[3], order=order)
        
        elif albumID != None:
            lista = await spotifyAlbum(albumID[3], order=order)
        
        else:
            embed = discord.Embed(title="Wrong URL.", colour = discord.Color.green())
            await context.message.channel.send(embed=embed)
            return
        
    else:
        ID = re.search("(youtube.com|youtu.be)(\/playlist\?list=)([a-zA-Z0-9\-\_]+)", url)
        if ID == None:
            embed = discord.Embed(title="Wrong URL.", colour = discord.Color.green())
            await context.message.channel.send(embed=embed)
            return

        lista = await retrievePlaylist(ID[3], order)
  
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

@commands.guild_only()
@commands.check(userConnectedToGuildVoice)
@commands.check(botIsConnectedToGuildVoice)
@client.command(pass_context = True)
async def leave(context):
    serverID = str(context.message.guild.id)
    await data[serverID]["voiceClient"].disconnect()
    data[serverID]["loop"] = 0
    data[serverID]["playlist"].clear()
    data[serverID]["currentSong"] = None
    

@commands.guild_only()
@commands.check(userConnectedToGuildVoice)
@commands.check(botIsConnectedToGuildVoice)
@client.command(pass_context = True)
async def loop(context, msg):
    global data
    serverID = str(context.message.guild.id)

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

@commands.guild_only()
@commands.check(userConnectedToGuildVoice)
@commands.check(botIsConnectedToGuildVoice)
@client.command(pass_context = True)
async def skip(context, ind = None):

    global data
    serverID = str(context.message.guild.id)
    
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

@commands.guild_only()
@commands.check(userConnectedToGuildVoice)
@commands.check(botIsConnectedToGuildVoice)
@client.command(pass_context = True)
async def lista(context):
    global data
   
    serverID = str(context.message.guild.id)
  
    if data[serverID]["loop"] == 0:
        loopSetting = "off"

    elif data[serverID]["loop"] == 1:
        loopSetting = "single"

    else:
        loopSetting = "all"

       
    text = "• **Actual:** {0} \n• **Loop:** {1}\n \n".format(data[serverID]["currentSong"].title, loopSetting)
    for num, video in enumerate(data[serverID]["playlist"]):
        text += '**' + str(num+1) + ")  "  + '**' + video.title + "\n \n"
    
    embed = discord.Embed(title="Playlist:", description = text, colour = discord.Color.green()) 

    await context.message.channel.send(embed=embed)

@commands.guild_only()
@commands.check(userConnectedToGuildVoice)
@commands.check(botIsConnectedToGuildVoice)
@client.command(pass_context = True)
async def quitar(context, numero):
    global data
    
    textChannel = context.message.channel
    serverID = str(context.message.guild.id)
   
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

@commands.guild_only()
@commands.check(userConnectedToGuildVoice)
@commands.check(botIsConnectedToGuildVoice)
@client.command(pass_context = True)
async def vaciar(context):
    global data

    textChannel = context.message.channel
    serverID = str(context.message.guild.id)

    data[serverID]["playlist"].clear()

    embed = discord.Embed(title="Se ha vaciado la playlist", colour = discord.Color.green())
    await textChannel.send(embed=embed)

@commands.guild_only()
@commands.check(userConnectedToGuildVoice)
@commands.check(botIsConnectedToGuildVoice)
@client.command(pass_context = True)
async def song(context):
    global data
  
    serverID = str(context.message.guild.id)
    textChannel = context.message.channel

    embed = discord.Embed(colour=discord.Color.green())
    
    if data[serverID]["voiceClient"] != None and data[serverID]["voiceClient"].is_playing():
        msg = list(["-" for x in range(0, 30)])
        ind = round(30* (data[serverID]["currentSong"].perCentPlayed()))

        msg[ind] = "**|**"
        msg = "".join(msg)
       
        embed.title = data[serverID]["currentSong"].title

        embed.description = "\t" + msg
    
    else:
        embed.title = "No está sonando nada"

    await textChannel.send(embed=embed)


client.run(token)
