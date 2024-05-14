package datastore_test

import (
	"testing"

	"github.com/jenarvaezg/cunhaobot/datastore"
	"github.com/jenarvaezg/cunhaobot/entities"
	"github.com/stretchr/testify/assert"
)

func TestFetchUsers(t *testing.T) {
	user1 := datastore.InitUser(db, mainCtx, 1, "User 1")
	user2 := datastore.InitUser(db, mainCtx, 2, "User 2")
	user3 := datastore.InitUser(db, mainCtx, 3, "User 3")

	t.Run("returns all users", func(t *testing.T) {
		expected := []entities.User{*user1.ToEntity(), *user2.ToEntity(), *user3.ToEntity()}
		users, err := db.FetchUsers(mainCtx)

		assert.Nil(t, err, "No error getting users")
		assert.Equal(t, expected, users, "Users must match")
	})

	t.Cleanup(func() {
		datastore.DropUsers(db, mainCtx, []*datastore.Key{user1.Id, user2.Id})
	})

}

func TestFetchUserById(t *testing.T) {
	user1 := datastore.InitUser(db, mainCtx, 1, "User 1")
	user2 := datastore.InitUser(db, mainCtx, 2, "User 2")

	t.Run("returns all users", func(t *testing.T) {
		expected := user1.ToEntity()
		users, err := db.FetchUserById(mainCtx, user1.ToEntity().Id)

		assert.Nil(t, err, "No error getting user by id")
		assert.Equal(t, expected, users, "Users must match")
	})
	t.Cleanup(func() {
		datastore.DropUsers(db, mainCtx, []*datastore.Key{user1.Id, user2.Id})
	})

}
