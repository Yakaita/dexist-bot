from typing import List, Literal
from discord.ext import commands
from discord import app_commands
from peewee import fn
import asyncio

from dotenv import load_dotenv
load_dotenv()

from models import *
from datetime import datetime,timedelta
import discord, os, json, logging, math
import random as rand

logger = logging.getLogger('peewee')
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

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

pokemon_colors = Literal[
    "Red",
    "Blue",
    "Yellow",
    "Green",
    "Black",
    "Brown",
    "Purple",
    "Gray",
    "White",
    "Pink"
]

pokemon_types = Literal[
    "Normal",
    "Fire",
    "Water",
    "Electric",
    "Grass",
    "Ice",
    "Fighting",
    "Poison",
    "Ground",
    "Flying",
    "Psychic",
    "Bug",
    "Rock",
    "Ghost",
    "Dragon",
    "Dark",
    "Steel",
    "Fairy",
    "N/A"
]

challengeDescriptions = {
    "Color":["Red", "Blue", "Yellow", "Green", "Black", "Brown", "Purple", "Gray", "White", "Pink"],
    "Generation":"123456789",
    "Starting Letter":"ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "Team":["Aaron", "Acerola", "Adaman", "Agatha", "Akari", "Alder", "Aliana", "Allister", "Archer", "Archie", "Ariana", "Atticus", "Avery", "Barry", "Bea", "Bede", "Beni", "Bertha", "Bianca", "Blaine", "Blue", "Brassius", "Brawly", "Brendan", "Brock", "Bruno", "Brycen", "Bryony", "Bugsy", "Burgh", "Byron", "Caitlin", "Calem", "Candice", "Celosia", "Charm", "Charon", "Cheren", "Chili", "Chuck", "Cilan", "Clair", "Clay", "Clemont", "Colress", "Courtney", "Crasher Wake", "Cress", "Cynthia", "Cyrus", "Diantha", "Drake", "Drasna", "Drayden", "Elesa", "Emmet", "Eri", "Erika", "Falkner", "Fantina", "Flannery", "Flint", "Gaeric", "Gardenia", "Geeta", "Ghetsis", "Giacomo", "Giovanni", "Glacia", "Gladion", "Gordie", "Grant", "Grimsley", "Grusha", "Guzma", "Hala", "Hassel", "Hau", "Hop", "Hugh", "Ingo", "Iono", "Irida", "Iris", "Janine", "Jasmine", "Juan", "Jupiter", "Kabu", "Kahili", "Kamado", "Karen", "Katy", "Klara", "Kofu", "Koga", "Korrina", "Lance", "Larry", "Lenora", "Leon", "Lian", "Lorelei", "Lt Surge", "Lucian", "Lysandre", "Mable", "Mai", "Malva", "Marlon", "Marnie", "Mars", "Marshal", "Matt", "Maxie", "May", "Maylene", "Mela", "Melli", "Melony", "Milo", "Misty", "Molayne", "Morty", "Mustard", "N", "Nemona", "Nessa", "Norman", "Olivia", "Olympia", "Opal", "Ortega", "Penny", "Peony", "Petrel", "Phoebe", "Piers", "Plumeria", "Poppy", "Proton", "Pryce", "Raihan", "Ramos", "Red", "Rei", "Rika", "Roark", "Roxanne", "Roxie", "Ryme", "Sabi", "Sabrina", "Sada", "Saturn", "Shauna", "Shauntal", "Serena", "Shelly", "Sidney", "Siebold", "Silver", "Skyla", "Steven", "Tabitha", "Tate and Liza", "Tierno", "Trace", "Trevor", "Tulip", "Turo", "Valerie", "Viola", "Volkner", "Volo", "Wallace", "Wally", "Wattson", "Whitney", "Wikstrom", "Will", "Winona", "Wulfric", "Xerosic", "Zinzolin"],
    "Description":["Starter Pokemon", "Paradox", "Based On Real Animal", "Final Evolution", "Regional Form", "Legendary", "Ultra Beast", "Baby Pokemon", "Subtle Shiny", "First Route", "Victory Road","Monotype"],
    "Type":["Normal", "Fire", "Water", "Electric", "Grass", "Ice", "Fighting", "Poison", "Ground", "Flying", "Psychic", "Bug", "Rock", "Ghost", "Dragon", "Dark", "Steel", "Fairy"]
}

bot = commands.Bot(command_prefix=config["commandPrefix"], intents=discord.Intents.all())


GUILD = bot.get_guild(976929325406355477)

# --------------------------------------------------------- Database stuff

async def field_autocomplete(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    if interaction.namespace["to_edit"] == "Pokemon": fields = ["identity","name","national","color","isFemale","varient","type1","type2","generation","before","after"]
    elif interaction.namespace["to_edit"] == "Challenge": fields = ["name","description"]
    else: return []
    return [app_commands.Choice(name = field, value = field) for field in fields if current.lower() in field.lower()]

async def new_data_autocomplete(interaction: discord.Interaction, current:str) -> List[app_commands.Choice[str]]:
    if interaction.namespace["field"] == "color": data = pokemon_colors
    elif interaction.namespace["field"] == "isFemale": data = ["true","false"]
    elif interaction.namespace["field"] == "type1" or interaction.namespace["field"] == "type2": data = pokemon_types
    elif interaction.namespace["field"] == "generation": data = ["1","2","3","4","5","6","7","8","9"]
    else: return []
    return [app_commands.Choice(name = field, value = field) for field in data if current.lower() in field.lower()]

@bot.tree.command(name="edit", description="Edit part of the database. Must be a mod or higher to run this command",guild=GUILD)
@app_commands.describe(to_edit="The thing to edit")
@app_commands.describe(field="The part to edit")
@app_commands.autocomplete(field = field_autocomplete)
@app_commands.describe(id="The id of the item")
@app_commands.describe(new_data="The new data")
@app_commands.autocomplete(new_data = new_data_autocomplete)
async def edit(interaction: discord.Interaction,to_edit: Literal["Pokemon","Challenge"],id:int,field:str, new_data: str):
    print(f"{interaction.user.display_name} ran /edit {to_edit} {id} {field} {new_data}")

    allowed_roles = [1242248445184573553]

    user_roles = [role.id for role in interaction.user.roles]
    if not any(role in allowed_roles for role in user_roles):
        await interaction.response.send_message("You do not have permission to use this command!",ephemeral=True)
        return

    if field.lower() == "id": 
        await interaction.response.send_message("You cannot edit the ID!",ephemeral=True)
        return
    
    if to_edit == "Pokemon":
        try:
            mydb.connect()
            pokemon = await asyncio.to_thread(Pokemon.get_by_id,id)
        except Pokemon.DoesNotExist:
            await interaction.response.send_message("Im sorry but a Pokemon by that id does not exist! Please try again",ephemeral=True)
            return
        finally:
            mydb.close()

        embed = await asyncio.to_thread(pokemon.get_embed)
        await interaction.response.send_message("Are you sure you want to edit this Pokemon?",embed=embed,view=YesCancelButtons(pokemon,field,new_data),ephemeral=True)
    elif to_edit == "Challenge":
        try:
            mydb.connect()
            challenge = await asyncio.to_thread(Challenge.get_by_id,id)

            #todo: finish this
        except Challenge.DoesNotExist:
            await interaction.response.send_message(f"I could not find a challenge with the id {id}!",ephemeral=True)
            return
        finally:
            mydb.close()

@bot.tree.command(name="add_pokemon",description="Add a Pokemon to the database. Only mods+ can run this command",guild=GUILD)
@app_commands.describe(identity="The identity of the Pokemon, [n#]-[varient if any]-[f if female]")
@app_commands.describe(name="The species name of the Pokemon. Does not include any identifiers. Raichu and Alolan Raichu are both named \"Raichu\"")
@app_commands.describe(national="The national Pokedex number of the species.")
@app_commands.describe(color="The color in the Pokedex")
@app_commands.describe(isfemale="Where the Pokemon is the female varient (has -f in the indentity)")
@app_commands.describe(varient="The varient of the Pokemon. Alolan or Galarian instead of alola or galar. This should be part of the identity as well")
@app_commands.describe(type1="The first type of the Pokemon, should not be n/a")
@app_commands.describe(type2="The second type of the Pokemon. use N/A if it is monotype")
@app_commands.describe(generation="The generation of the Pokemon. Will default to the most recent generation")
@app_commands.describe(before="The id of the Pokemon that comes before this one. Mostly used for new varients that should be next to their counterparts in the Pokedex")
@app_commands.describe(after="The id of the Pokemon that comes after this one. Mostly used for new varients that should be next to their counterparts in the Pokedex")
async def add_pokemon(interaction: discord.Interaction, identity:str, name:str, isfemale: bool = False, national:int = 0, color:pokemon_colors = "White", varient:str = "", type1:pokemon_types = "N/A",type2:pokemon_types = "N/A",generation:int = 9, before:int=None,after:int=None):
    print(f"{interaction.user.display_name} ran /add_pokemon {identity} {name} {national} {color} {isfemale} {varient} {type1} {type2} {generation} {before} {after}")

    allowed_roles = [1242248445184573553]

    user_roles = [role.id for role in interaction.user.roles]
    if not any(role in allowed_roles for role in user_roles):
        await interaction.response.send_message("You do not have permission to use this command!",ephemeral=True)
        return
    
    try:
        mydb.connect()

        await asyncio.to_thread(Pokemon.get,Pokemon.identity == identity)
        await interaction.response.send_message(f"A Pokemon with that identifier already exists! Please use /Pokedex {identity} to see it",ephemeral=True)
        return
    except Pokemon.DoesNotExist:
        pass
    finally:
        mydb.close()
    
    try:
        mydb.connect()

        new_pokemon = Pokemon(identity=identity,name=name,isFemale=isfemale,national=national,color=color,varient=varient,type1=type1,type2=type2,generation=generation,before=before,after=after)

        await asyncio.to_thread(new_pokemon.save)

        if before != None:
            before_pokemon = await asyncio.to_thread(Pokemon.get_by_id,before)
            before_pokemon.after = new_pokemon.id
            await asyncio.to_thread(before_pokemon.save)

        if after != None:
            after_pokemon = await asyncio.to_thread(Pokemon.get_by_id,after)
            after_pokemon.before = new_pokemon.id
            await asyncio.to_thread(after_pokemon.save)
    except Exception as e:
        await interaction.response.send_message(f"Failed to add Pokemon: {e}",ephemeral=True)
        return
    finally:
        mydb.close()

    embed = await asyncio.to_thread(new_pokemon.get_embed)
    await interaction.response.send_message(f"{new_pokemon.identity} added with id of {new_pokemon.id}", embed=embed,ephemeral=True,view=PokedexButtons(new_pokemon.id))
    
# --------------------------------------------------------- end of database stuff
# --------------------------------------------------------- Views

class YesCancelButtons(discord.ui.View):
    def __init__(self,object,attribute:str,new_value:str):
        super().__init__()
        self.object = object
        self.attribute = attribute
        self.new_value = new_value


    @discord.ui.button(label="Yes",style=discord.ButtonStyle.green)
    async def yes(self,interaction:discord.Interaction,button:discord.ui.Button):
        try:
            old_value = getattr(self.object,self.attribute)

            await edit_database_object(self.object,self.attribute,self.new_value)
            await interaction.response.send_message(f"Changed {self.attribute} from {old_value} to {self.new_value}!",ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Something went wrong, nothing changed! {e}",ephemeral=True)
            return

    @discord.ui.button(label="Cancel",style=discord.ButtonStyle.red)
    async def cancel(self, interaction:discord.Interaction,button:discord.ui.Button):
        await interaction.response.edit_message(content="Canceled edit.",view=None,embed=None)


class PokedexButtons(discord.ui.View):
    def __init__(self,id:int):
        super().__init__()
        self.id = id

    @discord.ui.button(label="Previous",style=discord.ButtonStyle.blurple)
    async def previous(self, interaction: discord.Interaction,button:discord.ui.Button):
        if self.id == 1:
            self.children[0].disabled = True
            await interaction.response.edit_message(view=self)
            return
        
        try:
            mydb.connect()
            pokemon = await asyncio.to_thread(Pokemon.get_by_id,self.id)
            new_id = pokemon.before if pokemon.before != None else self.id - 1
            new_pokemon = await asyncio.to_thread(Pokemon.get_by_id,new_id)
        except Exception as e:
            await interaction.response.edit_message(f"Something went wrong: {e}")
            return
        finally:
            mydb.close()

        embed = await asyncio.to_thread(new_pokemon.get_embed)
        await interaction.response.edit_message(embed=embed,view=PokedexButtons(new_id))

    @discord.ui.button(label="Next",style=discord.ButtonStyle.blurple)
    async def next(self,interaction: discord.Interaction, button:discord.ui.Button):
        try:
            mydb.connect()
            pokemon = await asyncio.to_thread(Pokemon.get_by_id,self.id)
            new_id = pokemon.after if pokemon.after != None else self.id + 1
            new_pokemon = await asyncio.to_thread(Pokemon.get_by_id,new_id)
        except Pokemon.DoesNotExist:
            self.children[1].disabled = True
            await interaction.response.edit_message(view=self)
        finally:
            mydb.close()

        embed = await asyncio.to_thread(new_pokemon.get_embed)
        await interaction.response.edit_message(embed=embed,view=PokedexButtons(new_id))

# --------------------------------------------------------- end of Views
# --------------------------------------------------------- Xp and level stuff

@bot.tree.command(name="level",description="See the level of yourself or someone else",guild=GUILD)
@app_commands.describe(member="The user to display, leave blank to check your own level")
async def level(interaction: discord.Interaction, member: discord.User = None):
    print(f"{interaction.user.display_name} ran /level {member.name if member != None else ""}")

    if member == None: member = interaction.user
    
    try: 
        mydb.connect()
        user = await asyncio.to_thread(User.get_by_id,member.id)
    except:
        await interaction.response.send_message("I could not find that user!",ephemeral=True)
    finally:
        mydb.close()

    embed = discord.Embed(
        title = member.display_name + " is level " + str(user.level),
        description = "XP: " + str(user.xp) + "/" + str(await asyncio.to_thread(user.xpForLevel)) if (user.level) < 100 else "No more xp.",
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

    await interaction.response.send_message(embed=embed,ephemeral=True)

    mydb.close()


@bot.tree.command(name="award_xp",description="Awards xp to a user. Must be mod+ to run this command",guild=GUILD)
@app_commands.describe(user="The discord user to add the xp to.")
@app_commands.describe(amount="The amount of xp to add, defaults to 1 if not given a value")
async def award_xp(interaction: discord.Interaction, user: discord.User,amount: int = 1):
    print(f"{interaction.user.display_name} ran /award_xp {user.name} {amount}")

    allowed_roles = [1242248445184573553]

    user_roles = [role.id for role in interaction.user.roles]
    if not any(role in allowed_roles for role in user_roles):
        await interaction.response.send_message("You do not have permission to use this command!",ephemeral=True)
        return
    
    try:
        mydb.connect()
        table_user = asyncio.to_thread(User.get_by_id,user.id)
        worked = await asyncio.to_thread(table_user.addXP,amount=amount,can_hit_odds=True)
    except Exception as e:
        await interaction.response.send_message(f"Failed to award xp: {e}",ephemeral=True)
        return
    finally:
        mydb.close()

    if worked:
        await interaction.response.send_message(f"Awarded {amount} xp to {user.name}",ephemeral=True)
    else:
        await interaction.response.send_message(f"User is level 100 so I couldnt add any more xp!")

# --------------------------------------------------------- end of xp / level stuff
# --------------------------------------------------------- Pokemon stuff

@bot.tree.command(name="random", description="Get the Pokedex page of a random Pokemon",guild=GUILD)
async def random(interaction: discord.Interaction):
    print(f"{interaction.user.display_name} ran /random")

    pokemon = await asyncio.to_thread(Pokemon.get_random)
    embed = await asyncio.to_thread(pokemon.get_embed)
    await interaction.response.send_message(embed=embed,view=PokedexButtons(int(embed.footer.text)),ephemeral=True)

@bot.tree.command(name="pokedex", description="Lookup a Pokemon by their national dex number (and any extra identifiers)",guild=GUILD)
@app_commands.describe(identity = "What Pokemon to look up")
async def pokedex(interaction: discord.Interaction, identity: str):
    print(f"{interaction.user.display_name} ran /pokedex {identity}")
    
    try:
        pokemon = await asyncio.to_thread(Pokemon.get,Pokemon.identity == identity)
        embed = await asyncio.to_thread(pokemon.get_embed)
    except Exception as e:
        await interaction.response.send_message(f"Error: {e}",ephemeral=True)
        print(f"Error: {e}")
        return

    await interaction.response.send_message(embed=embed,view=PokedexButtons(int(embed.footer.text)),ephemeral=True)

# --------------------------------------------------------- end of Pokemon stuff
# --------------------------------------------------------- bot stuff
    
@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        for command in synced: print(f"synced {command.name}")
        print(f"synced {len(synced)} commands")
    except Exception as e:
        print(e)

@bot.event
async def on_message(message):
    if message.author.bot: return

    memberID = message.author.id

    try:
        user = asyncio.to_thread(User.get_by_id,memberID)
    except User.DoesNotExist:
        user = asyncio.to_thread(User.create,id = memberID)

    await asyncio.to_thread(user.add_xp,1)

    await bot.process_commands(message)

# --------------------------------------------------------- end of bot stuff
# --------------------------------------------------------- weekly and leaderboard stuff

#todo continue refactor here

@bot.tree.command(name="leaderboard",description="Shows the leaderboard",guild=GUILD)
@app_commands.describe(type="The time frame to use when looking up the leaderboard")
@app_commands.describe(date="A date in mm-dd-yyyy format. This will return the leaderboard for that week")
async def leaderboard(interaction: discord.Interaction, type: Literal["This Week","All Time","Specific"], date: str = "None"):
    print(f"{interaction.user.display_name} ran /leaderboard {type} {date}")

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

    await interaction.response.send_message(embed=embed,ephemeral=True)

    mydb.close()

@bot.tree.command(name="weekly",description="Get the current weekly hunt",guild=GUILD)
async def weekly(interaction: discord.Interaction):
    print(f"{interaction.user.display_name} ran /weekly")
    mydb.connect()
    
    try:
        weekly = Week.select().order_by(Week.endDate.desc()).limit(1).get()
        
        if weekly.endDate < datetime.now():
            await interaction.response.send_message("Weekly has not been started yet! Starting a new one now!",ephemeral=True)
            mydb.close()
            embed = await startWeekly(interaction.user.id)
        else:
            mydb.close()
            embed = await getWeeklyEmbed()
    except Week.DoesNotExist:
        await interaction.response.send_message("No Weekly found! Starting a new one",ephemeral=True)
        mydb.close()
        embed = await startWeekly(interaction.user.id)

    await interaction.response.send_message(embed=embed,ephemeral=True)

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

    return await getWeeklyEmbed()

# --------------------------------------------------------- end of weekly and leaderboard stuff

bot.run(os.getenv("BOT_TOKEN"))