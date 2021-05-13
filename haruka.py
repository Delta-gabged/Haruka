import asyncio
import atexit
import datetime
import importlib
import io
import logging
import os
import random
import re
import sys
import time

import discord
import pytz
import requests
import yaml
from discord.ext import commands

from cogs.utilities import checks, messageHandler, utils

logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(
	filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter(
	'%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

intents = discord.Intents.default()
intents.members = True
intents.typing = False
intents.presences = False


bot = commands.Bot(command_prefix=['$'],
                   description="I may just be a bot, but I really do love my big sister Kanata! For questions about Haruka please visit 'https://discord​​.gg/qp7nuPC' or DM `Junior Mints#2525`",
                   case_insensitive=True, intents=intents)

# cogList = ['cogs.administration', 'cogs.fun', 'cogs.guildFunctions',
#            'cogs.events', 'cogs.setup', 'cogs.music', 'cogs.scheduler']
# cogNames = ['Music', 'Administration', 'Fun',
#             'GuildFunctions', 'Events', 'Setup', 'Scheduler']
cogList = ['cogs.guildFunctions']
cogNames = ['GuildFunctions']
with open('Resources.yaml', "r") as file:
	bot.config = yaml.full_load(file)
bot.messageHandler = messageHandler.MessageHandler(bot.config, bot)


async def is_admin(ctx):
	try:
		if ctx.author.permissions_in(ctx.message.channel).administrator:
			return True
		print("You do not have permission to do this. This incident will be reported.")
		return False
	except Exception as e:
		print(e)
		return False


def is_me():
	def predicate(ctx):
		return ctx.message.author.id == ctx.bot.config["owner"]
	return commands.check(predicate)


@bot.event
async def on_ready():
	x=[bot.messageHandler.initRoles(bot)]
	for cog in cogList:
		bot.load_extension(cog)
	x.append( bot.change_presence(activity=discord.Game("Making Kanata's bed!", type=1)))
	guild = bot.get_guild(bot.config["nijiCord"])
	print('Logged in as:\n{0} (ID: {0.id})'.format(bot.user))
	guildList = ""
	totalUsers = 0

	for guild in bot.guilds:
		guildList = guildList + guild.name + ", "
		totalUsers += guild.member_count
	print("Currently in the current {2} guilds: {0} with a total userbase of {1}".format(
		guildList, totalUsers, len(bot.guilds)))
	await asyncio.gather(x[0],x[1])


@bot.event
async def on_command_error(ctx, error):
	if isinstance(error, KeyboardInterrupt):
		print("is keyboard interrupt")
		await shutdown(ctx)
	ignored = (commands.CommandNotFound, commands.UserInputError)
	if hasattr(ctx.command, 'on_error'):
		print(error)
		print("Which occured in guild: {0}".format(str(ctx.guild)))
		return
	if isinstance(error, ignored):
		return
	print("error in {0}".format(str(ctx.guild)))
	try:
		logger.error("Error in {0} with message {1}".format(
			str(ctx.guild), str(ctx.message.clean_content)))
	except:
		logger.error(
			"Message that caused error either doesn't exist or can't be found")
	raise (error)


async def shutdown(ctx):
	print("shutting down messagehandler")
	bot.messageHandler.disconnect()
	print("shutting down music cog")
	music = bot.get_cog("Music")
	await music.kill()
	print("killed music cog")
	for cog in cogList:
		print("shutting down {0}".format(cog))
		cogName = cog.replace("cogs.", "")
		cogName = cogName[0].capitalize() + cogName[1:]
		await bot.get_cog(cog).shutdown(ctx)
		bot.unload_extension(cog)
		print("shut down {0}".format(cog))
	print("shutdown complete")
	x = bot.logout()
	print("logging out")
	await x



@checks.is_me()
@bot.command(hidden=True, aliases=["SR"])
async def softReset(ctx, *, selectedCogs=None):
	await bot.change_presence(activity=discord.Game("Quickly doing a soft-reset for a minor update, will be back up soon!", type=1))
	if selectedCogs is None:
		msg = True
		cogs = cogList
		selectedCogs = ""
	elif "messageHandler" in selectedCogs:
		cogs = selectedCogs.split(" ")
		cogs.remove("messageHandler")
		msg = True
	else:
		cogs = selectedCogs.split(" ")
		msg = False
	if msg:
		bot.messageHandler.disconnect()
	music = bot.get_cog("Music")
	if "cogs.music" in selectedCogs or "music" in selectedCogs:
		try:
			await music.kill()
		except:
			print("no music service active")
	print("about to unload cogs")
	for cog in cogs:
		cogName = cog.replace("cogs.", "")
		cogName = cogName[0].capitalize() + cogName[1:]
		try:
			await bot.get_cog(cogName).shutdown(ctx)
			bot.unload_extension("cogs." + cog.replace("cogs.", ""))
		except Exception as e:
			print("cannot unload cog {0} because of exception\n{1}".format(cog, e))
	print("cogs unloaded, reloading everything now")

	with open('Resources.yaml', "r") as file:
		bot.config = yaml.full_load(file)
	if msg:
		importlib.reload(messageHandler)
		bot.messageHandler = messageHandler.MessageHandler(bot.config, bot)

	for cog in cogs:
		try:
			bot.load_extension("cogs." + cog.replace("cogs.", ""))
		except Exception as e:
			await ctx.send("WARNING: cog {0} was not successfully reloaded for reason:\n`{1}`".format(cog, str(e)))
	if msg:
		try:
			await bot.messageHandler.initRoles(bot)
		except Exception as e:
			await ctx.send("WARNING: messageHandler was not successfully reloaded for reason {0}".format(str(e)))
	guild = bot.get_guild(bot.config["nijiCord"])
	print('Logged in as:\n{0} (ID: {0.id})'.format(bot.user))
	guildList = ""
	totalUsers = 0
	for guild in bot.guilds:
		guildList = guildList + guild.name + ", "
		totalUsers += guild.member_count
	print("Currently in the {2} guilds: {0} with a total userbase of {1}".format(
		guildList, totalUsers, len(bot.guilds)))
	await bot.change_presence(activity=discord.Game("Making Kanata's bed!", type=1))
	rxn = utils.getRandEmoji(bot.emojis, "hug")
	await ctx.message.add_reaction(rxn)


@checks.is_me()
@bot.command(hidden=True)
async def kill(ctx):
	print("shutting down messagehandler")
	bot.messageHandler.disconnect()
	print("shutting down music cog")
	music = bot.get_cog("music")
	await music.kill()
	print("killed music cog")
	for cog in cogList:
		print("shutting down {0}".format(cog))
		bot.unload_extension(cog)
		print("shut down {0}".format(cog))
	print("shutdown complete")
	x = bot.logout()
	print("logging out")
	await x


@bot.event
async def on_message(message):
	await bot.messageHandler.handleMessage(message, bot)
	return


@bot.command(hidden=True)
@commands.check(is_admin)
async def s(ctx, *, msg=""):
	fileList = [discord.File(io.BytesIO(await x.read(use_cached=True)), filename=x.filename) for x in ctx.message.attachments]
	await ctx.send(msg, files=fileList)
	await ctx.message.delete()


@bot.command()
async def git(ctx):
	"""Link to Haruka's source code, and information related to the development"""
	await ctx.send("Haruka was developed by Junior Mints#2525 and you can deliver any questions or comments to him. You can find the source code at https://github.com/JacobMintzer/Haruka \nIf you have any questions about it, feel free to message Junior Mints, or submit a pull request if you have any improvements you can make.")


with open("token.txt", "r") as file_object:
	bot.run(file_object.read().strip())
