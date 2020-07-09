import youtube_dl

from threading import Thread
import discord
from discord.voice_client import VoiceClient
from discord.ext import commands
from discord.ext.commands import Bot
from os import remove
from os.path import isfile
from asyncio import sleep
from .httpRequests import getStringResponse
from googleapiclient.discovery import build
from json import load as loadJson
from spotify import HTTPClient
from random import randint


with open("tokens.json") as tokens:
    tokens = loadJson(tokens)
    api_key = tokens["youtube"]
    spotifyClientId = tokens["spotify"]["clientId"]
    spotifySecretId = tokens["spotify"]["secretId"]

youtube = build("youtube", "v3", developerKey= api_key)
spotifyClient = HTTPClient( spotifyClientId, spotifySecretId)

class video():
    def __init__(self, videoId, title, length=0):
        self.id = videoId
        self.title = title
        self.length = length


async def player(context, data):

    serverID = str(context.message.guild.id)
    textChannel = context.message.channel

    data[serverID]["voiceClient"] = await context.message.author.voice.channel.connect()    
    
    while data[serverID]["voiceClient"].is_connected():

        if not data[serverID]["voiceClient"].is_playing():
            
            await playSong(data, serverID, textChannel)

        await sleep(3)

        if len(data[serverID]["voiceClient"].channel.members) == 1:
            data[serverID]["loop"] = 0
            data[serverID]["playlist"].clear()

            await data[serverID]["voiceClient"].disconnect()
            data[serverID]["voiceClient"] = None

            await textChannel.send("Se ha ido todo el mundo, me piro")
                   
            try:
                remove("serverAudio/" + serverID + ".mp3")
            except FileNotFoundError:               
                pass
            return

        # If there are no more songs and the one that was playing is finished, the loop ends.
        if (data[serverID]["currentSong"] == None and not data[serverID]["voiceClient"].is_playing()):
            break
    
    # Cuando se acaba la playlist:
    data[serverID]["loop"] = 0
    data[serverID]["playlist"].clear()
    await textChannel.send("La playlist esta vacia, me piro.")
    
    try:
        remove("serverAudio/" + serverID + ".mp3")
    except FileNotFoundError:               
        pass
    
    await data[serverID]["voiceClient"].disconnect()
    data[serverID]["voiceClient"] = None

def downloadSong(videoId, path):
    
    url = "https://www.youtube.com/watch?v={0}".format(videoId)
    
    ydl_opts = {

        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
            
        }],
        'quiet': False,
        'outtmpl': 'musica.mp3',
        'noplaylist': True
    }  
    

    ydl_opts["outtmpl"] = path


    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])  # Download into the current working directory
    
async def playSong(data, serverID, textChannel):
    
    
    if data[serverID]["loop"] == 2:
        data[serverID]["playlist"].append(data[serverID]["currentSong"])

    if data[serverID]["currentSong"] != 1:
        
        if len(data[serverID]["playlist"]) > 0:
            data[serverID]["currentSong"] = data[serverID]["playlist"][0]
            data[serverID]["playlist"].pop(0)
        else:
            data[serverID]["currentSong"] = None
            return

    if data[serverID]["currentSong"].id == None:
        try:
            data[serverID]["currentSong"].id = yt_search(data[serverID]["currentSong"].title)["items"][0]["id"]["videoId"]
        except IndexError:
            await textChannel.send("Video no disponible.")
            return
       
    # Downloads the song if loop is not on single.
    if data[serverID]["loop"] != 1:
        
        vidID = data[serverID]["currentSong"].id
        try:
                
            try:
                remove("serverAudio/" + serverID + ".mp3")
            except FileNotFoundError:               
                pass

            path = "serverAudio/" + serverID+".mp3"
            p1 = Thread(target=downloadSong, args=(vidID, path))
            p1.start()

            while p1.isAlive():
                await sleep(3)

        except:
            await textChannel.send("Woopsies")

    try:
        data[serverID]["voiceClient"].play(discord.FFmpegPCMAudio("serverAudio/" + serverID + ".mp3"))
    except:
        await textChannel.send("Video no disponible.")

def yt_search(string):
    global youtube
    
    return youtube.search().list(part="snippet", type="video", q=string).execute()

async def sendYtRresults(context, data):

    serverID = context.message.guild.id

    q = context.message.content[6:]

    result = yt_search(q)

    data[str(serverID)]["search"].clear()     
    embed = discord.Embed(title="Results", colour = discord.Color.green())       
                
    for num, vid in enumerate(result["items"]):
        embed = discord.Embed(title=str(num+1) + ") " + vid["snippet"]["title"], colour = discord.Color.green())  
        embed.set_image(url=vid["snippet"]["thumbnails"]["default"]["url"])
        data[str(serverID)]["search"].append(video(vid["id"]["videoId"], vid["snippet"]["title"]))
        await context.message.channel.send(embed=embed)
    
    #embed.set_footer(text = "Use /play + num")

    

    # else:
    #     embed = discord.Embed(title="Aprende a escribir pringao", colour = discord.Color.green())
    #     await context.message.channel.send(embed=embed)

async def getVidInfo(idVid):
    try:
        res = youtube.videos().list(part="snippet", id=idVid).execute()
        title = res["items"][0]["snippet"]["title"]

        duration = res["items"][0]["contentDetails"]["duration"]

        return title

    except IndexError:
        return None

def retrievePlaylist(playlistID):
    lista = []
    
    try:
        
        res = youtube.playlistItems().list(part="snippet", playlistId=playlistID, maxResults=30).execute()
        title = res["items"][0]["snippet"]["title"]

        for vid in res["items"]:
            title = vid["snippet"]["title"]
            vidID = vid["snippet"]["resourceId"]["videoId"]

            lista.append(video(vidID, title))
    except:
        pass

    return lista

async def spotifyPlaylist(playlistId, r):
    global spotifyClient

    playlist = await spotifyClient.get_playlist(playlistId)
    lista = []

    if r == "r":
        
        while len(lista) < 30 and len( playlist["tracks"]["items"]) > 0:

            ind = randint(0, len(playlist["tracks"]["items"]))
            
            title = playlist["tracks"]["items"][ind]["track"]["name"] + playlist["tracks"]["items"][ind]["track"]["artists"][0]["name"]
            vidID = None
            
            lista.append(video(None, title))
            playlist["tracks"]["items"].pop(ind)

    else:
        for song in playlist["tracks"]["items"]:
            
            lista.append(video(None, song["track"]["name"] + " " + song["track"]["artists"][0]["name"]))
            
            if len(lista) >= 30:
                break
        
    return lista
