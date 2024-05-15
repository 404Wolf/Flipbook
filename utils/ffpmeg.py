import os
import logging

logger = logging.getLogger(__name__)

def break_into_frames(video_source, frames_per_second, output_directory):
    """
    Break a video into frames.

    Args:
        video_source (str): The path to the video file.
        frames_per_second (int): The number of frames to extract per second.
        output_directory (str): The directory to save the frames.
    """

    command = f"ffmpeg -i {video_source} -vf fps={frames_per_second} {output_directory}/frame_%04d.png"
    logger.info(f"Running command: {command}")
    return os.system(command)


def get_video_duration(video_source):
    """
    Get the duration of a video.


    Notes:
        Uses ffmpeg to get the duration of the video.
    Args:
        video_source (str): The path to the video file.
    """
    command = (
        f"ffmpeg -i {video_source} 2>&1 | grep 'Duration' | cut -d ' ' -f 4 | sed s/,//"
    )
    logger.info(f"Running command: {command}")
    duration = (
        os.popen(command).read().strip()
    )  # in the format hh:mm:ss.ms; need to convert it to seconds
    logger.info(f"Duration: {duration}")
    duration = duration.split(":")
    duration = (
        int(duration[0]) * 3600
        + int(duration[1]) * 60
        + int(duration[2].split(".")[0])
        + int(duration[2].split(".")[1]) / 100
    )
    logger.info(f"Duration in seconds: {duration}")
    return duration

