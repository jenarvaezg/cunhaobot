from google.cloud import datastore

datastore_client = datastore.Client()
kinds = ["LongPhrase", "Phrase"]
changes = []
print(kinds)
for kind in kinds:
    print(kind)
    print("*" * 50)
    query = datastore_client.query(kind=kind)
    for entity in query.fetch():
        old_key = entity.key
        key_from_text = datastore_client.key(kind, entity["text"])
        if old_key != key_from_text:
            print(key_from_text, old_key)
            changes.append(entity)
            datastore_client.delete(old_key)
            entity.key = key_from_text
            datastore_client.put(entity)
