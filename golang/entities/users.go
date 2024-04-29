package entities

import (
	"context"
	"fmt"
)

type User struct {
	Id      int
	ChatID  int
	GDPR    bool
	IsGroup bool
	Name    string
}

func (u User) String() string {
	return fmt.Sprintf("User: id=%v chatID=%v GDPR=%v IsGroup=%v Name=%v", u.Id, u.ChatID, u.GDPR, u.IsGroup, u.Name)
}

type UserRepository interface {
	// FetchGophers return all gophers saved in storage
	FetchUsers(ctx context.Context) ([]User, error)
	FetchUserById(ctx context.Context, id int) (*User, error)
}
