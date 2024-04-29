package entities

import (
	"fmt"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestUser(t *testing.T) {
	t.Run("test String", func(t *testing.T) {
		u := User{
			Id:      123,
			ChatID:  456,
			GDPR:    true,
			IsGroup: true,
			Name:    "test",
		}
		expected := fmt.Sprintf("User: id=%v chatID=%v GDPR=%v IsGroup=%v Name=%v", u.Id, u.ChatID, u.GDPR, u.IsGroup, u.Name)

		actual := u.String()

		assert.Equal(t, expected, actual, "they should be equal")

	})
}
