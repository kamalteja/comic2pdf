"""
This script creates pdf files from the downloaded manga chapters from https://mangakatana.com/
"""

#!/usr/bin/env python

import argparse

import os
import re
import tempfile
import zipfile

from PIL import Image

def natural_sort_key(key):
    """Sort key to handle numeric parts in filenames."""
    return [
        int(text) if text.isdigit() else text.lower()
        for text in re.split(r"(\d+)", key)
    ]


def create_pdf_from_images(pdf_file, image_folder):
    """Create a PDF file from images in a folder."""
    images = sorted(
        [os.path.join(image_folder, f) for f in os.listdir(image_folder)],
        key=natural_sort_key,
    )
    img_list = []

    for image_path in images:
        try:
            with Image.open(image_path) as img:
                if img.mode == "P":
                    img = img.convert("RGB")
                img_list.append(img.copy())
        except Exception as e:
            print(f"Error processing image {image_path}: {e}")

    if img_list:
        img_list[0].save(pdf_file, save_all=True, append_images=img_list[1:])


def generate_manga(args):
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
    processed_manga_count = 0
    root_folder = args.manga_dir
    pdf_folder = args.output_dir
    if not os.path.exists(pdf_folder):
        os.makedirs(pdf_folder)

    for zip_file in os.listdir(root_folder):
        if zip_file.endswith(".zip"):
            zip_path = os.path.join(root_folder, zip_file)
            chapter_name = os.path.splitext(zip_file)[0]
            series_name = "-".join(chapter_name.split("_")[:-2])

            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                with tempfile.TemporaryDirectory() as temp_dir:
                    zip_ref.extractall(temp_dir)

                    chapter_count = 0
                    for chapter_folder in sorted(
                        os.listdir(temp_dir), key=natural_sort_key
                    ):
                        manga_folder = os.path.join(temp_dir, chapter_folder)
                        manga_pdf_file = f"{series_name}_{chapter_folder}.pdf"

                        if manga_pdf_file in os.listdir(pdf_folder):
                            print(
                                f"PDF already exists: {manga_pdf_file}, skipping {chapter_folder}"
                            )
                            continue

                        print(f"Processing: {zip_ref.filename} - {chapter_folder}")
                        abs_pdf_file = os.path.join(pdf_folder, manga_pdf_file)
                        create_pdf_from_images(abs_pdf_file, manga_folder)
                        chapter_count += 1
            processed_manga_count += 1
            print(
                f"ZIP processing completed: {chapter_name}.zip, {chapter_count} PDF generated, "
                f"{len(os.listdir(pdf_folder))} total"
            )

    if processed_manga_count == 0:
        print("No manga found in the directory")


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
    args = args.parse_args()
    generate_manga(args)


if __name__ == "__main__":
    main()
