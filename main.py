import random

import discord
import yt_dlp as youtube_dl
from discord.ext import commands
import asyncio

from database_functions import *

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',  # bind to ipv4 since ipv6 addresses cause issues sometimes
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
}

ffmpeg_options = {
    'options': '-vn -fflags +discardcorrupt -ignore_unknown -dn -sn -ab 32000',
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

OWNER_CLIENT_ID = "207371595113562124"


# Referenced from the Author of discord.py Rapptz
class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        cls(discord.FFmpegPCMAudio(executale= "C:/ffmpeg", source=filename, **ffmpeg_options), data=data)


class Commands(commands.Cog, name="commands"):

    def __init__(self, bot):
        self.bot = bot
        with open('songs.json') as f:
            data = json.load(f)
            self.song_data = data
        print(f"Loaded {len(self.song_data)} songs...")
        random.shuffle(self.song_data)
        self.song_index = 0
        with open('anime_characters.json') as f:
            data = json.load(f)
            self.anime_char_data = data
        print(f"Loaded {len(self.anime_char_data)} anime characters...")
        random.shuffle(self.anime_char_data)
        self.anime_char_index = 0
        self.in_game = {}

        self.trivia_index = 0
        with open('trivia_questions.json') as f:
            data = json.load(f)
            self.anime_trivia_questions = data
        print(f"Loaded {len(self.anime_trivia_questions)} trivia questions...")
        random.shuffle(self.anime_trivia_questions)

    @commands.command(name="guesstheost", aliases=['gto'], pass_context=True)
    async def play_game(self, ctx):
        """
        Entry point for the game
        :return: void
        """
        play_amount = 0
        args = ctx.message.content.split(" ")
        if len(args) > 2:
            play_amount += int(args[1])
        voice_channel = ctx.author.voice.channel
        try:
            await voice_channel.connect()
            await ctx.send("Playing a song in a few seconds, hold tight!")
        except Exception as e:
            print(e)
            await ctx.send("Starting up another game!")
        await asyncio.sleep(1)

        if self.song_index == len(self.song_data) - 1:
            self.song_index = 0
            random.shuffle(self.song_data)
            await ctx.send("All unique songs have been played, shuffling the list now")

        def check_anime_song(m):
            anime_name = m.content.lower()
            return anime_name == music_to_guess.lower() and m.channel == ctx.channel

        while True:
            try:
                music_to_guess = self.song_data[self.song_index][0]
                music_url = self.song_data[self.song_index][1]

                player = await YTDLSource.from_url(music_url, loop=self.bot.loop,
                                                   stream=True)
                try:
                    if ctx.voice_client is not None:
                        ctx.voice_client.play(player, after=lambda x: print('Player error: %s' % x) if x else None)
                except Exception as e:
                    print("error playing song:", e)
                    self.song_index += 1
                    continue
                await ctx.send(
                    "Try guessing the soundtrack by typing in this channel (anyone can try)! You got 25 seconds.")

                user_msg = await self.bot.wait_for('message', check=check_anime_song, timeout=25.0)
                add_points(str(user_msg.author.id), 1)
                await ctx.send("Nice, you guessed the correct OST ({})!".format(
                    music_to_guess.title()))

                self.song_index += 1

                if self.song_index == len(self.song_data) - 1:
                    self.song_index = 0
                    random.shuffle(self.song_data)
                    await ctx.send("All unique songs have been played, shuffling the list now")

                music_to_guess = self.song_data[self.song_index][0]
                music_url = self.song_data[self.song_index][1]

                ctx.voice_client.stop()
                await asyncio.sleep(1)
            except Exception as e:
                print(e)
                if "Video unavailable" in str(e) or "Private video" in str(e):
                    await ctx.send(
                        f"{music_to_guess} has a broken link ({self.song_data[self.song_index][1]}), pls fix!")
                else:
                    await ctx.send(
                        "Sorry, you took to long to guess do !!gto to start again, the song was {}.".format(
                            music_to_guess.title()))
                self.song_index += 1
                ctx.voice_client.stop()

    @commands.command(name="playsong", pass_context=True)
    async def play_song(self, ctx):
        voice_channel = ctx.author.voice.channel
        try:
            await voice_channel.connect()
            await ctx.send("Playing a random anime song in my database, hold tight!")
        except Exception as e:
            print(e)
            ctx.voice_client.stop()
            await ctx.send("Starting up another random anime song!")
        await asyncio.sleep(1)

        rand_idx = random.randint(0, len(self.song_data) - 1)
        music_url = self.song_data[rand_idx][1]

        player = await YTDLSource.from_url(music_url, loop=self.bot.loop,
                                           stream=True)
        ctx.voice_client.play(player, after=lambda x: print('Player error: %s' % x) if x else None)

    @commands.command(name="leavegame", pass_context=True)
    async def leave_vc(self, ctx):
        await ctx.voice_client.disconnect()
        await ctx.send("Goodbye!")

    @commands.command(name="hello", pass_context=True)
    async def handle_hello(self, ctx):
        await ctx.send("Shut up scum.")

    @commands.command(name="stats", pass_context=True)
    async def handle_stats(self, ctx):
        e = discord.Embed(title=ctx.author.name + "'s Stats")
        elo = get_elo(str(ctx.author.id))
        rank_icon = ""
        rank = ""
        if 0 <= elo < 25:
            rank = "Cadet"
            rank_icon = "https://cdn.discordapp.com/attachments/942907758397763694/1215130004451500062/360.png?ex=65fba101&is=65e92c01&hm=d95e1dc739374eadd70c3c899f2e20ff61c4d05f89c11b23c451da74f7616d2c&"
        elif 25 <= elo < 35:
            rank = "Soldier"
            rank_icon = "https://cdn.discordapp.com/attachments/942907758397763694/1215136572463120434/ScoutMedalGreen.png?ex=65fba71f&is=65e9321f&hm=5d9672174f79ead8c5bfdae947606dee50158cfedb90f1da4353b62e18dd382b&"
        elif 35 <= elo < 45:
            rank = "Elite Soldier"
            rank_icon = "https://cdn.discordapp.com/attachments/942907758397763694/1215136572790542346/ScoutMedalRed.png?ex=65fba71f&is=65e9321f&hm=a452e026e879353e219cc9b5c9afb57bf89d63287303b3670abc49688b135fa6&"
        elif 45 <= elo < 55:
            rank = "Squad Leader"
            rank_icon = "https://cdn.discordapp.com/attachments/942907758397763694/1215134330863624303/Untitled157_20240306210432.png?ex=65fba508&is=65e93008&hm=a158928a228cbb3a61874031d095cb92c44bf2a3efff3d96a07a42bbd13751be&"
        elif 55 <= elo:
            rank = "Captain"
            rank_icon = "https://cdn.discordapp.com/attachments/942907758397763694/1215134331408744478/IMG_2017.png?ex=65fba508&is=65e93008&hm=6c7355cd4c8031c59b7171a33226d134e9775f74a882fb234e51db0b2e3ee220&"

        e.set_thumbnail(url=rank_icon)
        e.add_field(name="Guess Points", value=get_points(str(ctx.author.id)))
        e.add_field(name="ELO Points", value=elo, inline=False)
        e.add_field(name="Rank", value=rank, inline=False)

        await ctx.send(embed=e)

    @commands.command(name="query_song", aliases=['qs'], pass_context=True)
    async def query_song(self, ctx):
        args = ctx.message.content.split(" ")
        if len(args) < 2:
            await ctx.send("Format: !query_song <anime name>")
            return
        links = ""
        queried_name = " ".join(args[1:]).lower()
        total_songs = 0
        for data in self.song_data:
            anime_name = data[0].lower()
            if queried_name in anime_name:
                # youtube_vid = await YTDLSource.from_url(data[1], stream=True)
                links += anime_name.title() + f": " + data[1] + "\n\n"  # Links
                total_songs += 1

        await ctx.send(
            f"All Song Links from the queried {queried_name.title()}:\n```Total Songs Found: {total_songs}\n\n{links}```")

    @commands.command(name="character", aliases=['char', 'c', 'C'], pass_context=True)
    async def rand_char(self, ctx):
        if self.in_game.get(ctx.author.id):
            await ctx.send("You are already in a game, please finish that one first.")
            return
        self.anime_char_index += 1
        if self.in_game.get(ctx.author.id) is None or not self.in_game.get(ctx.author.id):
            self.in_game[ctx.author.id] = True

        character = self.anime_char_data[self.anime_char_index]
        e = discord.Embed(title="Guess the Character")
        e.set_image(url=character['img'])

        def check(m):
            char_name = m.content.lower()
            if m.channel == ctx.channel:
                for n in character['name']:
                    if char_name == n.lower():
                        return True
            reversed_name = reversed(character['name'])
            return char_name == " ".join(character['name']).lower() or char_name == " ".join(reversed_name).lower() or \
                   (char_name == "skip" and m.author.id == ctx.author.id)

        await ctx.send(embed=e)

        try:
            user_msg = await self.bot.wait_for('message', check=check, timeout=12.0)
            if user_msg.content.lower() == "skip":
                await ctx.send(f"Skipped **{' '.join(character['name'])}** from "
                               f"**{character['anime']}**, {user_msg.author.name}")
            else:
                add_points(str(user_msg.author.id), 1)
                add_character_to_inventory(user_msg.author.id, character)
                await ctx.send(
                    f"Nice, {user_msg.author.name} got the correct answer, you gain a point for guessing"
                    f" **{' '.join(character['name'])}** from the anime **{character['anime']}**!\n"
                    f"The character has been added to your inventory!")
        except asyncio.TimeoutError:
            await ctx.send(f"You could not answer correctly in the time given {ctx.author.name}.\n"
                           f"The character was **{' '.join(character['name'])}** from the anime **{character['anime']}**")
        finally:
            self.in_game[ctx.author.id] = False
            if self.anime_char_index == len(self.anime_char_data) - 1:
                random.shuffle(self.anime_char_data)
                self.anime_char_index = 0

    @commands.command(aliases=['sg'], pass_context=True)
    async def suggest_song(self, ctx):
        args = ctx.message.content.split(" ")
        if len(args) < 3:
            await ctx.send("Format: !suggest_song or !sg <youtube_link> <anime name>")
            return

        youtube_link = args[1]
        anime_name = " ".join(args[2:])

        if str(ctx.author.id) == OWNER_CLIENT_ID:
            self.song_data.append([anime_name, youtube_link])
            with open('songs.json', 'w') as json_file:
                json_string = json.dumps(self.song_data, indent=4)
                json_file.write(json_string)
            await ctx.send("Successfully added anime song to song database.")
            return
        else:
            await ctx.send("Considering the song suggestion, please wait until Brandon's approval.")
            if anime_name.startswith("http"):
                await ctx.send("The correct format is: !!suggest_song <YOUTUBE LINK> <ANIME NAME>")
                return

            def wait_for_approval(m):
                return (m.content.lower() == "lgtm" and str(m.author.id) == OWNER_CLIENT_ID) \
                       or (m.content.lower() == "no" and str(m.author.id) == OWNER_CLIENT_ID)

        try:
            user_msg = await self.bot.wait_for('message', check=wait_for_approval, timeout=180.0)
            if user_msg.content.lower() == "no":
                await ctx.send("Unapproved by Brandon.")
                return
            self.song_data.append([anime_name, youtube_link])
            with open('songs.json', 'w') as json_file:
                json_string = json.dumps(self.song_data, indent=4)
                json_file.write(json_string)
            await ctx.send("Successfully added anime song to song database.")
        except Exception as e:
            print(e)
            await ctx.send("Ran out of time for approval")

    @commands.command(name="trivia", aliases=['t', 'T'], pass_context=True)
    async def trivia(self, ctx):
        if self.in_game.get(ctx.author.id):
            await ctx.send("You are already in a game, please finish that one first.")
            return

        self.in_game[ctx.author.id] = True
        e = discord.Embed(title="Attack on Titan Trivia![{}]".format(ctx.author.name), color=discord.colour.Colour.teal(),
                          description="Pick one of the numbers or type out the answer.")
        e.set_thumbnail(url="https://cdn.discordapp.com/attachments/942907758397763694/1216260325418991617/latest.png?ex=65ffbdb2&is=65ed48b2&hm=c9602b872f2c96fa96227c783068194901a94fdadb8e00754d7b732ca36df9d3&")

        trivia_question = self.anime_trivia_questions[self.trivia_index]
        self.trivia_index += 1
        question = trivia_question["question"]
        e.add_field(name="Question", value=f"```{question}```", inline=False)
        random.shuffle(trivia_question["answers"])
        answers = "```"
        answers_dict = {

        }
        correct_ans = {

        }
        for i, answer in enumerate(trivia_question["answers"]):
            answers_dict[f"{i + 1}"] = answer
            if answer == trivia_question["answer"]:
                correct_ans[f"{i + 1}"] = answer
        for key in answers_dict:
            answer = answers_dict[key]
            answers += f"\n{key}. {answer}"

        answers += "```"
        e.add_field(name="Possible Answers", value=answers, inline=False)

        def check(m):
            return m.channel.id == ctx.channel.id and m.author.id == ctx.author.id

        await ctx.send(embed=e)

        try:
            user_msg = await self.bot.wait_for('message', check=check, timeout=20.0)
            user_ans = user_msg.content.lower()
            ans = trivia_question["answer"]
            if user_ans == ans.lower() or correct_ans.get(user_ans) == ans:
                add_points(str(user_msg.author.id), 1)
                await ctx.send(
                    "Nice! {} got the correct answer ({}).".format(user_msg.author.name, trivia_question["answer"]))
            else:
                await ctx.send("Wrong Answer, {}.".format(user_msg.author.name, trivia_question["answer"]))
        except asyncio.TimeoutError:
            await ctx.send(f"You could not answer correctly in the time given {ctx.author.name}.")
        finally:
            self.in_game[ctx.author.id] = False
            if self.trivia_index == len(self.anime_trivia_questions) - 1:
                random.shuffle(self.anime_trivia_questions)
                self.trivia_index = 0


async def setup(bot):
    await bot.add_cog(Commands(bot))
