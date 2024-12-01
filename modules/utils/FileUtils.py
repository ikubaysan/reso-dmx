import logging

logger = logging.getLogger(__name__)


def read_file_with_encodings(file_path: str, encodings_to_try=None) -> str:
    """
    Attempts to read a file using multiple encodings. Falls back to UTF-8 with error replacement if all fail.

    :param file_path: Path to the file to be read.
    :param encodings_to_try: List of encodings to attempt, in order. Defaults to common encodings.
    :return: The contents of the file as a string.
    :raises: Exception if the file cannot be read even with error replacement.
    """
    if encodings_to_try is None:
        encodings_to_try = ['utf-8', 'windows-1252', 'latin-1']

    for encoding in encodings_to_try:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                contents = f.read()
            # logger.info(f"Successfully read {file_path} using encoding {encoding}.")
            return contents
        except UnicodeDecodeError as e:
            # logger.warning(f"Failed to read {file_path} as {encoding}: {e}")
            pass
        except Exception as e:
            logger.error(f"Error reading {file_path} as {encoding}: {e}")

    # Fallback: use UTF-8 with error replacement
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            contents = f.read()
        logger.warning(f"Read {file_path} using utf-8 with errors replaced.")
        return contents
    except Exception as e:
        logger.error(f"Failed to read {file_path} with error replacement: {e}")
        raise Exception(f"Could not read the file {file_path} with any encoding.") from e
