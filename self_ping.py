# self_ping.py
import discord
from discord.ext import commands, tasks
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SelfPing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.self_ping_task.start()
        logging.info("SelfPing Cog loaded and task started.")

    def cog_unload(self):
        self.self_ping_task.cancel()
        logging.info("SelfPing task stopped.")

    @tasks.loop(minutes=5)
    async def self_ping_task(self):
        await self.bot.wait_until_ready()
        latency = self.bot.latency * 1000
        logging.info(f"Self-ping successful. Latency: {latency:.2f}ms")

async def setup(bot):
    await bot.add_cog(SelfPing(bot))
  
