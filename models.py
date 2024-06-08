import asyncio
import math
from peewee import Model,CharField,IntegerField,BooleanField,ForeignKeyField,BigIntegerField,DateField,DateTimeField,fn
from playhouse.mysql_ext import MySQLConnectorDatabase
from datetime import date
from bot import discordColors, bot
import os,discord
import random as rand


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

    def get_embed(self) -> discord.Embed:

        try:
            mydb.connect()

            gamePokemon = GamePokemon.select(GamePokemon, Pokemon,Game).join(Pokemon).switch(GamePokemon).join(Game).where(Pokemon.id == self.id)
        except Exception as e:
            raise Exception(e)
        finally:
            mydb.close()
        
        games = []
        games = [gameLine.game.name for gameLine in gamePokemon]
        name_parts = [self.name]

        if self.varient: name_parts.append(self.varient)
        if self.isFemale == 1: name_parts.append("Female")
        if len(name_parts) > 1: name = f"{self.name} ({" ".join(name_parts[1:])})"
        else: name = self.name

        types = [self.type1]
        if self.type2 != "NA": types.append(self.type2)
        
        embed = discord.Embed(
            title=name,
            description=self.identity,
            url='https://pokemondb.net/pokedex/' + str(self.national),
            color=discordColors[self.color]
        )
        embed.set_image(url="https://github.com/okwurt/dextracker/blob/main/sprites/games/home/shiny/"+ self.identity +".png?raw=true")
        embed.add_field(name = "Types" if len(types) > 1 else "Type", value = "\n".join(types) if len(types) > 1 else self.type1, inline = True)
        embed.add_field(name = "Color", value = self.color, inline = True)
        embed.add_field(name = "Generation", value = self.generation, inline = True)
        embed.add_field(name = "National Pokedex Number", value = self.national, inline = True)
        embed.add_field(name = "Available Games", value = "None" if games.__len__() == 0 else "\n".join(games), inline = False)
        embed.set_footer(text=self.id)

        return embed

    @staticmethod
    def get_random():
        return Pokemon.select().order_by(fn.RAND()).first()

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

    def xp_for_level(self, level = None) -> int:
        if level is None: level = self.level
        if level == 100: return 0

        if level <= 5: return math.floor(4 * level**3 / 5 + 30)
        else: return math.floor(4 * level**3 / 5)

    def add_xp(self, amount: int, can_hit_odds: bool = True) -> bool:
        if self.level == 100: return False

        random_number = rand.randint(1,8192)

        if can_hit_odds and  random_number == 2024:
            channel = bot.get_channel(1237051742781313066)
            member = bot.get_user(self.id)
            asyncio.create_task(channel.send(f"{member.mention} got lucky and got shiny XP! Thats 10 times the normal amount of xp!"))
            self.shinyXpTimesHit = self.shinyXpTimesHit + 1
            self.shinyXpEarned = self.shinyXpEarned + amount * 9
            self.save()

            amount = amount * 10

        xp_needed_for_next_level = self.xp_for_level()
        if self.xp + amount >= xp_needed_for_next_level:
            new_xp = self.xp + amount - xp_needed_for_next_level
            self.levelUp()

            if new_xp != 0: 
                self.add_xp(new_xp,False)
        else: 
            self.xp = self.xp + amount
            self.save()

        return True
    
    def levelUp(self):
        self.level = self.level + 1
        self.xp = 0
        self.save()

        channel = bot.get_channel(1237051742781313066)
        member = bot.get_user(self.id)
        embed = discord.Embed(
            title = member.display_name + " just hit level " + str(self.level + 1) + "!",
            description = "You need " + str(self.xpForLevel(self.level)) + " xp to level up again!" if (self.level) < 100 else "You can't level up anymore my friend. You've reached the end!",
            color= discord.Color.gold()
        )
        embed.set_author(
            name = member.display_name,
            icon_url = member.avatar.url       
        )

        asyncio.create_task(channel.send(member.mention, embed = embed))

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

async def edit_database_object(object, attribute: str, new_value:str):
    
    old_value = getattr(object,attribute)
    attribute_type = type(old_value)

    if attribute == "isFemale":
                new_value = 0 if new_value.lower() == "false" else 1

    if attribute_type == int:
        new_value = int(new_value)
    
    setattr(object,attribute,new_value)

    try:
        asyncio.to_thread(object.save)
    except Exception as e:
        raise(e)
    finally:
        mydb.close()