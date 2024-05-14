package datastore

import (
	"context"
	"fmt"

	"github.com/jenarvaezg/cunhaobot/entities"

	"cloud.google.com/go/datastore"
)

const userKind = "User"

type DatastoreUser struct {
	Id      *datastore.Key `datastore:"__key__"`
	ChatID  int            `datastore:"chat_id"`
	GDPR    bool           `datastore:"gdpr"`
	IsGroup bool           `datastore:"is_group"`
	Name    string         `datastore:"name"`
}

func (u DatastoreUser) ToEntity() *entities.User {
	return &entities.User{
		Id:      int(u.Id.ID),
		ChatID:  u.ChatID,
		GDPR:    u.GDPR,
		IsGroup: u.IsGroup,
		Name:    u.Name,
	}
}

func (d Database) FetchUsers(ctx context.Context) (users []entities.User, err error) {
	q := datastore.NewQuery(userKind)
	var results []DatastoreUser
	if _, err := d.client.GetAll(ctx, q, &results); err != nil {
		return users, fmt.Errorf("getting users: %w", err)

	}

	for _, u := range results {
		users = append(users, *u.ToEntity())
	}

	return
}

func (d Database) FetchUserById(ctx context.Context, id int) (*entities.User, error) {
	var result DatastoreUser
	if err := d.client.Get(ctx, datastore.IDKey(userKind, int64(id), nil), &result); err != nil {
		return nil, fmt.Errorf("fetching user: %w", err)
	}

	return result.ToEntity(), nil

}
