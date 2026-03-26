import logging
import os
from datetime import datetime
from typing import Optional

import config as cfg
from PIL import Image, UnidentifiedImageError
from pillow_heif import register_heif_opener
from tqdm import tqdm

_logger: Optional[logging.Logger] = None  # Module-level variable for logging

###############################################################################
###############################################################################
def setup_logger() -> logging.Logger:
    """
    Sets up a logger that saves any log output to a file in the script's
    directory, with a filename based on the current date and time.
    """

    global _logger

    # Only set up the logger once
    if _logger is None:
        # Create a logger and set it to WARNING or higher
        _logger = logging.getLogger(__name__)
        _logger.setLevel(logging.WARNING)

        # Check if a handler already exists (important to do this!!)
        if not _logger.handlers:
            # Construct the log file name using the current date and time
            log_file = f"ScriptLog_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

            # Get the script's directory
            script_dir = os.path.dirname(os.path.abspath(__file__))

            # Create the full log file path
            log_file_path = os.path.join(script_dir, log_file)

            # Create a FileHandler to output thru
            handler = logging.FileHandler(log_file_path)

            # Create a formatter
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)

            # Add the handler to the logger
            _logger.addHandler(handler)

    return _logger


###############################################################################
###############################################################################
def get_logger() -> logging.Logger:
    """
    Returns the scripts logger, initializing it if it hasn't been already.
    """
    global _logger

    if _logger is None:
        _logger = setup_logger()

    return _logger

def resize_image(image: Image.Image, width) -> Image.Image:
    """Downsizes a given image to a smaller width while maintaining the previous aspect ratio.

    Args:
        image (Image.Image): The origin image object before resizing.

    Returns:
        Image.Image: The image object resized to a smaller resolution
    """
    old_width, old_height = image.size
    width_height_proportion =  old_height / old_width

    new_width = cfg.ROBOT_PHOTOS_WIDTH
    new_height = int(new_width * width_height_proportion)
    image = image.resize((new_width, new_height))

    return image

###############################################################################
###############################################################################
def format_photos(srcPath: str, dstPath: str) -> None:
    """Given a list of file names, formats and resizes them, to store in a new path.

    Args:
        srcPath (str): Path to to get unformatted photos from
        dstPath (str): Path to copy the formatted versions of photos to
    """
    logger: logging.Logger = get_logger()

    # This allows pillow to process photos in the HEIC file format
    # Most photos from iPhone come in a HEIC format by default, so this is
    register_heif_opener()

    # Get all files in the source directory
    sourceFiles = [os.path.join(srcPath, f) for f in os.listdir(srcPath) if os.path.isfile(os.path.join(srcPath, f))]
    count = len(sourceFiles)

    if count == 0:
        msg = f"No files found to format in the directory {srcPath}"
        logger.info(msg)
        print(msg)
        return

    logger.info(f"Formatting {count} images.")

    with tqdm(total=count, desc="Formatting robot photos") as pbar:
        for file in sourceFiles:
            # Resize the image according to the config width then save it as a .jpg to the destination folder
            try:
                img = Image.open(file)

                # Resizes the img according to the width in ROBOT_PHOTOS_WIDTH while maintaining the aspect ratio
                new_img = resize_image(img, cfg.ROBOT_PHOTOS_WIDTH)
                # Converts the img to RGB
                # This is necessary if the imported img is formatted as a PNG, because we are losing transparency in saving as JPG
                new_img = new_img.convert("RGB")

                # The destination file name
                new_file_name = os.path.splitext(os.path.basename(file))[0] + ".jpg"

                # Save the image to the destination path as a JPG
                new_img.save(os.path.join(dstPath, new_file_name), format="JPEG")

                pbar.update(1)

            except UnidentifiedImageError as e:
                logger.warning(f"Skipping file {file} - not a valid image. {e}")
            except Exception as e:
                msg = f"An unexpected error occurred: {e}"
                logger.error(msg)
                print(msg)

    status_msg: str = f"Successfully copied {count} files to '{dstPath}'"
    logger.info(status_msg)
    print(status_msg)


###############################################################################
###############################################################################
#                  Main starting point for the script
###############################################################################
###############################################################################
def main() -> None:
    logger: logging.Logger = get_logger()

    # The path for the folder to get the unformatted photos from
    srcPath = cfg.ROBOT_PHOTOS_UNFORMATTED_FOLDER#os.path.join(os.getcwd(), cfg.ROBOT_PHOTOS_UNFORMATTED_FOLDER)
    if not srcPath or not os.path.exists(srcPath):
        msg = "Could not find the source folder in the config."
        logger.error(msg)
        print(msg)
        return

    # The destination path we are saving formatted images to
    dstPath = os.path.join(os.getcwd(), cfg.ROBOT_PHOTOS_FOLDER)
    if not dstPath:
        msg = "Destination path undefined"
        logger.error(msg)
        print(msg)
        return

    # Create the folder for the dstPath if it doesn't exist
    if not os.path.exists(dstPath):
        os.makedirs(dstPath)

    logger.info(f"Saving formatted versions of photos in {srcPath} to {dstPath}")

    format_photos(srcPath, dstPath)

###############################################################################
###############################################################################
if __name__ == "__main__":
    main()
