import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def format_seconds_to_timestamp(seconds):
    """
    Format seconds to a timestamp in format mm:ss:ms.

    Args:
        seconds (int): The number of seconds.
    Returns:
        str: The formatted timestamp in the format mm:ss:ms.
    """

    minutes_place = int(seconds / 60)
    seconds_place = int(seconds)
    milliseconds_place = int((seconds - seconds_place) * 100)
    return f"{minutes_place}:{seconds_place}:{milliseconds_place:02d}"


def create_temporary_directory():
    """
    Create a temporary directory to store the images and PDFs.
    """

    temporary_directory = Path("tmp")
    temporary_directory.mkdir()
    (temporary_directory / "images").mkdir()
    (temporary_directory / "pdfs").mkdir()
    return temporary_directory


def cleanup_temporary_directory(temporary_directory):
    """
    Cleanup the temporary directory.

    Args:
        temporary_directory (Path): The path to the temporary directory.
    """

    for temporary_subdirectory in temporary_directory.iterdir():
        for file in temporary_subdirectory.iterdir():
            file.unlink()
        temporary_subdirectory.rmdir()
    temporary_directory.rmdir()
