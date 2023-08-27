import datetime
import discord
from discord.ext import commands
import configs

#bot = discord.Client(intents = discord.Intents.all())  
bot = commands.Bot(command_prefix="!", intents = discord.Intents.all())

ten_seconds = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds = 10)
bot.sniped_messages = {}
ROLE_NAME = ""
MOD_LOG_CHANNEL_NAME = ""
MODLOG_COLORS = {"BAN": 0xeb4034, "ADDROLE": 0xeda239, "REMOVEROLE": 0x56c470, "UNBAN": 0x4fb09e, "KICK": 0x559ced}

@bot.event
async def on_ready():
    #prints Helper is ready. when the bot is ready to use
    print(str(bot.user.name) + " is ready.")

@bot.event
async def on_message(message):
    if bot.user.mentioned_in(message):
        em = await get_help_embed()
        await message.channel.send(embed=em)
    await bot.process_commands(message)

#sending log to log channel
async def log(guild, type, user, target):

    #find the log channel in guild text channels
    log_channel = discord.utils.get(guild.text_channels, name = "logs")
    
    #returns to caller if the log channel was not found
    if not log_channel:
        return

    #searches the log channel to find the bot id to send a log
    async for iter in log_channel.history(limit = 100):
        if iter.author.id == bot.user.id:
            break

    #creates the embed frame for the log
    log_embed = discord.Embed(color = 0x56c470, timestamp = datetime.datetime.now(datetime.timezone.utc))
    log_embed.set_author(name = f"{type.capitalize()}")
    log_embed.add_field(name = "Target", value = f"<@{str(target.id)}>", inline = True)
    log_embed.add_field(name = "Moderator", value = f"<@{str(user.id)}>", inline = True)
    await log_channel.send(embed = log_embed)

@bot.event
async def on_member_ban(member_guild, member):
    found_entry = None

    #tries to find the entry in guild where a member was banned
    async for entry in member_guild.audit_logs(limit = 100, action = discord.AuditLogAction.ban, after = ten_seconds):

        #target id matches the same id
        if entry.target.id == member.id:
            found_entry = entry
            break

    #returns if the entry was not found
    if not found_entry:
        return
    
    #logs entry in log channel
    await log(guild = member_guild, type = "BAN", user = found_entry.user, target = member) 

@bot.event
async def on_member_unban(member_guild, member):
    found_entry = None

    #tries to find the entry in guild where a member was unbanned
    async for entry in member.audit_logs(limit = 100, action = discord.AuditLogAction.unban, after = ten_seconds):

        #target id matches the same id
        if entry.target.id == member.id:
            found_entry = entry
            break

    #returns if the entry was not found
    if not found_entry:
        return
    
    #logs entry in log channel
    await log(guild = member_guild, type = "UNBAN", user = found_entry.user, target = member)

@bot.event
async def on_member_remove(member):
    found_entry = None
    #tries to find the entry in guild where a member was kicked
    async for entry in member.guild.audit_logs(limit = 100, action = discord.AuditLogAction.kick, after = ten_seconds): # 10 to prevent join-kick-join-leave false-positives

        #target id matches the same id
        if entry.target.id == member.id:
            found_entry = entry
            break

    #returns if the entry was not found
    if not found_entry:
        return

    #logs entry in log channel
    await log(guild = member.guild, type = "KICK", user = found_entry.user, target = member)

@bot.event
async def on_member_update(before, after):
    #returns if the roles did not change
    if before.roles == after.roles:
        return

    #search for the role
    added_role = discord.utils.get(after.guild.roles, name = ROLE_NAME)

    #returns if the role was not found
    if not added_role:
        return

    #added role
    if added_role in after.roles and not added_role in before.roles:
        found_entry = None

        #finds the entry in guild where a member's roles were updated
        async for entry in after.guild.audit_logs(limit = 100, action = discord.AuditLogAction.member_role_update, after = ten_seconds):

            #target id matches the same id after 10 seconds and added role
            if entry.target.id == after.id and added_role in entry.after.roles and not added_role in entry.before.roles:

                #saves entry in found_entry
                found_entry = entry
                break

        #returns if the entry was not found
        if not found_entry:
            return

        #logs entry in log channel
        await log(guild = after.guild, type = "ADDROLE", user = found_entry.user, target = after)

    #removed role
    elif added_role not in after.roles and added_role in before.roles:
        found_entry = None

        #tries to find the entry in guild where a member's roles were updated
        async for entry in after.guild.audit_logs(limit = 100, action = discord.AuditLogAction.member_role_update, after = ten_seconds):

            #target id matches the same id after 10 seconds and removed role
            if entry.target.id == after.id and added_role not in entry.after.roles and added_role in entry.before.roles:
                found_entry = entry
                break

        #returns if the entry was not found
        if not found_entry:
            return

        #logs entry in log channel
        await log(guild = after.guild, type = "REMOVEROLE", user = found_entry.user, target = after)

async def get_help_embed():
    em = discord.Embed(title="Hi", description="I cannot be banned or kicked.\n", color=discord.Color.green())
    em.description += f"**{bot.command_prefix}set_log_channel <channel>** : This is where I will report any major actions done by the moderators. \n"
    em.description += f"**{bot.command_prefix}set_role <role>** : I will keep a look out for who adds or removes this role. \n"
    em.description += f"**{bot.command_prefix}get_bans**: I will tell you about every ban that has occurred. \n"
    em.description += f"**{bot.command_prefix}get_unbans** : I will tell you who unbanned who. \n"
    em.description += f"**{bot.command_prefix}get_kicks** : I will share a little something I know about who got kicked. \n"
    em.description += f"**{bot.command_prefix}dm <user> <message>** : I may or may not let everyone know what you said to this person. \n"
    em.description += f"**{bot.command_prefix}dm_all <message>** : What you have to say will be everyone's concern. \n"
    em.description += f"**{bot.command_prefix}see_deleted_messages** : Somebody might have said something they deeply regret. \n"
    em.set_footer(text="You didn't hear any of this from me though.")
    return em

@bot.command()
async def get_help(ctx):
    em = await get_help_embed()
    await ctx.send(embed=em)

@bot.command()
async def set_log_channel(ctx, args=None):
    if args != None:
        MOD_LOG_CHANNEL_NAME = args
    else:
        print(f"{str(ctx.author.mention)}, you did not provide a channel name for me to send logs to!")

@bot.command()
async def set_role(ctx, args=None):
    if args != None:
        ROLE_NAME = args
    else:
        print(f"{str(ctx.author.mention)}, you did not provide a role name for me to keep track of!")
    
@bot.command()
async def get_bans(ctx):
    if ctx.guild.audit_logs(action=discord.AuditLogAction.ban).size() >= 1:
        async for entry in ctx.guild.audit_logs(action=discord.AuditLogAction.ban):
            print(f'{entry.user} banned {entry.target}')
        print("Mod abuse?")
    else:
        print("Zzzzzz... Ban someone already.")

@bot.command()
async def get_unbans(ctx):
    if ctx.guild.audit_logs(action=discord.AuditLogAction.unban).size() >= 1:
        async for entry in ctx.guild.audit_logs(action=discord.AuditLogAction.unban):
            print(f'{entry.user} unbanned {entry.target}')
        print("Character development?")
    else:
        print("Nobody unbanned anyone... Y'all are not that forgiving it seems.")

@bot.command()
async def get_kicks(ctx):
    if ctx.guild.audit_logs(action=discord.AuditLogAction.kick).size() >= 1:
        async for entry in ctx.guild.audit_logs(action=discord.AuditLogAction.kick):
            print(f'{entry.user} kicked {entry.target}')
        print("You did not hear that from me though.")
    else:
        print("Everyone must be getting along, since nobody has been kicked yet.")

@bot.command()
async def dm(ctx, user_id=None, *, args=None):
    if user_id != None and args != None:
        try:
            target = await bot.fetch_user(user_id)
            await target.send(args)
            await ctx.channel.send("'" + args + "' has been sent to: " + target.name)
        except:
            await ctx.channel.send("You're talking to Casper my guy.")
    elif user_id == None and args != None:
        await ctx.channel.send(f"{str(ctx.author.mention)} must be talking to a mirror.") 
    elif user_id != None and args == None:
        await ctx.channel.send(f"Speak up my boy. Go ahead and say it to {str(user_id.id)}.") 
    else:
        await ctx.channel.send(f"Did you even type anything {str(ctx.author.mention)}?") 

@bot.command()
async def dm_all(ctx, *, args=None):
    if args != None:
        members = ctx.guild.members
        for member in members:
            try:
                await member.send(args)
                print("'" + args + "' sent to " + member.name)
            except:
                print("Couldn't send '" + args + "' to " + member.name)
    else:
        await ctx.channel.send(f"I know you want to message everyone in the server, but you didn't say anything {str(ctx.author.mention)}.")

@bot.command()
async def see_deleted_messages(ctx):
    try:
        contents, author, channel_name, time = bot.sniped_messages[ctx.guild.id]
    except:
        await ctx.channel.send("There was no message that was recently deleted.")
        return

    embed = discord.Embed(description=contents, color=discord.Color.purple(), timestamp=time)
    embed.set_author(name=f"{author.name}#{author.discriminator}")
    embed.set_footer(text=f"Deleted in : #{channel_name}")

    await ctx.channel.send(embed=embed)

#runs bot token
bot.run(configs.DISCORD_BOT_TOKEN)