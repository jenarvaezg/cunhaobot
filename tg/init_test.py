from unittest.mock import MagicMock, patch
from tg import get_tg_application


class TestTgInit:
    def test_get_tg_application(self):
        with patch("telegram.ext.ApplicationBuilder.build") as mock_build:
            mock_app = MagicMock()
            mock_build.return_value = mock_app

            app = get_tg_application()
            assert app == mock_app
            mock_app.add_handlers.assert_called()
            mock_app.add_error_handler.assert_called()
