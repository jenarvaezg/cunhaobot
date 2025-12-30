from unittest.mock import MagicMock, patch
from infrastructure.datastore.base import DatastoreRepository


def test_datastore_repository_delete():
    with (
        patch("infrastructure.datastore.base.get_datastore_client") as mock_get_client,
        patch("google.cloud.datastore.Client"),
    ):
        mock_client_instance = MagicMock()  # Create instance mock without spec
        mock_get_client.return_value = mock_client_instance

        repo = DatastoreRepository(kind="TestKind")
        entity_id = "test_id"

        # Call the delete method
        repo.delete(entity_id)

        # Assert that client.delete was called with the correct key
        mock_client_instance.key.assert_called_once_with("TestKind", entity_id)
        mock_client_instance.delete.assert_called_once_with(
            mock_client_instance.key.return_value
        )
