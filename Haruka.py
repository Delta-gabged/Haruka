import time
import discord
from discord.ext import commands
import asyncio
import re
import random
import os
import json
import datetime
import pytz

bot = commands.Bot(command_prefix=['!'], description='NijigasakiBot')
global deletedMessages
deletedMessages=[]
global target
target=None
with open('Resources.json', 'r') as file_object:
	config=json.load(file_object)

def is_admin(ctx):
	try:
		if ctx.author.permissions_in(ctx.message.channel).administrator:
			return True
		return False
	except Exception as e:
		print(e)
		return False
	
@bot.event
async def on_ready():
	print('Logged in as:\n{0} (ID: {0.id})'.format(bot.user))
	await bot.change_presence(activity = discord.Game("Making lunch for Kanata", type=1))

#@bot.event
async def on_member_join(member):
	general = bot.get_channel(config["generalCh"])
	rules = bot.get_channel(config["rulesCh"])
	guild = bot.get_guild(config["nijiCord"])
	await general.send(config["welcome"].format(member.display_name, rules.mention))
	log=bot.get_channel(config["logCh"])
	baseRole=discord.utils.find(lambda x: x.name == "Idol Club Applicant", guild.roles)
	await member.add_roles(baseRole)
	await log.send(embed=genLog(member,"has joined the server."))

#@bot.event
async def on_member_remove(member):
	log=bot.get_channel(config["logCh"])
	await log.send(embed=genLog(member,"has left the server."))

#@bot.event
async def on_message_delete(message):
	log=bot.get_channel(config["logCh"])
	await log.send("{0} deleted the message:\n{1}".format(message.author.display_name,message.content))
	print("{0} deleted the message:\n{1}".format(message.author.display_name,message.content))
	

def inBotMod(msg):
	return msg.channel.id==config["ModBotCH"]

def genLog(member, what):
	embd=discord.Embed()
	embd.title=member.display_name
	embd.description=what
	embd=embd.set_thumbnail (url=member.avatar_url)
	embd.type="rich"
	embd.timestamp=datetime.datetime.now(pytz.timezone('US/Eastern'))
	embd=embd.add_field(name = 'Discord Username', value = str(member))
	embd=embd.add_field(name = 'id', value = member.id)
	embd=embd.add_field(name = 'Joined', value = member.joined_at)
	embd=embd.add_field(name = 'Roles', value = ', '.join(map(lambda x: x.name, member.roles)))
	embd=embd.add_field(name = 'AccountCreated', value = member.created_at)
	return embd

def isTarget(msg):
	global target
	if msg.author==target:
		return True
	return False

@bot.command(hidden=True)
@commands.check(is_admin)
async def purge(ctx,*,msgs:int=10):
	rxnMsg=await ctx.send("Are you sure you want to delete the last {0} messages on the server? react {1} to confirm or {2} to cancel.".format(str(msgs),u"\U0001F5D1", "🚫" ))
	await rxnMsg.add_reaction(u"\U0001F5D1")
	await rxnMsg.add_reaction("🚫")
	async with ctx.message.channel.typing():
		try:
			rxn, user=await bot.wait_for('reaction_add', check=adminRxn, timeout=60.0)
			if str(rxn.emoji)==u"\U0001F5D1":
				await ctx.message.channel.purge(limit = msgs)
				await ctx.send("purge complete")
			else:
				await ctx.send("cancelling the purge")
		except asyncio.TimeoutError:
			await rxnMsg.delete()

	return

def adminRxn(rxn, user):
	print(rxn.emoji)
	if user.permissions_in(bot.get_channel(config["generalCh"])).administrator and not user.bot:
		if str(rxn.emoji) in [u"\U0001F5D1","🔨","🚫"]:
			return True
	return False

@bot.command(hidden=True)
@commands.check(is_admin)
async def ban(ctx,*,person: discord.Member):
	global target
	while target!=None:
		time.sleep(10)
	rxnMsg=await ctx.send("React {1} to purge {0} and ban then, react 🔨 to only ban them and react 🚫 to cancel".format(str(person),u"\U0001F5D1"))
	async with ctx.message.channel.typing():
		await rxnMsg.add_reaction(u"\U0001F5D1")
		await rxnMsg.add_reaction("🔨")
		await rxnMsg.add_reaction("🚫")
		try:
			rxn, user=await bot.wait_for('reaction_add', check=adminRxn, timeout=60.0)
			if str(rxn.emoji)==u"\U0001F5D1":
				target = person
				for ch in ctx.message.guild.text_channels:
					await ch.purge(check=isTarget)
				target=None
				await ctx.send("purge complete")
				await person.ban()
			elif str(rxn.emoji)=="🔨":
				await person.ban()
			else:
				await ctx.send("cancelling the ban")
		except asyncio.TimeoutError:
			await rxnMsg.delete()
		return


@bot.command(hidden=True)
@commands.check(is_admin)
async def prune(ctx,*,person: discord.Member):
	global target
	while target!=None:
		time.sleep(10)
	rxnMsg=await ctx.send("Are you sure you want to delete all messages in the past 2 weeks by {0}? React {1} to confirm or 🚫 to cancel.".format(str(person),u"\U0001F5D1"))
	async with ctx.message.channel.typing():
		await rxnMsg.add_reaction(u"\U0001F5D1")
		await rxnMsg.add_reaction("🚫")
		try:
			rxn, user=await bot.wait_for('reaction_add', check=adminRxn, timeout=60.0)
			if str(rxn.emoji)==u"\U0001F5D1":
				target = person
				for ch in ctx.message.guild.text_channels:
					await ch.purge(check=isTarget)
				target=None
				await ctx.send("purge complete")
			elif str(rxn.emoji)=="🚫":
				await ctx.send("cancelling prune")
		except asyncio.TimeoutError:
			await rxnMsg.delete()
		return

#@bot.command(hidden=True)
@commands.check(is_admin)
async def undelete(ctx, number=5):
	num=int(number)
	if len(deletedMessages)<1:
		await ctx.send("no messages since my last restart")
	for msg in deletedMessages[-1*num:]:
		await ctx.send(content = "{0} sent:\n`{1}`\n with attachments:\n{2}".format( msg.author.display_name, msg.clean_content, "\n".join( map( lambda x: x.url, msg.attachments))))

#@bot.command()
async def uwu(ctx):
	msg=genLog(ctx.message.author,"has left the guild.")
	await ctx.send(embed=msg)

#@bot.command()
async def info(ctx, member: discord.Member = None):
	if member == None:
		await ctx.send(embed=genLog(ctx.message.author, "Info on {0}".format(ctx.message.author.display_name)))
	else:
		await ctx.send(embed=genLog(member, "info on {0}".format(member.display_name)))

@bot.command(name="best")
async def best(ctx, *, role):
	print (role)
	roleNames=config["girls"]
	if role.title() not in roleNames:
		await ctx.send("Not a valid role.")
		return
	member = ctx.message.author
	requestedRole = discord.utils.find(lambda x: x.name.lower() == role.lower(), ctx.guild.roles)
	roles = list(filter(lambda x: x.name.title() in roleNames, ctx.guild.roles))
	await member.remove_roles(*roles, atomic=True)
	await member.add_roles(requestedRole)




#@bot.command(name="pronoun")
async def Pronoun(ctx, action="", pronoun=""):
	"""please say '!pronoun add ' or '!pronoun remove ' followed by 'he', 'she', or 'they'. If you want a different pronoun added, feel free to contact a mod."""
	print(action)
	print(pronoun)
	if action=="" or pronoun=="":
		await ctx.send("please say '!pronoun add ' or '!pronoun remove ' followed by 'he', 'she', or 'they'. If you want a different pronoun added, feel free to contact a mod.")
		return
	
	if pronoun.lower().strip() == 'they':
		role = discord.utils.find(lambda x: x.name == "They/Them")
	elif pronoun.lower().strip() == 'she':
		role = discord.utils.find(lambda x: x.name == "She/Her")
	elif pronoun.lower().strip() == 'he':
		role = discord.utils.find(lambda x: x.name == "He/Him")
	else:
		await ctx.send("please say '!pronoun add ' or '!pronoun remove ' followed by 'he', 'she', or 'they'. If you want a different pronoun added, feel free to contact a mod.")
	
	if action.strip().lower() == "add":
		await ctx.member.add_roles(role)
	elif action.strip().lower() == "remove":
		await ctx.member.remove_roles(role)
	else:
		await ctx.send("please say '!pronoun add ' or '!pronoun remove ' followed by 'he', 'she', or 'they'. If you want a different pronoun added, feel free to contact a mod.")

with open("token.txt","r") as file_object:
	bot.run(file_object.read().strip())