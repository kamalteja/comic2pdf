"""
This script creates pdf files from the downloaded manga chapters from https://mangakatana.com/
"""

#!/usr/bin/env python

import argparse
import os
import re
import sys
import tempfile
import zipfile
from io import BytesIO
from typing import List

from PIL import Image
from comic_logging import get_logger

LOGGER = get_logger(__name__)


def natural_sort_key(key):
    """Sort key to handle numeric parts in filenames."""
    return [
        int(text) if text.isdigit() else text.lower()
        for text in re.split(r"(\d+)", key)
    ]


def compress_image(img: Image.Image, quality: int, pdf_file: str, image_num: int):
    """Compress image"""
    buffer = BytesIO()
    img.save(buffer, format="JPEG")
    LOGGER.tmi(
        "Pdf %s, Image %s's original size: %s", pdf_file, image_num, buffer.tell()
    )

    # Compress the image
    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=quality)
    img = Image.open(buffer)
    LOGGER.tmi(
        "Pdf %s, Image %s's compressed size: %s", pdf_file, image_num, buffer.tell()
    )
    return img


def create_pdf_from_images(pdf_file, image_folder, image_quality=10, compress=False):
    """Create a PDF file from images in a folder."""
    images = sorted(
        [os.path.join(image_folder, f) for f in os.listdir(image_folder)],
        key=natural_sort_key,
    )
    img_list: List[Image.Image] = []

    for image_num, image_path in enumerate(images):
        with Image.open(image_path) as img:
            if img.mode == "P":
                # Convert the image to RGB if it's in palette mode
                img = img.convert("RGB")

            if compress:
                # Compress the image
                img = compress_image(img, image_quality, pdf_file, image_num)

            img_list.append(img.copy())

    if img_list:
        img_list[0].save(
            pdf_file, save_all=True, append_images=img_list[1:], quality=image_quality
        )


def generate_manga(manga_dir, output_dir, force_create, compress, quality):
    """
    Extract images from a zip file.

    Directory structure:
    Example: beautiful_series_c001 _ c010.zip (chapter 1 to 10)
    <series_name>_c00<num> _ c00<num>
    ├── c001
    │   ├── 001.jpg
    │   ├── 002.jpg
    │   ├── 003.jpg
    ├── c002
    │   ├── 001.jpg
    │   ├── 002.jpg
    │   ├── 003.jpg
    ...
    """
    if force_create:
        LOGGER.info("[+] Enabled force create")
    if compress:
        LOGGER.info("[+] Enabled compression")

    processed_manga_count = 0
    root_folder = manga_dir

    for zip_file in os.listdir(root_folder):
        if zip_file.endswith(".zip"):
            zip_path = os.path.join(root_folder, zip_file)
            chapter_name = os.path.splitext(zip_file)[0]
            series_name = "-".join(chapter_name.split("_")[:-2])

            pdf_folder = (
                f"{output_dir}"
                f"{'/' if not output_dir.endswith('/') else ''}"
                f"{series_name}"
            )
            if not os.path.exists(pdf_folder):
                os.makedirs(pdf_folder)
            LOGGER.info("Output folder: %s", pdf_folder)

            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                with tempfile.TemporaryDirectory() as temp_dir:
                    zip_ref.extractall(temp_dir)

                    chapter_count = 0
                    for chapter_folder in sorted(
                        os.listdir(temp_dir), key=natural_sort_key
                    ):
                        manga_folder = os.path.join(temp_dir, chapter_folder)
                        manga_pdf_file = f"{series_name}_{chapter_folder}.pdf"

                        if (
                            manga_pdf_file in os.listdir(pdf_folder)
                            and not force_create
                        ):
                            LOGGER.info(
                                "PDF already exists: %s, skipping %s",
                                manga_pdf_file,
                                chapter_folder,
                            )
                            continue

                        LOGGER.debug(
                            "Processing: %s - %s", zip_ref.filename, chapter_folder
                        )
                        abs_pdf_file = os.path.join(pdf_folder, manga_pdf_file)
                        create_pdf_from_images(
                            abs_pdf_file,
                            manga_folder,
                            image_quality=quality,
                            compress=compress,
                        )
                        chapter_count += 1
            processed_manga_count += 1
            LOGGER.info(
                "ZIP processing completed: %s.zip, %s PDF generated, %s total",
                chapter_name,
                chapter_count,
                len(os.listdir(pdf_folder)),
            )

    if processed_manga_count == 0:
        LOGGER.info("No manga found in the directory")
        return 0

    LOGGER.info("Processing completed: %s manga's processed", processed_manga_count)
    return 0


def main():
    """Entry point of the script."""
    _current_dir = os.path.dirname(os.path.abspath(__file__))
    _manga_dir = os.environ.get("MANGA_DIR", _current_dir)
    _output_dir = os.environ.get("OUTPUT_DIR", f"{_current_dir}/pdfs")

    args = argparse.ArgumentParser()
    args.add_argument(
        "--manga-dir",
        help="Directory containing the downloaded manga chapters",
        default=_manga_dir,
    )
    args.add_argument(
        "--output-dir",
        help="Directory to save the generated PDFs",
        default=_output_dir,
    )
    args.add_argument(
        "-f",
        "--force",
        help="Force overwrite any existing PDFs",
        action="store_true",
    )
    args.add_argument(
        "-z",
        "--compress",
        help="Compress the generated PDFs",
        action="store_true",
    )
    args.add_argument(
        "--quality",
        help="Quality of the compressed pdf images",
        type=int,
        default=10,
    )
    args = args.parse_args()

    return generate_manga(
        args.manga_dir, args.output_dir, args.force, args.compress, args.quality
    )


if __name__ == "__main__":
    sys.exit(main())
