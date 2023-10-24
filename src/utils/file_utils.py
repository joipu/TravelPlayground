import json
import os


def read_json_from_file(filename):
    # Build the full path to the JSON file to avoid depending on the current working directory from which the script is run
    # Get the directory where the current main.py is located
    script_dir = os.path.dirname(__file__)
    absolute_file_path = os.path.join(script_dir, "resources", filename)
    with open(absolute_file_path, "r", encoding="utf-8") as f:
        return json.load(f)
