package datastore

import (
	"context"
	"fmt"

	"cloud.google.com/go/datastore"
)

type Database struct {
	client *datastore.Client
}

const defaultAppID = datastore.DetectProjectID

func New(ctx context.Context) (*Database, error) {

	client, err := datastore.NewClient(ctx, defaultAppID)
	if err != nil {
		return nil, fmt.Errorf("getting datastore client: %w", err)
	}

	return &Database{client: client}, nil
}
