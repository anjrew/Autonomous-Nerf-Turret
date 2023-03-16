import logging
from typing import Union

class InvalidLoggingLevel(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


def is_valid_string_log_level(level_str: str) -> bool:
    """
    Check whether an input string matches one of the log levels defined in the logging module.

    Parameters:
        level_str (str): The input string to check.

    Returns:
        bool: True if the input string matches one of the log levels, False otherwise.
    """
    assert type(level_str) == str
    try:
        level = logging.getLevelName(level_str.upper())
        return is_valid_int_log_level(int(level))
    except ValueError:
        return False


def is_valid_int_log_level(level: int) -> bool:
    """
    Check whether an input int matches one of the log levels defined in the logging module.

    Parameters:
        level (int): The input int to check.

    Returns:
        bool: True if the input int matches one of the log levels, False otherwise.
    """
    assert type(level) == int
 
    return level in (logging.CRITICAL, logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG, logging.NOTSET)
   

# Define the conversion function
def map_log_level(level_str: str) -> int:
    """
    Convert a logging level string to its corresponding integer value.

    Parameters:
        level_str (str): The logging level string to convert.

    Returns:
        int: The integer value corresponding to the logging level string.

    Raises:
        argparse.ArgumentTypeError: If the input value is not a valid logging level string.
    """
    
    if type(level_str) == int or level_str.isdigit() and is_valid_int_log_level(int(level_str)):
        return int(level_str)
    
    elif level_str.isalpha() and is_valid_string_log_level(level_str):
        
        level_name = level_str.upper()
        return logging.getLevelName(level_name)
       
    else:
        raise InvalidLoggingLevel(f"Invalid logging level: {level_str}")
    

def setup_logger(name: str, level: Union[int, str]) -> logging.Logger:
    # Create a logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # Set the logging level

    # Create a custom format
    custom_format = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')

    # Create a handler for the logger
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(custom_format)  # Set the custom format for the handler

    # Add the handler to the logger
    logger.addHandler(stream_handler)

    return logger
