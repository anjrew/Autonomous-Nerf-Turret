import logging
import argparse

# Define the conversion function
def map_log_level(level_str) -> int:
    if type(level_str) == int or level_str.isdigit():
        return int(level_str)
    elif level_str.isalpha():
        level_name = level_str.upper()
        try:
            level = logging.getLevelName(level_name)
            return level
        except ValueError:
            raise argparse.ArgumentTypeError(f"Invalid logging level: {level_str}")
    else:
        raise argparse.ArgumentTypeError(f"Invalid logging level: {level_str}")
    

def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')
