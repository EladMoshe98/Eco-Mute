import logging
import sys

# 1. Create a Custom Logger
logger = logging.getLogger("ecomute_logger")

# Set the lowest threshold so the logger captures everything from DEBUG up
logger.setLevel(logging.DEBUG)

# ---- HANDLER 1: Console (Standard Output) ----
# This handler will print messages to the terminal
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)  # Ignore DEBUG messages in the console

# ---- HANDLER 2: File (Disk Storage) ----
# This handler will write WARNING and above to a persistent file
file_handler = logging.FileHandler("ecomute.log")
file_handler.setLevel(logging.WARNING)

# ---- FORMATTING ----
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

# Apply the format to both handlers
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# ---- ACTIVATE ----
# Add the handlers to the main logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)


def get_logger() -> logging.Logger:
    return logger
