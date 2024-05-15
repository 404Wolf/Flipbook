import os
import logging

logger = logging.getLogger(__name__)

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

    logger.info(f"Running command: {command}")
    return os.system(command)
