from google.cloud import datastore


datastore_client = datastore.Client()
kind = "LongPhrase"
query = datastore_client.query(kind=kind)
changes = []
for entity in query.fetch():
    old_key = entity.key
    key_from_text = datastore_client.key(kind, entity['text'])
    if old_key != key_from_text:
        print(key_from_text, old_key)
        changes.append(entity)
        datastore_client.delete(old_key)
        entity.key = key_from_text
        datastore_client.put(entity)
