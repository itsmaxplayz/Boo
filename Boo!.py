import discord
import json
import random
import youtube_dl
import requests
import os
import time
import mysql.connector
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from discord.ext import commands, tasks
from discord.utils import get
from discord import FFmpegPCMAudio


def get_prefix(client, message):
    db = mysql.connector.connect(host='eu-cdbr-west-03.cleardb.net', user='b835d547697774', password='450bb570', database='heroku_43a797bed744649')
    cursor = db.cursor()
    cursor.execute(f'SELECT prefix FROM prefixes WHERE guild_id = "{message.guild.id}"')
    result = cursor.fetchone()
    return result


client = commands.Bot(command_prefix=get_prefix)
client.remove_command('help')


@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game('-help'))
    print('Bot is ready')
    
    
@client.event
async def on_guild_join(guild):
    db = mysql.connector.connect(host='eu-cdbr-west-03.cleardb.net', user='b835d547697774', password='450bb570', database='heroku_43a797bed744649')
    cursor = db.cursor()
    sql = (f'INSERT INTO prefixes (guild_id, prefix) VALUES(%s, %s)')
    val = (guild.id, '_')
    cursor.execute(sql, val)


@client.event
async def on_guild_remove(guild):
    db = mysql.connector.connect(host='eu-cdbr-west-03.cleardb.net', user='b835d547697774', password='450bb570', database='heroku_43a797bed744649')
    cursor = db.cursor()
    cursor.execute(f'DELETE FROM prefixes WHERE guild_id = "{guild.id}"')


@client.command()
@commands.has_permissions(administrator=True)
async def prefix(ctx, *, prefix):
    db = mysql.connector.connect(host='eu-cdbr-west-03.cleardb.net', user='b835d547697774', password='450bb570', database='heroku_43a797bed744649')
    cursor = db.cursor()
    sql = (f'UPDATE prefixes SET prefix = %s WHERE guild_id = %s')
    val = (prefix, ctx.guild.id)
    cursor.execute(sql, val)
    db.commit()
    
    
@client.event
async def on_message(message):
    if client.user.mentioned_in(message):
        a = message.content
        a = a.split(' ')
        if len(a) == 2:
            if a[1] == 'help' or a[1] == 'Help' or a[1] == 'HELP':
                await help(message)
                
    if not message.author.bot:

        exp = random.randrange(15,  26)
        await update_data(message.author, message.guild.id)
        await add_experience(message.author, exp, message.guild.id)
        await level_up(message.author, message, message.guild.id)

    await client.process_commands(message)


async def update_data(user, message):
    db = mysql.connector.connect(host='eu-cdbr-west-03.cleardb.net', user='b835d547697774', password='450bb570', database='heroku_43a797bed744649')
    cursor = db.cursor()
    cursor.execute(f'SELECT user_id FROM users WHERE user_id = "{user.id}" and guild_id = "{message}"')
    result = cursor.fetchone()
    if result is None:
        sql = (f'INSERT INTO users(guild_id, user_id, exp, level, last_msg, temp_exp, on_lvl_up) VALUES(%s, %s, %s, %s, %s, %s, %s)')
        val = (int(message), int(user.id), 0, 1, 0, 0, 0)
        cursor.execute(sql, val)
        db.commit()


async def add_experience(user, exp, message):

    db = mysql.connector.connect(host='eu-cdbr-west-03.cleardb.net', user='b835d547697774', password='450bb570', database='heroku_43a797bed744649')
    cursor = db.cursor()
    cursor.execute(f'SELECT exp, last_msg, temp_exp FROM users WHERE user_id = "{user.id}" and guild_id = "{message}"')
    result = cursor.fetchone()
    xp = result[0]
    last_msg = result[1]
    temp_exp = result[2]
    if time.time() - last_msg > 60:
        xp += exp
        temp_exp += exp
        last_msg = time.time()
        sql = 'UPDATE users SET exp = %s, temp_exp = %s, last_msg = %s WHERE user_id = %s and guild_id = %s'
        val = (xp, temp_exp, last_msg, user.id, message)
        cursor.execute(sql, val)
        db.commit()


async def level_up(user, message, msg):

    db = mysql.connector.connect(host='eu-cdbr-west-03.cleardb.net', user='b835d547697774', password='450bb570', database='heroku_43a797bed744649')
    cursor = db.cursor()
    cursor.execute(f'SELECT exp, level, temp_exp FROM users WHERE user_id = "{user.id}" and guild_id = "{msg}"')
    result = cursor.fetchone()
    exp = result[0]
    on_lvl_up = exp
    level = result[1]
    temp_exp = result[2]
    req_xp = int((level**4)+(level*100))

    if temp_exp >= req_xp:
        await message.channel.send(f'{user.mention} has leveled up to level {level+1}')
        level += 1
        temp_exp = 0
        sql = 'UPDATE users SET temp_exp = %s, level = %s, on_lvl_up = %s WHERE user_id = %s and guild_id = %s'
        val = (temp_exp, level, on_lvl_up, user.id, msg)
        cursor.execute(sql, val)
        db.commit()


@client.command(aliases=['lb'])
async def leaderboard(ctx):
    guild_id = ctx.guild.id
    db = mysql.connector.connect(host='eu-cdbr-west-03.cleardb.net', user='b835d547697774', password='450bb570', database='heroku_43a797bed744649')
    cursor = db.cursor()
    cursor.execute(f'SELECT user_id, exp, level FROM users WHERE guild_id = "{guild_id}" ORDER BY exp DESC')
    result = cursor.fetchmany(10)
    embed = discord.Embed(title='LEADERBOARD', color=discord.Color.purple(), url='http://allnewsnow.online/l/boo-leaderboard')
    embed.set_thumbnail(url='https://cdn.discordapp.com/avatars/809469105789993032/2348d58f6dd45965dd884a70ebcfcf26.png?size=256')
    for i in result:
        varvar = await client.fetch_user(i[0])
        embed.add_field(name=varvar, value=f'exp - {i[1]}, \t level - {i[2]}', inline=False)

    await ctx.send(embed=embed)



@client.command()
async def rank(ctx, member: discord.Member = None):

    if member is None:

        db = mysql.connector.connect(host='eu-cdbr-west-03.cleardb.net', user='b835d547697774', password='450bb570', database='heroku_43a797bed744649')
        cursor = db.cursor()
        id_1 = ctx.message.author.id
        cursor.execute(f'SELECT exp, level, temp_exp, on_lvl_up FROM users WHERE user_id = "{id_1}" and guild_id = "{ctx.guild.id}"')
        result = cursor.fetchone()
        exp = int(result[0])
        lvl = int(result[1])
        temp_exp = int(result[2])
        on_lvl_up = int(result[3])

        bg = Image.open('Rank Card(1).png')
        asset = ctx.author.avatar_url_as(size=128)
        data = BytesIO(await asset.read())
        pfp = Image.open(data)
        pfp = pfp.resize((135, 135))
        bigsize = (pfp.size[0] * 3, pfp.size[1] * 3)
        mask = Image.new('L', bigsize, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0) + bigsize, fill=255)
        mask = mask.resize(pfp.size, Image.ANTIALIAS)
        pfp.putalpha(mask)

        bg.paste(pfp, (70, 70), pfp)

        draw = ImageDraw.Draw(bg)
        name = str(ctx.message.author)
        f1 = ImageFont.truetype('cour.ttf', 65)
        f2 = ImageFont.truetype('arial.ttf', 28)
        f3 = ImageFont.truetype('arial.ttf', 35)
        draw.text((850, 45), str(lvl), (98, 211, 245), font=f1)
        draw.text((770, 140), str(exp), (127, 131, 132), font=f2)
        draw.text((270, 120), str(name), (255, 255, 255), font=f3)

        req_xp_for_lvl = (lvl ** 4) + (lvl*100)
        perc = (temp_exp/req_xp_for_lvl)*100
        rectangle2 = Image.open('rect_bg.png')
        rectangle2 = rectangle2.resize((630, 35))

        bg.paste(rectangle2, (255, 185))

        if perc > 0:
            rectangle1 = Image.open('rect.png')
            rectangle1 = rectangle1.resize((round(626 * perc/100), 35))
            bg.paste(rectangle1, (255, 185))

        bg.save('rank.png')
        await ctx.send(file=discord.File('rank.png'))
    else:

        db = mysql.connector.connect(host='eu-cdbr-west-03.cleardb.net', user='b835d547697774', password='450bb570', database='heroku_43a797bed744649')
        cursor = db.cursor()
        id_1 = member.id
        cursor.execute(f'SELECT exp, level, temp_exp, on_lvl_up FROM users WHERE user_id = "{id_1}" and guild_id = "{ctx.guild.id}"')
        result = cursor.fetchone()
        exp = int(result[0])
        lvl = int(result[1])
        temp_exp = int(result[2])
        on_lvl_up = int(result[3])

        bg = Image.open('Rank Card(1).png')
        asset = member.avatar_url_as(size=128)
        data = BytesIO(await asset.read())
        pfp = Image.open(data)
        pfp = pfp.resize((135, 135))
        bigsize = (pfp.size[0] * 3, pfp.size[1] * 3)
        mask = Image.new('L', bigsize, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0) + bigsize, fill=255)
        mask = mask.resize(pfp.size, Image.ANTIALIAS)
        pfp.putalpha(mask)

        bg.paste(pfp, (70, 70), pfp)

        draw = ImageDraw.Draw(bg)
        name = str(member)
        f1 = ImageFont.truetype('cour.ttf', 65)
        f2 = ImageFont.truetype('arial.ttf', 28)
        f3 = ImageFont.truetype('arial.ttf', 35)
        draw.text((850, 45), str(lvl), (98, 211, 245), font=f1)
        draw.text((790, 140), str(exp), (127, 131, 132), font=f2)
        draw.text((270, 120), str(name), (255, 255, 255), font=f3)

        req_xp_for_lvl = (lvl ** 4) + (lvl*100)
        perc = (temp_exp / req_xp_for_lvl) * 100
        rectangle2 = Image.open('rect_bg.png')
        rectangle2 = rectangle2.resize((630, 35))

        bg.paste(rectangle2, (255, 185))

        if perc > 0:
            rectangle1 = Image.open('rect.png')
            rectangle1 = rectangle1.resize((round(626 * perc / 100), 35))
            bg.paste(rectangle1, (255, 185))

        bg.save('rank.png')
        await ctx.send(file=discord.File('rank.png'))


@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('Missing argument, please try again with all required arguments')


@client.command()
async def help(ctx):
    
    db = mysql.connector.connect(host='eu-cdbr-west-03.cleardb.net', user='b835d547697774', password='450bb570', database='heroku_43a797bed744649')
    cursor = db.cursor()
    cursor.execute(f'SELECT prefix FROM prefixes WHERE guild_id = "{ctx.guild.id}"')
    result = cursor.fetchone()
    pre = result[0]
    embed = discord.Embed(
        color= discord.Color.purple()
    )

    embed.set_thumbnail(url='https://cdn.discordapp.com/avatars/809469105789993032/2348d58f6dd45965dd884a70ebcfcf26.png?size=256')
    embed.set_author(name='HELP', icon_url='https://cdn.discordapp.com/avatars/809469105789993032/2348d58f6dd45965dd884a70ebcfcf26.png?size=256')
    embed.add_field(name=f'`{pre}ping`', value='gives the ping of the bot', inline=False)
    embed.add_field(name=f'`{pre}prefix`', value='can be used to change prefix of bot (can be used by administrators only)', inline=False)
    embed.add_field(name=f'`{pre}hi`', value='just says hi, or maybe try mentioning someone ;)', inline=False)
    embed.add_field(name=f'`{pre}luv`', value='spread luv in the server or to a specific person', inline=False)
    embed.add_field(name=f'`{pre}8ball`', value='just your standard 8ball', inline=False)
    embed.add_field(name=f'`{pre}clear`', value='clears a particular amount of messages. (must have manage message permission)', inline=False)
    embed.add_field(name=f'`{pre}idjot`', value='Your standard idjot command to call someone an IDJOT. kekw', inline=False)
    embed.add_field(name=f'`{pre}play` or `{pre}p`', value='Plays a song (does not work with spotify yet)', inline=False)
    embed.add_field(name=f'`{pre}queue` or `{pre}q`', value='Add a song to queue', inline=False)
    embed.add_field(name=f'`{pre}pause` or `{pre}pa`', value='Pauses the song currently playing', inline=False)
    embed.add_field(name=f'`{pre}resume` or `{pre}r`', value='Resumes the song currently playing', inline=False)
    embed.add_field(name=f'`{pre}skip` or `{pre}s`', value='Skips the song playing and plays next song in queue', inline=False)
    embed.add_field(name=f'`{pre}leave` or `{pre}disconnect` or `{pre}dc`', value='Disconnects the bot from VC', inline=False)

    await ctx.author.send(embed=embed)


@client.command()
async def ping(ctx):
    await ctx.send(f'{round(client.latency * 1000)}ms')

    
@client.command()
@commands.is_owner()
async def busy(ctx):
    await ctx.send("I'm pretty busy coz I got a very hectic schedule with a ton of classes nowadays, and I've noticed the server is dying")
    await ctx.send('So I coded my bot to send some luv to everyone, every 12 hours')
    await ctx.send('This definitely has nothing to do with me being tired of studying maths and wanting to do some coding. hehe.')
        
    
@client.command(aliases=['hey', 'hello'])
async def hi(ctx, mem: discord.Member = None):
    if mem is None:
        await ctx.send(f'Hello IDJOT!')
    else:
        await ctx.send(f'<@!{ctx.author.id}> says HIII! <@!{mem.id}>')


@client.command()
async def luv(ctx, mem: discord.Member = None):
    if mem is None:
        await ctx.send('Spreading luv to everyone in the server')

    else:
        await ctx.send(f'<@!{ctx.author.id}> sends luv to <@!{mem.id}>')


@client.command(aliases=['8ball'])
async def _8ball(ctx, *, question):
    responses = ['Yes', 'You can rely on it', 'All signs point to yes',
                 'Eh, maybe', 'Cannot predict now', 'Concentrate and ask again',
                 'I would say no', 'Nah', 'All signs point to no']
    await ctx.send(f'{random.choice(responses)}')


@client.command(aliases=['delete'])
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount=1):
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f'Successfully deleted {amount} message')


@client.command()
@commands.cooldown(1, 30, commands.BucketType.user)
async def idjot(ctx, mem: discord.Member = None):
    if mem is None:
        await ctx.send(f"You're an IDJOT!")
    elif mem.id == 432337328694886408:
        await ctx.send("My creator is not an idjot. You're an IDJOT!")
    else:
        await ctx.send(f'<@!{mem.id}> is an IDJOT!')


@client.command(aliases=['dc', 'disconnect'])
async def leave(ctx):

    voice = get(client.voice_clients, guild=ctx.guild)

    if voice and voice.is_connected():
        await voice.disconnect()
        await ctx.send(':mailbox_with_no_mail: **Successfully disconnected**')
    else:
        await ctx.send('I am not in any voice channel currently')


def search(query):

    with ytdl:
        try:
            requests.get(query)
        except:
            info = ytdl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]
        else:
            info = ytdl.extract_info(query, download=False)
    return info, info['formats'][0]['url']

ydl_opts = {
    'format': 'bestaudio/best',
    'quiet': True,
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],

}

ytdl = youtube_dl.YoutubeDL(ydl_opts)

FFMPEG_OPTS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

@client.command(aliases=['p'])
async def play(ctx, *, url):
    channel = ctx.message.author.voice.channel
    voice = get(client.voice_clients, guild=ctx.guild)
    if voice and voice.is_connected():
        pass
    else:
        voice = await channel.connect()
        await ctx.send(f'Successfully joined `{channel}`')

    if voice.is_playing():
        await ctx.send('Already playing a song. Try using -q or -queue to queue a song :thumbsup:')
    else:
        await ctx.send(f'Searching for: `{url}` :mag_right:')
        video, source = search(url)
        voice.play(FFmpegPCMAudio(source, **FFMPEG_OPTS), after=lambda e: check_queue())
        voice.is_playing()
        await ctx.send(f'Playing: :notes: `{video["title"]}` - Now!')


def check_queue():
                           
    voice = get(client.voice_clients)
    if len(queue) <= 0:
        pass
    else:
        next_song = queue.pop(0)
        video, source = search(next_song)
        voice.play(FFmpegPCMAudio(source, **FFMPEG_OPTS), after=lambda e: check_queue())
        voice.is_playing()


@client.command(aliases=['q'])
async def queue(ctx, *, url):
    voice = get(client.voice_clients, guild=ctx.guild)                         
    if voice.is_connected():
        await ctx.send(f'Searching: :mag_right: `{url}`')
        video, source = search(url)
        await ctx.send(f'Found `{video["title"]}` :thumbsup:')
        queue.append(video['title'])
    else:
        await ctx.send('Not in a voice channel')


@client.command(aliases=['pa'])
async def pause(ctx):

    voice = get(client.voice_clients, guild=ctx.guild)
    if voice.is_playing():
        voice.pause()
        await ctx.send('**Paused** :pause_button:')


@client.command(aliases=['r'])
async def resume(ctx):

    voice = get(client.voice_clients, guild=ctx.guild)
    if voice.is_paused():
        voice.resume()
        await ctx.send('**Resuming** :play_pause:')

                   
@client.command(aliases=['s'])
async def skip(ctx):

    voice = get(client.voice_clients, guild=ctx.guild)
    role = discord.utils.get(ctx.guild.roles, name='DJ')
    if role in ctx.author.roles or ctx.message.author.guild_permissions.manage_channels:
        if len(queue) <= 0:
            await ctx.send('No song in queue to skip to. Stopped the one currently playing')
            voice.stop()
        else:
            next_song = queue[0]
            video, source = search(next_song)
            voice.stop()
            await ctx.send('**Skipped** :thumbsup:')
            await ctx.send(f'Playing :notes: `{video["title"]}` - Now!')
            voice.play(FFmpegPCMAudio(source, **FFMPEG_OPTS), after=lambda e: check_queue())
            voice.is_playing()
    else:
        await ctx.send("Can't skip song as you do not have the DJ role or Manage Role permission")


@client.command(aliases=['view'])
async def viewq(ctx):

    embed = discord.Embed(
        color=discord.Color.purple(), title='QUEUE'
    )
    for i in range(0, len(queue)):
        embed.add_field(name='Song ' + str(i+1), value=queue[i], inline=False)

    await ctx.send(embed=embed)

queue = []
client.run(str(os.environ.get('token')))

