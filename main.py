from pathlib import Path
import os
import logging
import argparse
from dotenv import load_dotenv
from utils.misc import (
    format_seconds_to_timestamp,
    create_temporary_directory,
    cleanup_temporary_directory,
)
from utils.ffpmeg import break_into_frames, get_video_duration
from utils.pdfs import merge_pdfs
from utils.typst import render_page
from utils.tensor import upscale_images_in_folder

logging.basicConfig(level=logging.INFO)

load_dotenv()

parser = argparse.ArgumentParser(description="Render a video as a multipage PDF.")
parser.add_argument("video", help="The path to the video file.", type=str)
parser.add_argument(
    "height", help="The height of the image in the PDF in inches.", type=float
)
parser.add_argument(
    "width", help="The width of the image in the PDF in inches.", type=float
)
parser.add_argument(
    "--no-upscale",
    help="Whether to upscale the images using the Stability AI API.",
    action="store_true",
)
parser.add_argument(
    "--margin",
    help="The margin of the image in the PDF in inches.",
    type=float,
    default=0,
)
parser.add_argument(
    "--page-template",
    help="The path to the template file for image pages.",
    default="templates/page/page.typ",
    type=str,
)
parser.add_argument(
    "--blank-template",
    help="The path to the template file for blank alternate pages.",
    default="templates/page/blank.typ",
    type=str,
)
parser.add_argument(
    "--output", help="The path to the output pdf file.", default="output.pdf", type=str
)
parser.add_argument(
    "--fps", help="The number of frames to extract per second.", default=20, type=int
)
parser.add_argument(
    "--keep-temporary-files", help="Keep the temporary files.", action="store_true"
)
parser.add_argument(
    "--temporary_directory",
    help="The directory to save the temporary files.",
    default="tmp",
    type=str,
)

args = parser.parse_args()
args.upscale = not args.no_upscale
logging.debug(args)

def main():
    temporary_directory = Path(args.temporary_directory)
    try:
        create_temporary_directory()

        logging.info(f"Extracting frames from {args.video}")
        logging.info(f"Extracting frames at {args.fps} frames per second.")
        if break_into_frames(args.video, args.fps, temporary_directory / "images") != 0:
            logging.error("Failed to extract frames.")
            return

        # Sort the frames by their number. The frames are named frame_0001.png, frame_0002.png, etc.
        frame_images = os.listdir(temporary_directory / "images")
        frame_images.sort(key=lambda x: int(x.split("_")[1].split(".")[0]))

        # Upscale the images in the folder
        image_folder_name = "images"
        if args.upscale:
            upscale_images_in_folder(temporary_directory / "images", temporary_directory / "upscaled_images")
            image_folder_name = "upscaled_images"

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
            # For every page add a blank page
            logging.info(
                f"Rendering frame {page_number} of {len(frame_images)*2} (blank page)"
            )
            render_page(
                args.blank_template,
                root=os.getcwd(),
                output_path=f"tmp/pdfs/page_{page_number}.pdf",
                timestamp=format_seconds_to_timestamp(current_timestamp),
                **dimensions,
            )
            page_number += 1

            # Render the frame as a page.
            logging.info(f"Rendering frame {page_number} of {len(frame_images)*2}")
            render_page(
                args.page_template,
                root=os.getcwd(),
                output_path=f"tmp/pdfs/page_{page_number}.pdf",
                imageSrc=f"//tmp/{image_folder_name}/{frame}",
                timestamp=format_seconds_to_timestamp(current_timestamp),
                **dimensions,
            )
            page_number += 1

            # Update the timestamp for the next frame.
            current_timestamp += duration_per_frame

        # Merge the PDFs into a single PDF.
        pdfs = [f"tmp/pdfs/{pdf}" for pdf in os.listdir("tmp/pdfs")]
        pdfs.sort(key=lambda x: int(x.split("_")[1].split(".")[0]))
        merge_pdfs(pdfs, args.output)
        logging.info("Finished.")
    finally:
        if not args.keep_temporary_files:
            cleanup_temporary_directory(temporary_directory)


if __name__ == "__main__":
    main()
