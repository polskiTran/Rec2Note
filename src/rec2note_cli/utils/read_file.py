def read_file(file_path):
    """
    Read file content from the given file path and return it as a string.

    Args:
        file_path (str): The path to the file to be read.

    Returns:
        str: The content of the file.
    """
    with open(file_path, "r") as file:
        return file.read()
