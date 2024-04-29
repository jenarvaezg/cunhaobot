package datastore

import (
	"context"
	"os"
	"testing"

	"github.com/stretchr/testify/assert"
	"google.golang.org/appengine/v2/aetest"
)

var mainCtx context.Context
var db *Database

func TestMain(m *testing.M) {
	ctx, done, _ := aetest.NewContext()
	defer done()
	mainCtx = ctx
	db, _ = New(mainCtx)
	os.Exit(m.Run())
}

func TestDatabase(t *testing.T) {
	t.Run("New", func(t *testing.T) {
		_, err := New(mainCtx)

		assert.Nil(t, err, "No error expected")
	})
}
