package main

import (
	"context"
	"fmt"
	"log"
	"time"

	"github.com/jenarvaezg/cunhaobot/datastore"
	"github.com/jenarvaezg/cunhaobot/entities"
)

func getUsers(db *datastore.Database, ctx context.Context) []entities.User {
	queryCtx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()
	users, err := db.FetchUsers(queryCtx)
	if err != nil {
		log.Panic(err)
	}

	return users
}

func main() {
	db, err := datastore.New(context.Background())
	if err != nil {
		log.Panic(err)
	}

	fmt.Println("Have DB")
	ctx := context.Background()

	fmt.Println(getUsers(db, ctx))

}
