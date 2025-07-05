import aiohttp
import asyncio
import json
import re
import os
from discord.ext import commands
import discord

token = os.environ.get("DISCORD_TOKEN")

if token is None:
    raise ValueError("DISCORD_TOKEN environment variable is not set.")

intents = discord.Intents.default()
client = commands.Bot(command_prefix="!", intents=intents)

CONFIG_FILE = "config.json"

with open(CONFIG_FILE) as f:
    config = json.load(f)

API_URL = "https://appy.bot/api/trpc/applicationSubmissions.statistics,applicationSubmissions.getPaginated?batch=1&input=%7B%220%22%3A%7B%22json%22%3A%7B%22guildId%22%3A%22711269728097927259%22%7D%7D%2C%221%22%3A%7B%22json%22%3A%7B%22guildId%22%3A%22711269728097927259%22%2C%22status%22%3A%22ALL%22%2C%22limit%22%3A20%2C%22page%22%3A1%7D%7D%7D"

TEAM_MAPPING = {
    "GE": "<@&798708370298372116>",
    "Worship": "<@&711298940292825108>",
    "Production": "<@&711298903730814997>",
    "Media": "<@&806674959141175327>",
    "Pastoral": "<@&982032570856407090>",
}

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

    # Auto-create message if message_id is missing or zero
    if config["message_id"] == 0:
        try:
            channel = await client.fetch_channel(config["channel_id"])
            msg = await channel.send(generate_status_message())
            config["message_id"] = msg.id
            save_config()
            print(f"Status message created and saved with ID {msg.id}")
        except Exception as e:
            print(f"Failed to create status message: {e}")

def save_config():
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

def generate_status_message(total=0, accepted=0, pending=0, denied=0):
    return (
        "**# <:gracechurch:1175897908965540010> | Volunteer Applications Are Open!**\n"
        "__Grace Church is *For Young People, **By Young People.***__\n\n"
        "If you're interested in serving as part of our ministry as a volunteer, this is the place to do it! We're looking for folks who love Jesus and want to use their God-given gifts and talents to help all in Grace Church to Know and Grow as they themselves Serve!\n\n"

        f"Current Pending Applications: `{pending}`\n"
        
        "# Our Volunteer Teams:\n"
        "<@&798708370298372116> **Guest Experience -** Provides hospitality and support by welcoming guests, answering questions, and fostering a warm, family-like atmosphere within the church community.\n\n"
        "<@&711298940292825108> - Leads the congregation in musical worship, committing to rehearsals and spiritual connection through song before, during, and after services.\n\n"
        "<@&711298903730814997> - Manages in-game stage lighting during services, ensuring smooth worship and sermon experiences through teamwork and communication.\n\n"
        "<@&806674959141175327> - Captures and creates media content for Grace Media, using creativity and collaboration to support ministry projects both in and out of the game.\n\n"
        "<@&982032570856407090> - Serves as spiritual leaders and counselors, focusing on teaching, outreach, and guiding members and guests in their walk with God.\n\n"
        "# ---------------\n"
        "Volunteer teams are led by various <@&715619118769766521> who serve by helping others serve!\n\n"
        "1. If you'd like to apply, you can do so below!\n"
        "2. Please be patient, as we take our time to review all applications personally.\n"
        "3. If your application is not accepted, please wait to reapply the following week.\n"
        "4. Please write your application yourself, and do not copy directly from AI."
    )

@client.slash_command(description="Update the volunteer application status message.")
async def update_status(ctx):
    await ctx.defer()

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(API_URL) as resp:
                if resp.status != 200:
                    await ctx.respond(f"Failed to fetch data from API. Status code: {resp.status}")
                    return
                data = await resp.json()

        stats = data["result"]["data"]["json"]
        total = stats["totalCount"]
        accepted = stats["acceptedCount"]
        pending = stats["pendingCount"]
        denied = stats["deniedCount"]

        status_message = generate_status_message(total, accepted, pending, denied)

        channel = await client.fetch_channel(config["channel_id"])
        message = await channel.fetch_message(config["message_id"])
        await message.edit(content=status_message)

        await ctx.respond("Volunteer status message updated successfully.")

    except Exception as e:
        print(f"Error: {e}")
        await ctx.respond("An error occurred while updating the status.")

@client.slash_command(description="Toggle [FULL] tag for a volunteer team.")
async def toggle_full(ctx, team: discord.Option(str, "Select the team", choices=list(TEAM_MAPPING.keys()))):
    await ctx.defer()

    try:
        channel = await client.fetch_channel(config["channel_id"])
        message = await channel.fetch_message(config["message_id"])
        content = message.content

        team_mention = TEAM_MAPPING[team]

        full_pattern = rf"\*\*\[FULL\]\*\*\s{re.escape(team_mention)}"
        normal_pattern = rf"(?<!\*\*\[FULL\]\*\*\s){re.escape(team_mention)}"

        if re.search(full_pattern, content):
            new_content = re.sub(full_pattern, team_mention, content)
            await message.edit(content=new_content)
            await ctx.respond(f"`[FULL]` removed from **{team.capitalize()}**.")
        else:
            new_content = re.sub(normal_pattern, f"**[FULL]** {team_mention}", content, count=1)
            await message.edit(content=new_content)
            await ctx.respond(f"`[FULL]` added to **{team.capitalize()}**.")

    except Exception as e:
        print(f"Error: {e}")
        await ctx.respond("An error occurred while toggling [FULL].")

client.run(token)
