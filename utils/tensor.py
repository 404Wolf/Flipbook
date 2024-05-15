import os
import time
from PIL import Image
import numpy as np
import tensorflow as tf
import tensorflow_hub as hub
import logging

SAVED_MODEL_PATH = "https://tfhub.dev/captain-pool/esrgan-tf2/1"
os.environ["TFHUB_DOWNLOAD_PROGRESS"] = "True"

logger = logging.getLogger(__name__)


def preprocess_image(image_path):
    """Loads image from path and preprocesses to make it model ready.

    Args:
      image_path: Path to the image file
    """
    hr_image = tf.image.decode_image(tf.io.read_file(image_path))
    # If PNG, remove the alpha channel. The model only supports
    # images with 3 color channels.
    if hr_image.shape[-1] == 4:
        hr_image = hr_image[..., :-1]
    hr_size = (tf.convert_to_tensor(hr_image.shape[:-1]) // 4) * 4
    hr_image = tf.image.crop_to_bounding_box(hr_image, 0, 0, hr_size[0], hr_size[1])
    hr_image = tf.cast(hr_image, tf.float32)
    return tf.expand_dims(hr_image, 0)


def save_image(image, filename):
    """Saves unscaled Tensor Images.

    Args:
      image: 3D image tensor. [height, width, channels]
      filename: Name of the file to save.
    """
    if not isinstance(image, Image.Image):
        image = tf.clip_by_value(image, 0, 255)
        image = Image.fromarray(tf.cast(image, tf.uint8).numpy())
    image.save("%s.jpg" % filename)
    logger.info("Saved as %s.jpg" % filename)


def save_image(image, filepath):
    """Saves unscaled Tensor Images.

    Args:
      image: 3D image tensor. [height, width, channels]
      filepath: Path of the file to save.
    """
    if not isinstance(image, Image.Image):
        image = tf.clip_by_value(image, 0, 255)
        image = Image.fromarray(tf.cast(image, tf.uint8).numpy())
    image.save(filepath)
    logger.info("Saved as %s" % filepath)


def upscale_image(image_path, output_path):
    """Upscale a single image using ESRGAN.

    Args:
        image_path: Path to the image file.
        output_path: Path to save the upscaled image.

    Returns:
      Image: Upscaled image.
    """
    hr_image = preprocess_image(image_path)
    hub_model = hub.load(SAVED_MODEL_PATH)
    fake_image = hub_model(hr_image)
    fake_image = tf.squeeze(fake_image)
    save_image(fake_image, output_path)
    return fake_image


def upscale_images_in_folder(input_folder, output_folder):
    """Upscale all images in a folder using ESRGAN.

    Args:
        input_folder: Path to the input folder.
        output_folder: Path to the output folder.
    """
    for image_path in os.listdir(input_folder):
        logger.info(f"Upscaling image: {image_path}")
        input_path = os.path.join(input_folder, image_path)
        output_path = os.path.join(output_folder, image_path)
        upscale_image(input_path, output_path)
        logger.info(f"Upscaled image saved to: {output_path}")
