import discord
from discord.ext import commands
from discord import app_commands
from datetime import timedelta
import random
import time
import json
import os
import asyncio

# =========================
# SETTINGS
# =========================

TOKEN = "PUT_YOUR_NEW_BOT_TOKEN_HERE"

# Put YOUR Discord user ID here
OWNER_ID = 123456789012345678

PREFIX = "sp!"
DATA_FILE = "speedo_access.json"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix=PREFIX,
    intents=intents,
    help_command=None
)

START_TIME = time.time()


# =========================
# ACCESS SYSTEM
# =========================

def load_access():
    if not os.path.exists(DATA_FILE):
        return set()

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return {int(x) for x in json.load(f)}
    except:
        return set()


access_users = load_access()


def save_access():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(list(access_users), f)


def has_access(member):
    return (
        member.id == OWNER_ID
        or member.guild_permissions.administrator
        or member.id in access_users
    )


async def check_access(ctx):
    if has_access(ctx.author):
        return True

    await ctx.send("❌ You don't have access to Speedo.")
    return False


# =========================
# READY
# =========================

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"Slash sync error: {e}")

    print(f"Logged in as {bot.user}")
    print("sᴘᴇᴇᴅᴏ is online!")


# ============================================================
# 1-20 MODERATION
# ============================================================

@bot.command()
async def kick(ctx, member: discord.Member, *, reason="No reason provided"):
    if not await check_access(ctx): return
    await member.kick(reason=reason)
    await ctx.send(f"👢 Kicked {member.mention}")


@bot.command()
async def ban(ctx, member: discord.Member, *, reason="No reason provided"):
    if not await check_access(ctx): return
    await member.ban(reason=reason)
    await ctx.send(f"🔨 Banned {member.mention}")


@bot.command()
async def unban(ctx, user_id: int):
    if not await check_access(ctx): return

    try:
        user = await bot.fetch_user(user_id)
        await ctx.guild.unban(user)
        await ctx.send(f"✅ Unbanned {user}")
    except:
        await ctx.send("❌ User could not be unbanned.")


@bot.command()
async def timeout(
    ctx,
    member: discord.Member,
    minutes: int = 10,
    *,
    reason="No reason provided"
):
    if not await check_access(ctx): return

    if minutes < 1 or minutes > 40320:
        return await ctx.send("❌ Minutes must be 1-40320.")

    await member.timeout(
        timedelta(minutes=minutes),
        reason=reason
    )

    await ctx.send(
        f"⏱️ {member.mention} timed out for {minutes} minutes."
    )


@bot.command()
async def untimeout(ctx, member: discord.Member):
    if not await check_access(ctx): return

    await member.timeout(None)
    await ctx.send(f"✅ Timeout removed from {member.mention}")


@bot.command()
async def warn(ctx, member: discord.Member, *, reason="No reason"):
    if not await check_access(ctx): return

    warnings_data.setdefault(member.id, [])
    warnings_data[member.id].append(reason)

    await ctx.send(
        f"⚠️ {member.mention} warned: {reason}"
    )


warnings_data = {}


@bot.command()
async def warnings(ctx, member: discord.Member):
    if not await check_access(ctx): return

    warns = warnings_data.get(member.id, [])

    if not warns:
        return await ctx.send("✅ No warnings.")

    text = "\n".join(
        f"{i+1}. {reason}"
        for i, reason in enumerate(warns)
    )

    await ctx.send(text)


@bot.command()
async def clear(ctx, amount: int = 10):
    if not await check_access(ctx): return

    if amount < 1 or amount > 100:
        return await ctx.send("❌ Use 1-100.")

    messages = await ctx.channel.purge(limit=amount + 1)

    await ctx.send(
        f"🧹 Deleted {len(messages)-1} messages.",
        delete_after=3
    )


@bot.command()
async def lock(ctx):
    if not await check_access(ctx): return

    overwrite = ctx.channel.overwrites_for(
        ctx.guild.default_role
    )

    overwrite.send_messages = False

    await ctx.channel.set_permissions(
        ctx.guild.default_role,
        overwrite=overwrite
    )

    await ctx.send("🔒 Channel locked.")


@bot.command()
async def unlock(ctx):
    if not await check_access(ctx): return

    overwrite = ctx.channel.overwrites_for(
        ctx.guild.default_role
    )

    overwrite.send_messages = None

    await ctx.channel.set_permissions(
        ctx.guild.default_role,
        overwrite=overwrite
    )

    await ctx.send("🔓 Channel unlocked.")


@bot.command()
async def slowmode(ctx, seconds: int = 0):
    if not await check_access(ctx): return

    if seconds < 0 or seconds > 21600:
        return await ctx.send("❌ Use 0-21600 seconds.")

    await ctx.channel.edit(slowmode_delay=seconds)

    await ctx.send(
        f"🐌 Slowmode: {seconds}s"
    )


@bot.command()
async def mute(ctx, member: discord.Member):
    if not await check_access(ctx): return

    await member.timeout(
        timedelta(minutes=10),
        reason="Speedo mute"
    )

    await ctx.send(f"🔇 Muted {member.mention}")


@bot.command()
async def unmute(ctx, member: discord.Member):
    if not await check_access(ctx): return

    await member.timeout(None)
    await ctx.send(f"🔊 Unmuted {member.mention}")


@bot.command()
async def softban(
    ctx,
    member: discord.Member,
    *,
    reason="No reason"
):
    if not await check_access(ctx): return

    await member.ban(
        reason=reason,
        delete_message_seconds=86400
    )

    user = await bot.fetch_user(member.id)

    await ctx.guild.unban(
        user,
        reason="Speedo softban"
    )

    await ctx.send(f"🔨 Soft-banned {member.mention}")


@bot.command()
async def purge(ctx, amount: int = 10):
    if not await check_access(ctx): return

    if amount < 1 or amount > 100:
        return await ctx.send("❌ Use 1-100.")

    messages = await ctx.channel.purge(
        limit=amount
    )

    await ctx.send(
        f"🧹 Deleted {len(messages)} messages.",
        delete_after=3
    )


@bot.command()
async def nick(
    ctx,
    member: discord.Member,
    *,
    nickname=None
):
    if not await check_access(ctx): return

    await member.edit(nick=nickname)

    await ctx.send("✅ Nickname changed.")


@bot.command()
async def role(
    ctx,
    member: discord.Member,
    role: discord.Role
):
    if not await check_access(ctx): return

    await member.add_roles(role)

    await ctx.send(
        f"✅ Added {role.mention} to {member.mention}"
    )


@bot.command()
async def removerole(
    ctx,
    member: discord.Member,
    role: discord.Role
):
    if not await check_access(ctx): return

    await member.remove_roles(role)

    await ctx.send(
        f"✅ Removed {role.mention}"
    )


@bot.command()
async def announce(ctx, *, text):
    if not await check_access(ctx): return

    await ctx.send(
        f"📢 **ANNOUNCEMENT**\n{text}"
    )


@bot.command()
async def warnlist(ctx):
    if not await check_access(ctx): return

    if not warnings_data:
        return await ctx.send("No warnings.")

    result = []

    for user_id, warns in warnings_data.items():
        result.append(
            f"<@{user_id}> — {len(warns)} warning(s)"
        )

    await ctx.send("\n".join(result))


# ============================================================
# 21-40 SERVER
# ============================================================

@bot.command()
async def serverinfo(ctx):
    if not await check_access(ctx): return

    g = ctx.guild

    await ctx.send(
        f"**{g.name}**\n"
        f"ID: `{g.id}`\n"
        f"Members: `{g.member_count}`\n"
        f"Owner: <@{g.owner_id}>"
    )


@bot.command()
async def userinfo(ctx, member: discord.Member = None):
    if not await check_access(ctx): return

    member = member or ctx.author

    await ctx.send(
        f"**{member}**\n"
        f"ID: `{member.id}`\n"
        f"Bot: `{member.bot}`"
    )


@bot.command()
async def avatar(ctx, member: discord.Member = None):
    if not await check_access(ctx): return

    member = member or ctx.author

    await ctx.send(member.display_avatar.url)


@bot.command()
async def roleinfo(ctx, role: discord.Role):
    if not await check_access(ctx): return

    await ctx.send(
        f"**{role.name}**\n"
        f"ID: `{role.id}`\n"
        f"Members: `{len(role.members)}`"
    )


@bot.command()
async def channelinfo(
    ctx,
    channel: discord.TextChannel = None
):
    if not await check_access(ctx): return

    channel = channel or ctx.channel

    await ctx.send(
        f"**#{channel.name}**\n"
        f"ID: `{channel.id}`"
    )


@bot.command()
async def createchannel(ctx, *, name):
    if not await check_access(ctx): return

    channel = await ctx.guild.create_text_channel(name)

    await ctx.send(
        f"✅ Created {channel.mention}"
    )


@bot.command()
async def deletechannel(
    ctx,
    channel: discord.TextChannel = None
):
    if not await check_access(ctx): return

    channel = channel or ctx.channel

    await channel.delete()


@bot.command()
async def createrole(ctx, *, name):
    if not await check_access(ctx): return

    role = await ctx.guild.create_role(
        name=name
    )

    await ctx.send(
        f"✅ Created {role.mention}"
    )


@bot.command()
async def deleterole(ctx, role: discord.Role):
    if not await check_access(ctx): return

    await role.delete()

    await ctx.send("✅ Role deleted.")


@bot.command()
async def renamechannel(ctx, *, name):
    if not await check_access(ctx): return

    await ctx.channel.edit(name=name)

    await ctx.send("✅ Channel renamed.")


@bot.command()
async def topic(ctx, *, text):
    if not await check_access(ctx): return

    await ctx.channel.edit(topic=text)

    await ctx.send("✅ Topic changed.")


@bot.command()
async def membercount(ctx):
    if not await check_access(ctx): return

    await ctx.send(
        f"👥 Members: {ctx.guild.member_count}"
    )


@bot.command()
async def channels(ctx):
    if not await check_access(ctx): return

    text = "\n".join(
        f"#{c.name}"
        for c in ctx.guild.text_channels
    )

    await ctx.send(text[:1900])


@bot.command()
async def roles(ctx):
    if not await check_access(ctx): return

    text = "\n".join(
        role.name
        for role in ctx.guild.roles
    )

    await ctx.send(text[:1900])


@bot.command()
async def emojiinfo(ctx, emoji: discord.Emoji):
    if not await check_access(ctx): return

    await ctx.send(
        f"Emoji: `{emoji.name}`\n"
        f"ID: `{emoji.id}`"
    )


@bot.command()
async def invite(ctx):
    if not await check_access(ctx): return

    invite = await ctx.channel.create_invite(
        max_age=3600,
        max_uses=1
    )

    await ctx.send(str(invite))


@bot.command()
async def say(ctx, *, text):
    if not await check_access(ctx): return

    await ctx.send(text)


@bot.command()
async def embed(ctx, *, text):
    if not await check_access(ctx): return

    e = discord.Embed(
        description=text
    )

    await ctx.send(embed=e)


@bot.command()
async def poll(ctx, *, question):
    if not await check_access(ctx): return

    msg = await ctx.send(
        f"📊 **Poll**\n{question}\n\n"
        "👍 Yes\n"
        "👎 No"
    )

    await msg.add_reaction("👍")
    await msg.add_reaction("👎")


@bot.command()
async def servericon(ctx):
    if not await check_access(ctx): return

    if ctx.guild.icon:
        await ctx.send(ctx.guild.icon.url)
    else:
        await ctx.send("No server icon.")


# ============================================================
# 41-60 FUN
# ============================================================

@bot.command()
async def choose(ctx, *, choices):
    if not await check_access(ctx): return

    options = [
        x.strip()
        for x in choices.split("|")
        if x.strip()
    ]

    if len(options) < 2:
        return await ctx.send(
            "❌ Separate choices using `|`."
        )

    await ctx.send(
        f"🎯 I choose **{random.choice(options)}**"
    )


@bot.command(name="8ball")
async def eightball(ctx, *, question):
    if not await check_access(ctx): return

    answers = [
        "Yes.",
        "No.",
        "Maybe.",
        "Definitely.",
        "Ask again later."
    ]

    await ctx.send(
        f"🎱 {random.choice(answers)}"
    )


@bot.command()
async def coinflip(ctx):
    if not await check_access(ctx): return

    await ctx.send(
        f"🪙 {random.choice(['Heads', 'Tails'])}"
    )


@bot.command()
async def dice(ctx):
    if not await check_access(ctx): return

    await ctx.send(
        f"🎲 {random.randint(1, 6)}"
    )


@bot.command()
async def roll(ctx, sides: int = 100):
    if not await check_access(ctx): return

    if sides < 2:
        return await ctx.send(
            "❌ Minimum is 2."
        )

    await ctx.send(
        f"🎲 {random.randint(1, sides)}"
    )


@bot.command()
async def random(ctx, minimum: int = 1, maximum: int = 100):
    if not await check_access(ctx): return

    if minimum > maximum:
        minimum, maximum = maximum, minimum

    await ctx.send(
        str(random.randint(minimum, maximum))
    )


@bot.command()
async def ship(
    ctx,
    user1: discord.Member,
    user2: discord.Member
):
    if not await check_access(ctx): return

    score = random.randint(0, 100)

    await ctx.send(
        f"💞 {user1.display_name} + "
        f"{user2.display_name} = **{score}%**"
    )


@bot.command()
async def rate(ctx, *, thing):
    if not await check_access(ctx): return

    await ctx.send(
        f"⭐ **{thing}** = "
        f"{random.randint(0,10)}/10"
    )


@bot.command()
async def roast(ctx, member: discord.Member = None):
    if not await check_access(ctx): return

    member = member or ctx.author

    await ctx.send(
        f"🔥 {member.mention}, "
        "your Wi-Fi has more personality than you 😂"
    )


@bot.command()
async def compliment(
    ctx,
    member: discord.Member = None
):
    if not await check_access(ctx): return

    member = member or ctx.author

    await ctx.send(
        f"✨ {member.mention}, you're awesome!"
    )


@bot.command()
async def joke(ctx):
    if not await check_access(ctx): return

    await ctx.send(
        random.choice([
            "Why did the computer get cold? "
            "It left its Windows open.",
            "Why was the math book sad? "
            "It had too many problems."
        ])
    )


@bot.command()
async def fact(ctx):
    if not await check_access(ctx): return

    await ctx.send(
        random.choice([
            "Octopuses have three hearts.",
            "Bananas are botanically berries."
        ])
    )


@bot.command()
async def rps(ctx, choice):
    if not await check_access(ctx): return

    choice = choice.lower()

    if choice not in [
        "rock",
        "paper",
        "scissors"
    ]:
        return await ctx.send(
            "Use rock, paper, or scissors."
        )

    bot_choice = random.choice([
        "rock",
        "paper",
        "scissors"
    ])

    if choice == bot_choice:
        result = "Tie!"
    elif (
        (choice == "rock" and bot_choice == "scissors")
        or
        (choice == "paper" and bot_choice == "rock")
        or
        (choice == "scissors" and bot_choice == "paper")
    ):
        result = "You win!"
    else:
        result = "I win!"

    await ctx.send(
        f"🪨 You: {choice}\n"
        f"🤖 Me: {bot_choice}\n"
        f"**{result}**"
    )


@bot.command()
async def reverse(ctx, *, text):
    if not await check_access(ctx): return

    await ctx.send(text[::-1])


@bot.command()
async def mock(ctx, *, text):
    if not await check_access(ctx): return

    result = "".join(
        char.upper() if i % 2 else char.lower()
        for i, char in enumerate(text)
    )

    await ctx.send(result)


@bot.command()
async def ascii(ctx, *, text):
    if not await check_access(ctx): return

    await ctx.send(f"```{text}```")


@bot.command()
async def wyr(ctx):
    if not await check_access(ctx): return

    await ctx.send(
        random.choice([
            "Would you rather fly or be invisible?",
            "Would you rather have unlimited money "
            "or unlimited free time?"
        ])
    )


@bot.command()
async def color(ctx):
    if not await check_access(ctx): return

    await ctx.send(
        f"🎨 #{random.randint(0, 0xFFFFFF):06X}"
    )


@bot.command()
async def flip(ctx, *, text):
    if not await check_access(ctx): return

    await ctx.send(
        text[::-1]
    )


@bot.command()
async def number(
    ctx,
    minimum: int = 1,
    maximum: int = 100
):
    if not await check_access(ctx): return

    await ctx.send(
        str(random.randint(minimum, maximum))
    )


# ============================================================
# 61-70 UTILITY
# ============================================================

@bot.command()
async def help(ctx):
    if not await check_access(ctx): return

    await ctx.send(
        "📚 Use `/help` or check your Speedo command list."
    )


@bot.command()
async def ping(ctx):
    if not await check_access(ctx): return

    await ctx.send(
        f"🏓 {round(bot.latency * 1000)}ms"
    )


@bot.command()
async def uptime(ctx):
    if not await check_access(ctx): return

    seconds = int(
        time.time() - START_TIME
    )

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    await ctx.send(
        f"⏱️ {hours}h {minutes}m"
    )


@bot.command()
async def botinfo(ctx):
    if not await check_access(ctx): return

    await ctx.send(
        f"**sᴘᴇᴇᴅᴏ**\n"
        f"Servers: `{len(bot.guilds)}`\n"
        f"Commands: `80`"
    )


@bot.command()
async def time(ctx):
    if not await check_access(ctx): return

    await ctx.send(
        discord.utils.utcnow().strftime(
            "%Y-%m-%d %H:%M UTC"
        )
    )


@bot.command()
async def id(ctx, member: discord.Member = None):
    if not await check_access(ctx): return

    member = member or ctx.author

    await ctx.send(
        f"🆔 `{member.id}`"
    )


@bot.command()
async def permissions(ctx):
    if not await check_access(ctx): return

    p = ctx.author.guild_permissions

    await ctx.send(
        f"Administrator: `{p.administrator}`\n"
        f"Manage Messages: `{p.manage_messages}`\n"
        f"Manage Roles: `{p.manage_roles}`"
    )


@bot.command()
async def rolelist(ctx):
    if not await check_access(ctx): return

    await ctx.send(
        "\n".join(
            r.name for r in ctx.guild.roles
        )[:1900]
    )


@bot.command()
async def channelid(ctx):
    if not await check_access(ctx): return

    await ctx.send(
        f"`{ctx.channel.id}`"
    )


@bot.command()
async def serverid(ctx):
    if not await check_access(ctx): return

    await ctx.send(
        f"`{ctx.guild.id}`"
    )


# ============================================================
# 71-75 OWNER
# ============================================================

@bot.command()
async def grantaccess(
    ctx,
    member: discord.Member
):
    if ctx.author.id != OWNER_ID:
        return await ctx.send(
            "❌ Owner only."
        )

    access_users.add(member.id)
    save_access()

    await ctx.send(
        f"✅ {member.mention} now has access "
        "**to ALL 80 Speedo commands.**"
    )


@bot.command()
async def revokeaccess(
    ctx,
    member: discord.Member
):
    if ctx.author.id != OWNER_ID:
        return await ctx.send(
            "❌ O
