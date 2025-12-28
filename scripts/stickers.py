import os

from telegram import Bot

from models.phrase import Phrase

bot = Bot(token=os.environ["TG_TOKEN"])
owner_id = int(os.environ["OWNER_ID"])


async def main():
    for s in (await bot.get_sticker_set(f"greeting_{1}_by_cunhaobot")).stickers:
        await bot.delete_sticker_from_set(s.file_id)

    await bot.get_chat(owner_id)
    for phrase in Phrase.refresh_cache():
        await phrase.generate_sticker(bot)
        phrase.save()
        print(phrase)
        print(phrase.sticker_file_id)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
