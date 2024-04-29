package main

import (
	"context"
	"fmt"
	"log"

	"github.com/jenarvaezg/cunhaobot/datastore"
)

func main() {
	db, err := datastore.New(context.Background())
	if err != nil {
		log.Panic(err)
	}

	fmt.Println(db)
}
