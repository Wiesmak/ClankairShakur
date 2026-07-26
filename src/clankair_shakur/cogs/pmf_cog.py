import discord
from discord.ext import commands
from discord import app_commands
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import binom
import logging as log
import io
import asyncio
from ..settings import get_settings


def create_pmf_graph(n: int, p: float, xlim: int = 10) -> io.BytesIO:
    x = np.arange(0, n + 1)

    pmf = binom.pmf(x, n, p)
    cdf = binom.cdf(x, n, p)

    fig, ax1 = plt.subplots(figsize=(10, 6))

    ax1.bar(x, pmf * 100, alpha=0.7, color="C0", label="PMF")
    ax1.set_xlabel("Number of successes (x)")
    ax1.set_ylabel("Probability (%)")
    ax1.set_ylim(0, max(pmf * 100) * 1.2)

    ax2 = ax1.twinx()
    ax2.plot(x, cdf * 100, marker="o", linewidth=2, color="C1", label="CDF")
    ax2.set_ylabel("Cumulative probability (%)")
    ax2.set_ylim(0, 105)

    ax1.set_xlim(0, xlim)

    plt.title(f"Binomial Distribution \nn={n}, p={p}")
    ax1.grid(axis="y", alpha=0.3)

    lines, labels = [], []
    for ax in [ax1, ax2]:
        l, lab = ax.get_legend_handles_labels()
        lines.extend(l)
        labels.extend(lab)

    ax1.legend(lines, labels, loc="upper left")

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')

    buffer.seek(0)

    plt.close(fig)

    return buffer


class BinomialCog(commands.Cog):
    def __init__(self, bot, thread_limit):
        self.bot = bot
        if thread_limit is not None:
            self.graph_semaphore = asyncio.Semaphore(thread_limit)
        else:
            self.graph_semaphore = None

    binomial_group = app_commands.Group(
        name="binomial",
        description="Binomial distribution charts",
    )

    @binomial_group.command(name="pmf", description="Generates a binomial distribution PMF chart")
    @app_commands.describe(
        n="The total number of trials",
        p="The probability of success on each trial",
        xlim="Limit number of successes",
    )
    async def pmf(
        self,
        interaction: discord.Interaction,
        n: app_commands.Range[int, 1, 1000],
        p: app_commands.Range[float, 0.0, 1.0] = 0.0075,
        xlim: app_commands.Range[int, 1, 1000] = 10,
    ) -> None:
        await interaction.response.defer(thinking=True)

        try:
            if self.graph_semaphore is not None:
                async with self.graph_semaphore:
                    buffer = await asyncio.to_thread(create_pmf_graph, n, p, xlim)
            else:
                buffer = await asyncio.to_thread(create_pmf_graph, n, p, xlim)
        except Exception as e:
            log.error(f"Graph generation failed: {e}")
            try:
                await interaction.followup.send(
                    "An error occurred while generating the chart.")
            except discord.NotFound:
                pass
            return

        try:
            chart_file = discord.File(fp=buffer, filename="chart.png")
            await interaction.followup.send(file=chart_file)
        except discord.NotFound:
            log.warning(
                "Could not send chart. The interaction expired may have expired.")
        except Exception as e:
            log.error(f"Failed to send followup message: {e}")

async def setup(bot: commands.Bot) -> None:
    thread_limit = get_settings().thread_limit
    await bot.add_cog(BinomialCog(bot, thread_limit))