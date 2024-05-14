package datastore

import (
	"context"
	"log"

	"cloud.google.com/go/datastore"
)

func InitUser(db *Database, context context.Context, id int64, name string) DatastoreUser {
	key := datastore.IDKey(userKind, int64(id), nil)
	user := DatastoreUser{
		Id:      key,
		Name:    name,
		ChatID:  123,
		GDPR:    false,
		IsGroup: false,
	}

	if _, err := db.client.Put(context, key, &user); err != nil {
		log.Panic(err)
	}

	return user
}

func DropUsers(db *Database, context context.Context, keys []*datastore.Key) {
	_ = db.client.DeleteMulti(context, keys)
}
