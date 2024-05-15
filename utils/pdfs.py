import logging
from PyPDF2 import PdfMerger

logger = logging.getLogger(__name__)

def merge_pdfs(pdf_paths, output_path):
    """
    Merge multiple PDFs into a single PDF.

    Args:
        pdf_paths (List[str]): The paths to the PDF files to merge.
        outputPath (str): The path to the output PDF file.
    """

    merger = PdfMerger()
    for pdf_path in pdf_paths:
        logger.info(f"Adding {pdf_path} to the merger.")
        merger.append(pdf_path)
    merger.write(output_path)
    logger.info(f"Output PDF saved to {output_path}")
    merger.close()
