"""
Tool for getting the current date and time.
"""
import datetime

def get_current_date() -> dict:
    """
    Returns the current date and time.

    Returns:
        dict: A dictionary containing the current date and time in ISO format.
    """
    try:
        now = datetime.datetime.now()
        return {
            "status": "success",
            "current_date_time": now.isoformat(),
            "pretty_date_time": now.strftime("%A, %d de %B de %Y, %H:%M:%S")
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error getting current date: {str(e)}"
        }
