import discord
from discord.ext import commands, tasks

class AutoMessage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.target_channel_id = 1383770877136605194  # معرف الروم المستهدف
        self.auto_message_task.start()

    @tasks.loop(minutes=5)
    async def auto_message_task(self):
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(self.target_channel_id)
        if channel:
            try:
                await channel.send("يا ساتر يارب 🔥")
                print(f"Sent auto message to channel {channel.name} ({self.target_channel_id})")
            except discord.Forbidden:
                print(f"Error: Bot does not have permission to send messages in channel {channel.name} ({self.target_channel_id})")
            except Exception as e:
                print(f"An error occurred while sending auto message: {e}")
        else:
            print(f"Error: Target channel with ID {self.target_channel_id} not found.")

    @auto_message_task.before_loop
    async def before_auto_message_task(self):
        print("Waiting for bot to be ready before starting auto message task...")

async def setup(bot):
    await bot.add_cog(AutoMessage(bot))
    
