import webbrowser
from app.models.base_action import BaseAction
from app.core.logging.logger import get_logger

logger = get_logger("orbit.actions.url")


class UrlAction(BaseAction):
    """Opens a web URL in the system's default browser."""

    def execute(self) -> bool:
        url = self.params.get("url", "")
        if not url:
            logger.error(f"UrlAction '{self.label}' missing 'url' parameter.")
            return False

        try:
            webbrowser.open(url)
            logger.info(f"Opened URL: {url}")
            return True
        except Exception as e:
            logger.error(f"Failed to open URL '{url}': {e}")
            return False
