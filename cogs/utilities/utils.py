import asyncio
import datetime
import random
import time
import re

import discord
import pytz
import requests
import yaml
from bs4 import BeautifulSoup
from dateparser.search import search_dates
from discord.ext import commands


def getRandEmoji(emojis, query="", ctx=None):
	if ctx:
		banned = ctx.bot.config["emoteBanned"].copy()
		if ctx.message.guild:
			if ctx.message.guild.id in banned:
				banned.remove(ctx.message.guild.id)
		emojis = list(filter(lambda x: not(x.guild.id in banned) and x.available, emojis))
	if query == "":
		return random.choice(emojis)
	choices = [emoji for emoji in emojis if query.lower() in emoji.name.lower()]
	if len(choices) < 1:
		if ctx:
			emojis = list(filter(lambda x: not(x.guild.id in banned) and x.available, ctx.bot.emojis))
			choices = [emoji for emoji in emojis if query.lower() in emoji.name.lower()]
			if len(choices) < 1:
				return None
		else:
			return None
	choice = random.choice(choices)
	return choice


async def yay(ctx):
	emoji = getRandEmoji(ctx.message.guild.emojis, "yay")
	if emoji is None:
		emoji = getRandEmoji(ctx.bot.emojis, "yay")
	await ctx.message.add_reaction(emoji)


def genLog(member, what):
	embd = discord.Embed()
	embd.title = member.display_name
	embd.description = what
	embd = embd.set_thumbnail(url=member.avatar_url)
	embd.type = "rich"
	embd.timestamp = datetime.datetime.now(pytz.timezone('US/Eastern'))
	embd = embd.add_field(name='Discord Username', value=str(member))
	embd = embd.add_field(name='id', value=member.id)
	embd = embd.add_field(name='Joined', value=member.joined_at)
	embd = embd.add_field(name='Roles', value=', '.join(
		map(lambda x: x.name, member.roles)))
	embd = embd.add_field(name='Account Created', value=member.created_at)
	embd = embd.add_field(name='Profile Picture', value=member.avatar_url)
	return embd


def saveConfig(ctx):
	print("creating backup")
	with open('Resources.yaml', "r") as file:
		backup = yaml.full_load(file)
	print("saving")
	try:
		with open('Resources.yaml', 'w') as outfile:
			yaml.dump(ctx.bot.config, outfile)
	except:
		with open('Resources.yaml', 'w') as outfile:
			yaml.dump(backup, outfile)
		raise


def getInstaEmbed(token, url):
	baseHtmlEmbed = requests.get(f"https://graph.facebook.com/v8.0/instagram_oembed?url={url}&access_token={token}").json()
	if "author_name" in baseHtmlEmbed.keys():
		authorUserName = baseHtmlEmbed["author_name"]
	else:
		authorUserName = ""
	try:
		imgUrl = baseHtmlEmbed["thumbnail_url"]
	except:
		print(baseHtmlEmbed)
	soup = BeautifulSoup(baseHtmlEmbed["html"], features="html.parser")
	try:
		comment = soup.p.a.contents[0]
	except:
		comment = ""
	try:
		authorName = (soup.find_all("p")[-1]).contents[-1].contents[0].strip()
		if comment == authorName:
			comment = ""
		if "A post shared by " in authorName:
			authorName = authorName.replace("A post shared by ","")
	except:
		authorName = ""
	try:
		time = (soup.find_all("p")[1]).contents[3].contents[0]
		timestamp = search_dates(
			time, settings={'TIMEZONE': 'UTC', 'RETURN_AS_TIMEZONE_AWARE': True})[0]
	except:
		timestamp = None
	profileUrl = f"https://www.instagram.com/{authorUserName}/"
	#profileInfo = requests.get(f"{profileUrl}?__a=1").json()
	#profilePicUrl = profileInfo["graphql"]["user"]["profile_pic_url"]
	embd = discord.Embed()
	embd.type = "rich"
	embd.color = discord.Color.purple()
	embd.title = f"Instagram Post by {authorName if authorName else authorUserName}"
	embd = embd.set_author(name=f"{authorName} ({authorUserName})", url=profileUrl) if (not ("@" in authorName) and authorName) else embd.set_author(name=f"{authorName}", url=profileUrl)
	#, icon_url=profilePicUrl)
	embd = embd.set_image(url=imgUrl)
	embd.url = url
	embd.description = comment[:1023]
	if timestamp:
		embd.timestamp = timestamp[1] 
	return embd

def suppress_links(msg):
	"""Given a message, will find links using regex and surround them with <>"""
	linkRegex = re.compile(r'((http:\/\/www\.|https:\/\/www\.|http:\/\/|https:\/\/)?[a-z0-9]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,5}(:[0-9]{1,5})?(\/\S*)?)+')
	return re.sub(linkRegex, r'<\1>', msg)
