from PyPDF2 import PdfMerger
from pathlib import Path
import os
import logging
import argparse

parser = argparse.ArgumentParser(description="Render a video as a multipage PDF.")
parser.add_argument("video", help="The path to the video file.", type=str)
parser.add_argument("height", help="The height of the image in the PDF in inches.", type=float)
parser.add_argument("width", help="The width of the image in the PDF in inches.", type=float)
parser.add_argument("--margin", help="The margin of the image in the PDF in inches.", type=float, default=0)
parser.add_argument("--page-template", help="The path to the template file for image pages.", default="templates/page/page.typ", type=str)
parser.add_argument("--blank-template", help="The path to the template file for blank alternate pages.", default="templates/page/blank.typ", type=str)
parser.add_argument("--output", help="The path to the output pdf file.", default="output.pdf", type=str)
parser.add_argument("--fps", help="The number of frames to extract per second.", default=20, type=int)
parser.add_argument("--temporary_directory", help="The directory to save the temporary files.", default="tmp", type=str)
args = parser.parse_args()

logging.basicConfig(level=logging.INFO)

def render_page(template_path, output_path="out.pdf", root=None, **inputs):
    """
    Render a typst page using the given template and arguments.

    Args:
        templatePath (str): The path to the template file.
        root (str): The root directory to use for rendering.
        **inputs: The arguments to pass to the template.
    """

    command = f"typst compile {template_path}"
    if root:
        command += f" --root {root}"
    for key, value in inputs.items():
        command += f" --input {key}='{value}'"
    command += f" {output_path}"

    logging.info(f"Running command: {command}")
    return os.system(command)

def break_into_frames(video_source, frames_per_second, output_directory):
    """
    Break a video into frames.

    Args:
        video_source (str): The path to the video file.
        frames_per_second (int): The number of frames to extract per second.
        output_directory (str): The directory to save the frames.
    """

    command = f"ffmpeg -i {video_source} -vf fps={frames_per_second} {output_directory}/frame_%04d.png"
    logging.info(f"Running command: {command}")
    return os.system(command)

def get_video_duration(video_source):
    """
    Get the duration of a video.


    Notes:
        Uses ffmpeg to get the duration of the video.
    Args:
        video_source (str): The path to the video file.
    """
    command = f"ffmpeg -i {video_source} 2>&1 | grep 'Duration' | cut -d ' ' -f 4 | sed s/,//"
    logging.info(f"Running command: {command}")
    duration = os.popen(command).read().strip() # in the format hh:mm:ss.ms; need to convert it to seconds
    logging.info(f"Duration: {duration}")
    duration = duration.split(":")
    duration = (
          int(duration[0]) * 3600 
        + int(duration[1]) * 60
        + int(duration[2].split(".")[0])
        + int(duration[2].split(".")[1]) / 100)
    logging.info(f"Duration in seconds: {duration}")
    return duration

def merge_pdfs(pdf_paths, output_path):
    """
    Merge multiple PDFs into a single PDF.

    Args:
        pdf_paths (List[str]): The paths to the PDF files to merge.
        outputPath (str): The path to the output PDF file.
    """

    merger = PdfMerger()
    for pdf_path in pdf_paths:
        logging.info(f"Adding {pdf_path} to the merger.")
        merger.append(pdf_path)
    merger.write(output_path)
    logging.info(f"Output PDF saved to {output_path}")
    merger.close()

def format_seconds_to_timestamp(seconds):
    """
    Format seconds to a timestamp.

    Args:
        seconds (int): The number of seconds.
    Returns:
        str: The formatted timestamp in the format hh:mm:ss:ms.
    """

    hours_place = int(seconds // (60 * 60))
    seconds %= 60 * 60
    minutes_place = int(seconds // 60)
    seconds %= 60
    milliseconds = int((seconds % 1) * 100)
    seconds = int(seconds)
    return f"{hours_place:02d}:{minutes_place:02d}:{seconds:02d}:{milliseconds:02d}"

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

def main():
    temporary_directory = Path(args.temporary_directory)
    try: 
        create_temporary_directory()

        logging.info(f"Extracting frames from {args.video}")
        if break_into_frames(args.video, args.fps, temporary_directory / "images") != 0:
            logging.error("Failed to extract frames.")
            return

        # Sort the frames by their number. The frames are named frame_0001.png, frame_0002.png, etc.
        frame_images = os.listdir(temporary_directory / "images")
        frame_images.sort(key=lambda x: int(x.split("_")[1].split(".")[0]))
        
        duration_per_frame = get_video_duration(args.video) / len(frame_images)

        # Render each frame as a page in the PDF.
        current_timestamp = 0
        page_number = 0
        dimensions = {
            "width": f"{args.width}in",
            "height": f"{args.height}in",
            "margin": f"{args.margin}in",
        }
        for frame in frame_images:
            # Render the frame as a page.
            logging.info(f"Rendering frame {page_number} of {len(frame_images)}")
            render_page(
                args.page_template,
                root=os.getcwd(),
                output_path=f"tmp/pdfs/page_{page_number}.pdf",
                imageSrc=f"//tmp/images/{frame}",
                timestamp=format_seconds_to_timestamp(current_timestamp),
                **dimensions,
            )
            page_number += 1

            # For every page add a blank page
            logging.info(f"Rendering frame {page_number} of {len(frame_images)} (blank page)")
            render_page(
                args.blank_template,
                root=os.getcwd(),
                output_path=f"tmp/pdfs/page_{page_number}.pdf",
                imageSrc=f"//tmp/images/{frame}",
                timestamp=format_seconds_to_timestamp(current_timestamp),
                **dimensions,
            )
        # Update the timestamp for the next frame.
        current_timestamp += duration_per_frame

    # Merge the PDFs into a single PDF.
        pdfs = [f"tmp/pdfs/{pdf}" for pdf in os.listdir("tmp/pdfs")]
        pdfs.sort(key=lambda x: int(x.split("_")[1].split(".")[0]))
        merge_pdfs(pdfs, args.output)
        logging.info("Finished.")
    finally:
        cleanup_temporary_directory(temporary_directory)

if __name__ == "__main__":
    main()
