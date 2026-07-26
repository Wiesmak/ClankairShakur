import discord
from discord.ext import commands
import logging as log
from .settings import get_settings


class ClankairShakurBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="__",
            intents=discord.Intents.default(),
        )

    async def setup_hook(self) -> None:
        await self.load_extension("clankair_shakur.cogs.pmf_cog")
        await self.tree.sync()

        log.info("ClankairShakur is ready.")

def main() -> None:
    bot = ClankairShakurBot()
    token = get_settings().discord_token
    bot.run(token)

if __name__ == '__main__':
    main()