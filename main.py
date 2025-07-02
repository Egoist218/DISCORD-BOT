import discord
from discord.ext import commands, tasks
import json
import os
from keep_alive import keep_alive
import asyncio

# تحديد مسار ملف الإعدادات
CONFIG_FILE = 'config.json'

# تحميل الإعدادات من ملف JSON
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        'registered_channels': [],
        'allowed_role': None,
        'bot_status': True,
        'welcome_settings': {
            'channel_id': None,
            'message': None,
            'dm_message': None,
            'image_url': None,
            'line_image_url': None,
            'embed_color': '#f39c12',
            'enabled': False
        }
    }

# حفظ الإعدادات في ملف JSON
def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4)

config = load_config()

# إعداد البوت
intents = discord.Intents.default()
intents.message_content = True  # تفعيل قراءة محتوى الرسائل
intents.members = True # تفعيل قراءة معلومات الأعضاء

bot = commands.Bot(command_prefix='$', intents=intents)

# دالة للتحقق من صلاحيات الرتبة
async def has_allowed_role(ctx):
    if config["allowed_role"] is None:
        if ctx.author.guild_permissions.administrator:
            return True
        else:
            await ctx.send("❗ لا يمكنك استخدام هذا الأمر، هذه الأوامر مخصصة للمسؤولين فقط.")
            return False
    
    role = ctx.guild.get_role(config["allowed_role"])
    if role and role in ctx.author.roles:
        return True
    
    await ctx.send(f"❗ لا يمكنك استعمال هذا الأمر لأنك لا تملك <@&{config['allowed_role']}>.")
    return False

# دالة للتحقق من حالة البوت
async def is_bot_enabled(ctx):
    if not config['bot_status']:
        await ctx.send('❌ البوت متوقف مؤقتًا.')
        return False
    return True

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    print(f'Bot ID: {bot.user.id}')
    print('------')

# 1. $react <رابط الرسالة>
@bot.command(name='react')
@commands.check(has_allowed_role)
@commands.check(is_bot_enabled)
async def react_command(ctx, message_link: str):
    try:
        guild_id, channel_id, message_id = map(int, message_link.split('/')[-3:])
        
        if channel_id not in config['registered_channels']:
            await ctx.send('⛔ هذه الروم ليست مسجلة في البوت.')
            return

        channel = bot.get_channel(channel_id)
        if not channel:
            await ctx.send('خطأ: لم يتم العثور على القناة.')
            return

        message = await channel.fetch_message(message_id)
        await message.add_reaction('✅')
        await message.add_reaction('❌')
        await ctx.send('📌 تم إضافة ردود الفعل بنجاح!')
    except Exception as e:
        await ctx.send(f'حدث خطأ: تأكد من صحة رابط الرسالة. {e}')

# 2. $setup <#channel>
@bot.command(name='setup')
@commands.check(has_allowed_role)
async def setup_command(ctx, channel: discord.TextChannel):
    if len(config['registered_channels']) >= 5:
        await ctx.send('🚫 لا يمكنك إضافة أكثر من 5 رومات مسجلة.')
        return

    if channel.id in config['registered_channels']:
        await ctx.send('⚠️ هذه الروم موجودة مسبقًا ⛔')
        return

    config['registered_channels'].append(channel.id)
    save_config(config)
    await ctx.send(f'🛠️ تم اختيار هذه الروم للرياكشنات من قبل {ctx.author.mention}.')

# 3. $add-role <@role>
@bot.command(name='add-role')
@commands.check(has_allowed_role)
async def add_role_command(ctx, role: discord.Role):
    if config['allowed_role'] is not None:
        await ctx.send('🚫 لا يمكنك إضافة أكثر من رتبة واحدة.')
        return

    config['allowed_role'] = role.id
    save_config(config)
    await ctx.send(f'🧰 تم تسجيل الرتبة {role.mention} للتحكم في البوت.')

# 4. $enable / $disable
@bot.command(name='enable')
@commands.check(has_allowed_role)
async def enable_command(ctx):
    if config['bot_status']:
        await ctx.send('✅ البوت مفعل بالفعل.')
        return
    config['bot_status'] = True
    save_config(config)
    await ctx.send('✅ تم تفعيل البوت بنجاح.')

@bot.command(name='disable')
@commands.check(has_allowed_role)
async def disable_command(ctx):
    if not config['bot_status']:
        await ctx.send('❌ البوت متوقف بالفعل.')
        return
    config['bot_status'] = False
    save_config(config)
    await ctx.send('❌ تم إيقاف البوت مؤقتًا.')

# 5. $bot-list
@bot.command(name='bot-list')
@commands.check(has_allowed_role)
async def bot_list_command(ctx):
    embed = discord.Embed(title='📋 قائمة الرومات والرولات المسجلة في البوت:', color=discord.Color.blue())
    
    channels_list = []
    for channel_id in config['registered_channels']:
        channel = bot.get_channel(channel_id)
        if channel:
            channels_list.append(f'🟦 - {channel.mention}')
        else:
            channels_list.append(f'🟦 - قناة غير موجودة (ID: {channel_id})')
    embed.add_field(name='الرومات:', value='\n'.join(channels_list) if channels_list else 'لا توجد رومات مسجلة.', inline=False)

    role_mention = 'لا توجد رتبة مسجلة.'
    if config['allowed_role']:
        role = ctx.guild.get_role(config['allowed_role'])
        if role:
            role_mention = f'🟨 - {role.mention}'
        else:
            role_mention = f'🟨 - رتبة غير موجودة (ID: {config["allowed_role"]})'
    embed.add_field(name='الرتبة:', value=role_mention, inline=False)

    await ctx.send(embed=embed)

@bot.command(name='commands')
async def commands_command(ctx, category: str = None):
    embed = discord.Embed(title='🆘 قائمة أوامر البوت:', color=discord.Color.green())

    if category is None:
        embed.description = 'الرجاء تحديد نوع المساعدة:\n\n- `$commands رياكت` لأوامر الرياكشنات\n- `$commands ترحيب` لأوامر الترحيب'
    elif category.lower() == 'رياكت':
        embed.add_field(name='$react <رابط الرسالة>', value='📌 يضيف تفاعلات ✅ و ❌ إلى الرسالة المحددة.', inline=False)
        embed.add_field(name='$setup <#channel>', value='🛠️ يسجل الروم المحددة للرياكشنات.', inline=False)
        embed.add_field(name='$add-role <@role>', value='🧰 يسجل الرتبة المحددة للتحكم في البوت.', inline=False)
        embed.add_field(name='$enable / $disable', value='✅❌ لتفعيل أو إيقاف البوت مؤقتًا.', inline=False)
        embed.add_field(name='$bot-list', value='📋 يعرض قائمة بالرومات والرولات المسجلة.', inline=False)
    elif category.lower() == 'ترحيب':
        embed.add_field(name="$welcome-setup #channel", value="🎯 تحديد الروم التي تُرسل فيها رسائل الترحيب.", inline=False)
        embed.add_field(name="$msg [رسالة]", value="💬 تحديد رسالة الترحيب داخل السيرفر.", inline=False)
        embed.add_field(name="$dm-msg [رسالة]", value="📬 تحديد رسالة خاصة (DM) تُرسل تلقائيًا لكل عضو جديد.", inline=False)
        embed.add_field(name="$pic [رابط صورة]", value="🖼️ صورة تُعرض داخل Embed الترحيب.", inline=False)
        embed.add_field(name="$line [رابط صورة]", value="➖ خط زخرفي يُرسل بصورة منفصلة أسفل الترحيب.", inline=False)
        embed.add_field(name="$color [اللون]", value="🎨 لتغيير لون Embed الترحيب.", inline=False)
        embed.add_field(name="$preview", value="👀 عرض رسالة ترحيب تجريبية.", inline=False)
        embed.add_field(name="$reset [نوع الإعداد]", value="♻️ حذف جميع إعدادات الترحيب أو إعداد محدد.", inline=False)
        embed.add_field(name="$settings", value="📋 يعرض الإعدادات الحالية.", inline=False)
        embed.add_field(name="$toggle on/off", value="🔘 تفعيل أو تعطيل الترحيب مؤقتًا.", inline=False)
    else:
        embed.description = 'نوع المساعدة غير معروف. الرجاء الاختيار من: رياكت، ترحيب.'

    await ctx.send(embed=embed)


# Welcome Commands
@bot.command(name='welcome-setup')
@commands.has_permissions(administrator=True)
async def welcome_setup(ctx, channel: discord.TextChannel):
    if config['welcome_settings']['channel_id'] is not None:
        await ctx.send('⚠️ لا يمكنك إضافة أكثر من روم واحدة!\nاحذف السابقة بـ $reset welcome-setup لإعادة التهيئة.')
        return
    
    config['welcome_settings']['channel_id'] = channel.id
    save_config(config)
    await ctx.send(f'🛠️ تم اختيار هذه الروم للترحيب من قبل {ctx.author.mention}.')

@bot.command(name='msg')
@commands.has_permissions(administrator=True)
async def welcome_message(ctx, *, message: str):
    if config['welcome_settings']['message'] is not None:
        await ctx.send('⚠️ لا يمكنك إنشاء أكثر من رسالة ترحيب واحدة!')
        return
    
    config['welcome_settings']['message'] = message
    save_config(config)
    await ctx.send('📨 تم حفظ رسالة الترحيب بنجاح!')

@bot.command(name='dm-msg')
@commands.has_permissions(administrator=True)
async def welcome_dm_message(ctx, *, message: str):
    config['welcome_settings']['dm_message'] = message
    save_config(config)
    await ctx.send('📥 تم حفظ رسالة الخاص.')

@bot.command(name='pic')
@commands.has_permissions(administrator=True)
async def welcome_pic(ctx, link: str):
    if not (link.startswith('http://') or link.startswith('https://')):
        await ctx.send('الرابط غير صالح أو لا يحتوي على صورة.')
        return
    
    config['welcome_settings']['image_url'] = link
    save_config(config)
    await ctx.send('📌 تم حفظ الصورة بنجاح.')

@bot.command(name='line')
@commands.has_permissions(administrator=True)
async def welcome_line(ctx, link: str):
    if not (link.startswith('http://') or link.startswith('https://')):
        await ctx.send('الرابط غير صالح أو لا يحتوي على صورة.')
        return
    
    config['welcome_settings']['line_image_url'] = link
    save_config(config)
    await ctx.send('🎨 تم حفظ الخط وسيظهر تحت الترحيب.')

@bot.command(name='color')
@commands.has_permissions(administrator=True)
async def welcome_embed_color(ctx, color_name: str):
    colors = {
        'ازرق': 0x3498db, 'احمر': 0xe74c3c, 'اخضر': 0x2ecc71, 'اسود': 0x000000,
        'ابيض': 0xffffff, 'رمادي': 0x95a5a6, 'بني': 0x795548, 'بنفسجي': 0x9b59b6, 'اصفر': 0xf1c40f
    }
    
    color_hex = colors.get(color_name.lower())
    if color_hex is None:
        await ctx.send('🚫 اللون غير معروف! استخدم الألوان المحددة فقط.')
        return
    
    config['welcome_settings']['embed_color'] = f'{color_hex:#08x}'
    save_config(config)
    await ctx.send(f'🎨 تم تغيير اللون إلى "{color_name}"')

@bot.command(name='preview')
@commands.has_permissions(administrator=True)
async def welcome_preview(ctx):
    welcome_channel_id = config['welcome_settings']['channel_id']
    if welcome_channel_id is None:
        await ctx.send('لا توجد روم ترحيب مسجلة. استخدم $setup لتحديدها.')
        return
    
    welcome_channel = bot.get_channel(welcome_channel_id)
    if welcome_channel is None:
        await ctx.send('الروم المسجلة للترحيب غير موجودة أو لا يمكن الوصول إليها.')
        return

    await on_member_join(ctx.author)
    await ctx.send('👀 تم عرض رسالة ترحيب تجريبية في روم الترحيب المسجلة.')

@bot.command(name='reset')
@commands.has_permissions(administrator=True)
async def welcome_reset(ctx, setting_type: str = None):
    if setting_type is None:
        config['welcome_settings'] = {
            'channel_id': None, 'message': None, 'dm_message': None, 'image_url': None,
            'line_image_url': None, 'embed_color': '#f39c12', 'enabled': False
        }
        await ctx.send('🧹 تم حذف جميع إعدادات الترحيب بنجاح.')
    else:
        setting_map = {
            'welcome-setup': 'channel_id', 'msg': 'message', 'dm-msg': 'dm_message',
            'pic': 'image_url', 'line': 'line_image_url', 'color': 'embed_color', 'toggle': 'enabled'
        }
        key_to_reset = setting_map.get(setting_type.lower())
        if key_to_reset:
            default_values = {'embed_color': '#f39c12', 'enabled': False}
            config['welcome_settings'][key_to_reset] = default_values.get(key_to_reset)
            await ctx.send(f'🧹 تم حذف إعداد {setting_type} بنجاح.')
        else:
            await ctx.send('🚫 نوع الإعداد غير معروف.')
            return
    save_config(config)

@bot.command(name='settings')
@commands.has_permissions(administrator=True)
async def welcome_settings(ctx):
    settings = config['welcome_settings']
    embed = discord.Embed(title='📋 إعدادات الترحيب الحالية:', color=discord.Color.blue())
    
    channel_mention = f'<#{settings["channel_id"]}>' if settings['channel_id'] else 'غير محدد'
    embed.add_field(name='الروم:', value=channel_mention, inline=False)
    embed.add_field(name='الرسالة:', value=settings['message'] or 'غير محددة', inline=False)
    embed.add_field(name='رسالة الخاص:', value=settings['dm_message'] or 'غير محددة', inline=False)
    embed.add_field(name='الصورة:', value=settings['image_url'] or 'غير محددة', inline=False)
    embed.add_field(name='الخط الزخرفي:', value=settings['line_image_url'] or 'غير محدد', inline=False)
    embed.add_field(name='لون Embed:', value=settings['embed_color'], inline=False)
    embed.add_field(name='الحالة:', value='مفعل' if settings['enabled'] else 'معطل', inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name='toggle')
@commands.has_permissions(administrator=True)
async def welcome_toggle(ctx, status: str):
    status = status.lower()
    if status == 'on':
        config['welcome_settings']['enabled'] = True
        await ctx.send('✅ تم تفعيل الترحيب بنجاح.')
    elif status == 'off':
        config['welcome_settings']['enabled'] = False
        await ctx.send('❌ تم تعطيل الترحيب مؤقتًا.')
    else:
        await ctx.send('الرجاء تحديد "on" أو "off".')
        return
    save_config(config)

@bot.event
async def on_member_join(member):
    if not config['welcome_settings']['enabled']:
        return

    welcome_channel_id = config['welcome_settings']['channel_id']
    if welcome_channel_id is None: return
    
    welcome_channel = bot.get_channel(welcome_channel_id)
    if welcome_channel is None: return

    dm_message = config['welcome_settings']['dm_message']
    if dm_message:
        try:
            await member.send(dm_message)
        except discord.Forbidden:
            pass

    welcome_message_content = config['welcome_settings']['message']
    if welcome_message_content:
        replacements = {
            '(mention user)': member.mention, '(user)': member.name,
            '(server)': member.guild.name, '(count)': str(member.guild.member_count)
        }
        for placeholder, value in replacements.items():
            welcome_message_content = welcome_message_content.replace(placeholder, value)

        embed_color_str = config['welcome_settings']['embed_color']
        embed_color = int(embed_color_str.lstrip('#'), 16)
        embed = discord.Embed(description=welcome_message_content, color=embed_color)
        
        if config['welcome_settings']['image_url']:
            embed.set_image(url=config['welcome_settings']['image_url'])
        
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.set_footer(text=f'Welcome {member.name}!', icon_url=member.guild.icon.url if member.guild.icon else None)
        
        await welcome_channel.send(embed=embed)

    if config['welcome_settings']['line_image_url']:
        await welcome_channel.send(config['welcome_settings']['line_image_url'])

# الكلاس الخاص بالرسائل التلقائية
class AutoMessage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.target_channel_id = 1383770877136605194 
        self.auto_message_task.start()

    @tasks.loop(minutes=5)
    async def auto_message_task(self):
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(self.target_channel_id)
        if channel:
            try:
                await channel.send("يا ساتر يارب 🔥")
            except Exception as e:
                print(f"An error occurred while sending auto message: {e}")

# تشغيل البوت
async def main():
    async with bot:
        await bot.add_cog(AutoMessage(bot))
        await bot.load_extension('self_ping') # <-- هذا هو السطر الجديد لتحميل ملف self_ping.py
        keep_alive()
        await bot.start(os.getenv("BOT_TOKEN"))

if __name__ == "__main__":
    asyncio.run(main())
