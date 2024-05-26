from typing import Literal
import discord.context_managers
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from playhouse.mysql_ext import MySQLConnectorDatabase
from peewee import *
from datetime import date,datetime,timedelta
import discord, os, json, logging, math
import random as rand

logger = logging.getLogger('peewee')
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

load_dotenv()
with open('config.json','r') as config_file: config = json.load(config_file)

discordColors = {
    'Red':discord.Color.red(),
    'Blue':discord.Color.blue(),
    'Yellow':discord.Color.yellow(),
    'Green':discord.Color.green(),
    'Black':discord.Color.default(),
    'Brown':discord.Color.dark_gold(),
    'Purple':discord.Color.purple(),
    'Gray':discord.Color.light_gray(),
    'White':discord.Color.light_embed(),
    'Pink':discord.Color.pink()
}
challengeDescriptions = {
    "Color":["Red", "Blue", "Yellow", "Green", "Black", "Brown", "Purple", "Gray", "White", "Pink"],
    "Generation":"123456789",
    "Starting Letter":"ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "Team":["Aaron", "Acerola", "Adaman", "Agatha", "Akari", "Alder", "Aliana", "Allister", "Archer", "Archie", "Ariana", "Atticus", "Avery", "Barry", "Bea", "Bede", "Beni", "Bertha", "Bianca", "Blaine", "Blue", "Brassius", "Brawly", "Brendan", "Brock", "Bruno", "Brycen", "Bryony", "Bugsy", "Burgh", "Byron", "Caitlin", "Calem", "Candice", "Celosia", "Charm", "Charon", "Cheren", "Chili", "Chuck", "Cilan", "Clair", "Clay", "Clemont", "Colress", "Courtney", "Crasher Wake", "Cress", "Cynthia", "Cyrus", "Diantha", "Drake", "Drasna", "Drayden", "Elesa", "Emmet", "Eri", "Erika", "Falkner", "Fantina", "Flannery", "Flint", "Gaeric", "Gardenia", "Geeta", "Ghetsis", "Giacomo", "Giovanni", "Glacia", "Gladion", "Gordie", "Grant", "Grimsley", "Grusha", "Guzma", "Hala", "Hassel", "Hau", "Hop", "Hugh", "Ingo", "Iono", "Irida", "Iris", "Janine", "Jasmine", "Juan", "Jupiter", "Kabu", "Kahili", "Kamado", "Karen", "Katy", "Klara", "Kofu", "Koga", "Korrina", "Lance", "Larry", "Lenora", "Leon", "Lian", "Lorelei", "Lt Surge", "Lucian", "Lysandre", "Mable", "Mai", "Malva", "Marlon", "Marnie", "Mars", "Marshal", "Matt", "Maxie", "May", "Maylene", "Mela", "Melli", "Melony", "Milo", "Misty", "Molayne", "Morty", "Mustard", "N", "Nemona", "Nessa", "Norman", "Olivia", "Olympia", "Opal", "Ortega", "Penny", "Peony", "Petrel", "Phoebe", "Piers", "Plumeria", "Poppy", "Proton", "Pryce", "Raihan", "Ramos", "Red", "Rei", "Rika", "Roark", "Roxanne", "Roxie", "Ryme", "Sabi", "Sabrina", "Sada", "Saturn", "Shauna", "Shauntal", "Serena", "Shelly", "Sidney", "Siebold", "Silver", "Skyla", "Steven", "Tabitha", "Tate and Liza", "Tierno", "Trace", "Trevor", "Tulip", "Turo", "Valerie", "Viola", "Volkner", "Volo", "Wallace", "Wally", "Wattson", "Whitney", "Wikstrom", "Will", "Winona", "Wulfric", "Xerosic", "Zinzolin"],
    "Description":["Starter Pokemon", "Paradox", "Based On Real Animal", "Final Evolution", "Regional Form", "Legendary", "Ultra Beast", "Baby Pokemon", "Subtle Shiny", "First Route", "Victory Road","Monotype"],
    "Type":["Normal", "Fire", "Water", "Electric", "Grass", "Ice", "Fighting", "Poison", "Ground", "Flying", "Psychic", "Bug", "Rock", "Ghost", "Dragon", "Dark", "Steel", "Fairy"]
}

bot = commands.Bot(command_prefix=config["commandPrefix"], intents=discord.Intents.all())

# --------------------------------------------------------- Database stuff

mydb = MySQLConnectorDatabase(
  "u491157569_dexist",
  user=os.getenv("DB_USERNAME"),
  password=os.getenv("DB_PASSWORD"),
  host=os.getenv("DB_HOST")
)

class BaseModel(Model):
    class Meta:
        database=mydb

class Pokemon(BaseModel):
    identity = CharField()
    name = CharField()
    national = IntegerField()
    color = CharField()
    isFemale = BooleanField(default=False)
    varient = CharField()
    type1 = CharField()
    type2 = CharField(null=True,default=None)
    generation = IntegerField()
    before = IntegerField(null=True,default=None)
    after = IntegerField(null=True,default=None)

class Game(BaseModel):
    name = CharField()
    image = CharField()
    generation = IntegerField()
    spriteLocation = CharField()

class GamePokemon(BaseModel):
    pokemon = ForeignKeyField(Pokemon)
    game = ForeignKeyField(Game)
    notes = CharField()
    regional = IntegerField()

class User(BaseModel):
    id = BigIntegerField(primary_key=True, unique=True)
    level = IntegerField(default=0)
    xp = IntegerField(default=0)
    shinyXpTimesHit = IntegerField(default=0)
    shinyXpEarned = IntegerField(default=0)

class Challenge(BaseModel):
    name = CharField()
    timesRolled = IntegerField(default=0)
    pointsAwarded = IntegerField(default=0)
    description = CharField(default="")

class Leaderboard(BaseModel):
    user = ForeignKeyField(User)
    pokemon = ForeignKeyField(Pokemon)
    points = IntegerField(default=1)
    date = DateField(default=date.today())
    image = CharField()
    challenge = ForeignKeyField(Challenge,null=True)

class Week(BaseModel):
    endDate = DateTimeField()
    challenge = ForeignKeyField(Challenge)
    challengeDesc = CharField()
    pointsAwarded = IntegerField(default=0)
    startedBy = ForeignKeyField(User)

# --------------------------------------------------------- end of database stuff
# --------------------------------------------------------- Xp and level stuff
async def xpForLevel(level: int) -> int:
    if level == 100: return 0

    if level <= 5: return math.floor(4 * level**3 / 5 + 30)
    else: return math.floor(4 * level**3 / 5)

async def addXP(amount: int, user: User, canHitOdds: bool = True):
    if user.level == 100: return False

    randomNum = rand.randint(1,8192)

    if canHitOdds and  randomNum == 2024:
        channel = bot.get_channel(1237051742781313066)
        member = bot.get_user(user.id)
        await channel.send(f"{member.mention} got lucky and got shiny XP! Thats 10 times the normal amount of xp!")
        query = User.update(shinyXpTimesHit = User.shinyXpTimesHit + 1,shinyXpEarned = User.shinyXpEarned + amount * 9)
        query.execute()

        amount = amount * 10

    xpNeededForNextLevel = await xpForLevel(user.level)
    if user.xp + amount >= xpNeededForNextLevel:
        newXP = user.xp + amount - xpNeededForNextLevel
        await levelUp(user)

        if newXP != 0: 
            user = User.get_by_id(user.id)
            await addXP(newXP,user,False)
    else: 
        query = User.update(xp = User.xp + amount).where(User.id == user.id)
        query.execute()

async def levelUp(user: User):
    query = User.update(level = User.level + 1, xp = 0).where(User.id == user.id)
    query.execute()

    channel = bot.get_channel(1237051742781313066)
    member = bot.get_user(user.id)
    embed = discord.Embed(
        title = member.display_name + " just hit level " + str(user.level + 1) + "!",
        description = "You need " + str(await xpForLevel(user.level + 1)) + " xp to level up again!" if (user.level + 1) < 100 else "You can't level up anymore my friend. You've reached the end!",
        color= discord.Color.gold()
    )
    embed.set_author(
        name = member.display_name,
        icon_url = member.avatar.url       
    )

    await channel.send(member.mention, embed = embed)

@bot.tree.command(name="level",description="See the level of yourself or someone else")
@app_commands.describe(member="The user to display, leave blank to check your own level")
async def level(interaction: discord.Interaction, member: discord.User = None):
    mydb.connect()
    
    if member == None: member = interaction.user
            
    user = User.get_by_id(member.id)
    embed = discord.Embed(
        title = member.display_name + " is level " + str(user.level),
        description = "XP: " + str(user.xp) + "/" + str(await xpForLevel(user.level)) if (user.level) < 100 else "No more xp.",
        color= discord.Color.gold()
    )
    embed.add_field(
        name="Shiny XP Hit",
        value=user.shinyXpTimesHit,
        inline=True
    )
    embed.add_field(
        name="Shiny XP Earned",
        value=user.shinyXpEarned,
        inline=True
    )
    embed.set_author(
        name = member.display_name,
        icon_url = member.avatar.url       
    )

    await interaction.response.send_message(embed = embed)

    mydb.close()

# --------------------------------------------------------- end of xp / level stuff
# --------------------------------------------------------- Pokemon stuff

async def getPokemonCard(identifier: str) -> discord.Embed:
    mydb.connect()

    games = []

    if identifier == 'random':
        pokemon = Pokemon.select().order_by(fn.Rand()).limit(1).get()
    else:
        try:
            pokemon = Pokemon.get(Pokemon.identity == identifier)
        except Pokemon.DoesNotExist:
            mydb.close()
            raise ValueError(f"Pokemon with id {identifier} does not exist.")
        
    gamePokemon = GamePokemon.select(GamePokemon, Pokemon,Game).join(Pokemon).switch(GamePokemon).join(Game).where(Pokemon.id == pokemon.id)
    games = [gameLine.game.name for gameLine in gamePokemon]
    name_parts = [pokemon.name]
    if pokemon.varient: name_parts.append(pokemon.varient)
    if pokemon.isFemale == 1: name_parts.append("Female")

    if len(name_parts) > 1: name = f"{pokemon.name} ({" ".join(name_parts[1:])})"
    else: name = pokemon.name
        
    mydb.close()

    types = [pokemon.type1]
    if pokemon.type2 != "NA": types.append(pokemon.type2)
    
    embed = discord.Embed(
        title=name,
        description=pokemon.identity,
        url='https://pokemondb.net/pokedex/' + str(pokemon.national),
        color=discordColors[pokemon.color]
    )
    embed.set_image(url="https://github.com/okwurt/dextracker/blob/main/sprites/games/home/shiny/"+ pokemon.identity +".png?raw=true")
    embed.add_field(name = "Types" if len(types) > 1 else "Type", value = "\n".join(types) if len(types) > 1 else pokemon.type1, inline = True)
    embed.add_field(name = "Color", value = pokemon.color, inline = True)
    embed.add_field(name = "Generation", value = pokemon.generation, inline = True)
    embed.add_field(name = "National Pokedex Number", value = pokemon.national, inline = True)
    embed.add_field(name = "Available Games", value = "None" if games.__len__() == 0 else "\n".join(games), inline = False)
    embed.set_footer(text=pokemon.id)

    return embed

@bot.tree.command(name="random", description="Get the Pokedex page of a random Pokemon")
async def random(interaction: discord.Interaction):
    print("saying someting")

    card = await getPokemonCard('random')
    await interaction.response.send_message(embed=card)

@bot.tree.command(name="pokedex", description="Lookup a Pokemon by their national dex number (and any extra identifiers)")
@app_commands.describe(identity = "What Pokemon to look up")
async def pokedex(interaction: discord.Interaction, identity: str):
    try:
        card = await getPokemonCard(identity)
    except ValueError as e:
        await interaction.response.send_message(f"Error: {e}")
        return

    await interaction.response.send_message(embed=card)

# --------------------------------------------------------- end of Pokemon stuff
# --------------------------------------------------------- bot stuff
    
@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"synced {len(synced)} commands")
    except Exception as e:
        print(e)

@bot.event
async def on_message(message):
    if message.author.bot: return

    memberID = message.author.id
    
    mydb.connect()

    try:
        user = User.get(User.id == memberID)
    except User.DoesNotExist:
        user = User.create(id = memberID)

    await addXP(1,user)

    mydb.close()
    await bot.process_commands(message)

# --------------------------------------------------------- end of bot stuff
# --------------------------------------------------------- weekly and leaderboard stuff

@bot.tree.command(name="leaderboard",description="Shows the leaderboard")
@app_commands.describe(type="The time frame to use when looking up the leaderboard")
@app_commands.describe(date="A date in year-month-day format. This will return the leaderboard for that week")
async def leaderboard(interaction: discord.Interaction, type: Literal["This Week","All Time","Specific"], date: str = "None"):
    mydb.connect()

    if type != 'All Time':
        date = datetime.now() if type == 'This Week' else datetime.strptime(date,'%m-%d-%Y')

        monday_before = date - timedelta(days=date.weekday())
        sunday_after = date + timedelta(days=6-date.weekday())

        timeframe = f"{monday_before.date()} - {sunday_after.date()}"

        query = Leaderboard.select(Leaderboard.user,fn.SUM(Leaderboard.points),User.id).join(User).where((Leaderboard.date >= monday_before) & (Leaderboard.date < sunday_after)).group_by(Leaderboard.user).order_by(fn.SUM(Leaderboard.points).desc()).limit(5)
    else:
        timeframe = "All Time"
        query = Leaderboard.select(Leaderboard.user,fn.SUM(Leaderboard.points),User.id).join(User).group_by(Leaderboard.user).order_by(fn.SUM(Leaderboard.points).desc()).limit(5)

    users = []

    users = [" - ".join([interaction.guild.get_member(user.user.id).display_name,str(user.points)]) for user in query]

    embed = discord.Embed(
        title=f"Leaderboard ({timeframe})",
        color=discordColors["Pink"]
    )
    embed.add_field(
        name="Users",
        value="\n".join(users)
    )

    await interaction.response.send_message(embed=embed)

    mydb.close()

@bot.tree.command(name="weekly",description="Get the current weekly hunt")
async def weekly(interaction: discord.Interaction):
    mydb.connect()
    
    try:
        weekly = Week.select().order_by(Week.endDate.desc()).limit(1).get()
        
        if weekly.endDate < datetime.now():
            await interaction.response.send_message("Weekly has not been started yet! Starting a new one now!")
            mydb.close()
            embed = await startWeekly(interaction.user.id)
        else:
            mydb.close()
            embed = await getWeeklyEmbed()
    except Week.DoesNotExist:
        await interaction.response.send_message("No Weekly found! Starting a new one")
        mydb.close()
        embed = await startWeekly(interaction.user.id)

    await interaction.response.send_message(embed=embed)

async def getWeeklyEmbed() -> discord.Embed:
    mydb.connect()

    weekly = Week.select().order_by(Week.endDate.desc()).limit(1).get()
    challenge = weekly.challenge

    embed = discord.Embed(
        title=f"This weeks challenge is {weekly.challengeDesc}",
        description=challenge.description
    )
    embed.add_field(name="End Date",value=weekly.endDate)

    member = await bot.get_guild(976929325406355477).fetch_member(weekly.startedBy)

    embed.set_footer(text=f"Started by {member}")

    mydb.close()

    return embed

async def startWeekly(user) -> discord.Embed:
    mydb.connect()

    today = datetime.today()
    sunday =  today + timedelta((6-today.weekday()) % 7)
    sunday = datetime.combine(sunday, datetime.max.time())

    challenge = Challenge.select().order_by(fn.Rand()).limit(1).get()

    match challenge.name:
        case "Pokemon":
            max = Pokemon.select().order_by(Pokemon.national.desc()).limit(1).get()
            max = max.national
            randomNumber = rand.randint(1,max)
            challengeDesc = str(randomNumber)
        case _:
            challengeDesc = rand.choice(challengeDescriptions[challenge.name]["items"])

    week = Week(endDate=sunday,challenge=challenge.id,challengeDesc=challengeDesc,startedBy=user)
    week.save()

    mydb.close()

    return await getWeeklyEmbed(week.id)

# --------------------------------------------------------- end of weekly and leaderboard stuff

bot.run(os.getenv("BOT_TOKEN"))