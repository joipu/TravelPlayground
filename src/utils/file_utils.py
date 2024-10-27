import json
import os
from utils.constants import *


def proj_root_dir():
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def read_json_from_file_in_resources(filename):
    # Build the full path to the JSON file to avoid depending on the current working directory from which the script is run
    # Get the directory where the current main.py is located
    script_dir = os.path.dirname(__file__)
    absolute_file_path = os.path.join(script_dir, "..", "resources", filename)
    return read_json_from_file(absolute_file_path)


def read_json_from_file(full_path):
    content = read_content_from_file(full_path)
    try:
        json_content = json.loads(content)
        return json_content
    except Exception as e:
        print("Error when parsing json content from file: ", full_path)
        print("Error: ", e)
        exit(1)
        return {}


def write_json_to_file_full_path(full_path, json_object):
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding=UTF_8_ENCODING) as f:
        json.dump(json_object, f, ensure_ascii=False, indent=4)


def write_response_to_debug_log_file(response, dir_name, log_filename):
    # Write response content to debug log file
    debug_log_dir = os.path.join(proj_root_dir(), dir_name)
    if not os.path.exists(debug_log_dir):
        os.makedirs(debug_log_dir)

    with open(os.path.join(debug_log_dir, log_filename), "w", encoding=UTF_8_ENCODING) as f:
        f.write(response)


def write_content_to_file(content, filename):
    with open(filename, "w", encoding=UTF_8_ENCODING) as f:
        f.write(content)


def read_content_from_file(filename):
    with open(filename, "r", encoding=UTF_8_ENCODING) as f:
        return f.read()
