package datastore

import (
	"log"
	"testing"

	"cloud.google.com/go/datastore"
	"github.com/jenarvaezg/cunhaobot/entities"
	"github.com/stretchr/testify/assert"
)

func initUser(id int64, name string) DatastoreUser {
	key := datastore.IDKey(userKind, int64(id), nil)
	user := DatastoreUser{
		Id:      key,
		Name:    name,
		ChatID:  123,
		GDPR:    false,
		IsGroup: false,
	}

	if _, err := db.client.Put(mainCtx, key, &user); err != nil {
		log.Panic(err)
	}

	return user
}

func dropUsers(keys []*datastore.Key) {
	_ = db.client.DeleteMulti(mainCtx, keys)
}

func TestFetchUsers(t *testing.T) {
	user1 := initUser(1, "User 1")
	user2 := initUser(2, "User 2")
	user3 := initUser(3, "User 3")

	t.Run("returns all users", func(t *testing.T) {
		expected := []entities.User{*user1.toEntity(), *user2.toEntity(), *user3.toEntity()}
		users, err := db.FetchUsers(mainCtx)

		assert.Nil(t, err, "No error getting users")
		assert.Equal(t, expected, users, "Users must match")
	})

	t.Cleanup(func() {
		dropUsers([]*datastore.Key{user1.Id, user2.Id, user3.Id})
	})

}

func TestFetchUserById(t *testing.T) {
	user1 := initUser(1, "User 1")
	user2 := initUser(2, "User 2")

	t.Run("returns all users", func(t *testing.T) {
		expected := user1.toEntity()
		users, err := db.FetchUserById(mainCtx, user1.toEntity().Id)

		assert.Nil(t, err, "No error getting user by id")
		assert.Equal(t, expected, users, "Users must match")
	})
	t.Cleanup(func() {
		dropUsers([]*datastore.Key{user1.Id, user2.Id})
	})

}
