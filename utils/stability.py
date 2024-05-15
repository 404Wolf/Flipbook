import os
import base64
import aiohttp
import asyncio
import logging
from pathlib import Path
from enum import Enum
import aiofiles
from io import BytesIO

logger = logging.getLogger(__name__)


class StabilityAIEngines(Enum):
    X2 = "esrgan-v1-x2plus"


class BadResponseError(Exception):
    pass


async def upscale_image(
    api_key: str,
    engine_id: StabilityAIEngines,
    image_path: str | Path,
    output_path: str | Path,
    width: int = None,
    height: int = None,
):
    """Upscale an image using the Stability AI API.

    Args:
        api_key (str) The stability AI API key.
        engine_id (StabilityAiEngines): The stability AI upscaling engine ID.
        image_path (str|Path): _description_
        output_path (str|Path): The path to save the upscaled image.

    Raises:
        Exception: _description_
    """
    api_host = "https://api.stability.ai"

    async with aiofiles.open(image_path, "rb") as image_file_to_upscale:
        image_bytes_to_upscale = await image_file_to_upscale.read()
        async with aiohttp.ClientSession() as session:
            # Send the image to the API for upscaling
            path = f"{api_host}/v1/generation/{engine_id.value}/image-to-image/upscale"
            logger.info("POSTing to '%s' with '%s'")

            # Build the request body
            data = aiohttp.FormData()
            data.add_field(
                "image",
                BytesIO(image_bytes_to_upscale),
                filename=image_path,
                content_type="image/png",
            )
            if width and height:
                raise ValueError("Only one of width or height can be specified")
            if width is not None:
                data.add_field("width", str(width))
            if height is not None:
                data.add_field("height", str(height))

            async with session.post(
                path,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Accept": "application/json",
                },
                data=data,
            ) as response:
                logger.info("Upscaling image: %s", image_path)
                if response.status != 200:
                    raise BadResponseError(
                        "Non-200 response: "
                        + str(response.status)
                        + " "
                        + await response.text()
                    )

                # Save the upscaled image to the output path
                response_data = await response.json()

    # Decode the base64 encoded image and save it to the output path
    encoded_image = response_data["artifacts"][0]["base64"]
    async with aiofiles.open(output_path, "wb") as image_file_to_upscale:
        await image_file_to_upscale.write(base64.b64decode(encoded_image))


async def upscale_images_in_folder(
    api_key: str,
    engine_id: StabilityAIEngines,
    input_folder: Path | str,
    output_folder: Path | str,
):
    """Upscale all images in a folder using the Stability AI API.

    Args:
        api_key (string) The stability AI API key.
        engine_id (StabilityAIEngine): The stability AI engine ID.
        input_folder (Path): The folder containing the images to upscale.
        output_folder (Path): The folder to save the upscaled images to.
    Returns:
        List[str]: The list of upscaled image filenames.
    """
    logger.info(f"Upscaling images in folder: {input_folder}")
    tasks = []
    for filename in os.listdir(input_folder):
        if filename.endswith(".png"):
            input_path = os.path.join(input_folder, filename)
            task = upscale_image(api_key, engine_id, input_path, output_folder)
            tasks.append(task)
            logger.info(f"Upscaling image: {input_path}")

    return(await asyncio.gather(*tasks))
