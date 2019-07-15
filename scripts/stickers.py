
for s in bot.get_sticker_set('greeting_{}_by_cunhaobot'.format(1)).stickers:
    bot.delete_sticker_from_set(s.file_id)


bot.get_chat(owner_id)
for phrase in Phrase.refresh_cache():
    phrase.generate_sticker(bot)
    phrase.save()
    print(phrase)
    print(phrase.sticker_file_id)
