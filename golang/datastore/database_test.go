package datastore_test

import (
	"context"
	"os"
	"testing"

	"github.com/jenarvaezg/cunhaobot/datastore"
	"github.com/stretchr/testify/assert"
	"google.golang.org/appengine/v2/aetest"
)

var mainCtx context.Context
var db *datastore.Database

func TestMain(m *testing.M) {
	ctx, done, _ := aetest.NewContext()
	defer done()
	mainCtx = ctx
	db, _ = datastore.New(mainCtx)
	os.Exit(m.Run())
}

func TestDatabase(t *testing.T) {
	t.Run("New", func(t *testing.T) {
		_, err := datastore.New(mainCtx)

		assert.Nil(t, err, "No error expected")
	})
}
