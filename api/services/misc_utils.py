from api.dependencies.pras_dependencies import websock_connection
from loguru import logger

async def send_custom_toast(
    message: str,
    toast_type: str = "info",
    position: str = "top-right",
    auto_close: int = 3000
):
    """
    Send a custom toast notification to the frontend
    
    Args:
        message: The message to display
        toast_type: "success", "error", "warning", "info"
        position: "top-right", "top-center", "top-left", "bottom-right", etc.
        auto_close: Time in milliseconds before auto-closing (0 = never)
    """
    try:
        send_data = {
            "event": "CUSTOM_TOAST",
            "message": message,
            "type": toast_type,
            "position": position,
            "autoClose": auto_close
        }
        await websock_connection.broadcast(send_data)
        logger.debug(f"Custom toast sent: {message}")
    except Exception as e:
        logger.error(f"Failed to send custom toast: {e}")

# Convenience functions for common toast types
async def send_success_toast(message: str, position: str = "top-right", auto_close: int = 3000):
    """Send a success toast"""
    await send_custom_toast(message, "success", position, auto_close)

async def send_error_toast(message: str, position: str = "top-center", auto_close: int = 5000):
    """Send an error toast"""
    await send_custom_toast(message, "error", position, auto_close)

async def send_warning_toast(message: str, position: str = "top-right", auto_close: int = 4000):
    """Send a warning toast"""
    await send_custom_toast(message, "warning", position, auto_close)

async def send_info_toast(message: str, position: str = "top-right", auto_close: int = 3000):
    """Send an info toast"""
    await send_custom_toast(message, "info", position, auto_close) 