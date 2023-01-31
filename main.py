import os
import sys
import json
import random
import base64
import logging
import datetime
import requests
import concurrent.futures
from rich import print
from rich.logging import RichHandler

FORMAT = "%(message)s"
logging.basicConfig(
    level="NOTSET", format=FORMAT, datefmt="[%X]", handlers=[RichHandler(markup=True)]
)
log = logging.getLogger("rich")
DEBUG_PRINTS = "-d" in sys.argv

OUTPUT_DIR = "out"
COPIES = 30
MAX_THREADS = 30
IPFS_GATEWAY = "https://ipfs.infura.io:5001/api/v0/add?pin=false"
UPLOAD_IMAGES_TO_IPFS = False
UPLOAD_JSON_TO_IPFS = False

copies_supplied_by_argv = False
gateway_supplied_by_argv = False

# When we open a JSON file, we store it in this dictionary so we don't have to open it again.
json_cache = {}
futures = []

generated_json_paths = []
generated_ipfs_links = []

apiKey = ""
apiSecret = ""

print("""
[bold red]
   __  __    ___    __           _                      __  __  
   \ \/ _\  /___\/\ \ \   /\  /\/_\    /\/\    /\/\    /__\/__\ 
    \ \ \  //  //  \/ /  / /_/ //_\\\\  /    \  /    \  /_\ / \// 
 /\_/ /\ \/ \_// /\  /  / __  /  _  \/ /\/\ \/ /\/\ \//__/ _  \ 
 \___/\__/\___/\_\ \/   \/ /_/\_/ \_/\/    \/\/    \/\__/\/ \_/ 
[/bold red]

JSON Hammer v1.0.0                                                 
""")

# ---------------------

def upload_to_ipfs(file_path, putPath = False):
    with open(file_path, "rb") as f:
        creds = base64.b64encode(bytes(apiKey, "utf-8") + b":" + bytes(apiSecret, "utf-8")).decode("utf-8")
        headers = {
            "Authorization": f"Basic {creds}",
        }
        r = requests.post("https://ipfs.infura.io:5001/api/v0/add?pin=false", headers=headers, files={"file": f.read()})
        if r.status_code == 200:
            hash = r.json()["Hash"]
            if putPath: generated_ipfs_links.append(f"ipfs://{hash}")
            return f"ipfs://{hash}"
        else:
            log.fatal(f"Got failing response {r.status_code} while uploading {file_path}. Exiting.")
            log.info("Hint: Make sure your Infura API key and secret are correct.")
            exit()

def create_dir_if_not_exists(dir = OUTPUT_DIR):
    if not type(dir) == str:
        log.fatal("Invalid output directory specified. Exiting.")
        exit()
    if not os.path.exists(dir):
        log.warning(f"Output directory {dir} does not exist, creating...")
        os.makedirs(dir)

def create_json_file(json_data, file_name):
    if not type(json_data) == dict:
        log.fatal("Invalid JSON data supplied. Exiting.")
        exit()
    if not type(file_name) == str:
        log.fatal("Invalid file name supplied. Exiting.")
        exit()
    with open(f"{OUTPUT_DIR}/{file_name}", 'w') as file:
        json.dump(json_data, file)
        if DEBUG_PRINTS: log.debug(f"Created JSON file {file_name}")

def process_line(line):
    if DEBUG_PRINTS: log.debug(f"Processing line: {line}")
    if (type(line)) == str:
        try:
            index = line.index(':')
        except ValueError:
            return line
        possible_cmd = line[0:index]
        if possible_cmd in TEMPLATE_COMMANDS:
            return TEMPLATE_COMMANDS[possible_cmd](line[index+1:])
    if (type(line)) == list:
        return [process_line(item) for item in line]
    if (type(line)) == dict:
        return iterate_json_object(line)
    return line

# Iterates over a JSON object and calls process_line on each value.
def iterate_json_object(object):
    if DEBUG_PRINTS: log.debug(f"Iterating over JSON object: {object}")
    processed = object
    keys = list(object.keys())
    for key in keys:
        processed[key] = process_line(object[key])
    return processed

# ---------------------
# Template commands:

# IMG_FROM_ASSETS:assets/asset_directory
# Picks a random image from assets/assets_directory and returns the path to it.
def image_from_assets(asset):
    if DEBUG_PRINTS: log.debug(f"IMG_FROM_ASSETS:{asset}")
    if not type(asset) == str:
        log.fatal("Invalid asset supplied. Exiting.")
        exit()
    if not os.path.isdir(f"assets/{asset}"):
        log.fatal(f"assets/{asset} is not a directory. Exiting.")
        log.info(f"Hint: Make sure assets/{asset} is a folder containing one or more images.")
        exit()
    images = os.listdir(f"assets/{asset}")
    if len(images) == 0:
        log.fatal(f"assets/{asset} is empty. Exiting.")
        log.info(f"Hint: Make sure assets/{asset} is a folder containing one or more images.")
        exit()

    # pick random image
    image = random.choice(images)
    if not UPLOAD_IMAGES_TO_IPFS:
        return f"assets/{asset}/{image}"
    
    # upload to IPFS
    log.info(f"Uploading {image} to IPFS...")
    return upload_to_ipfs(f"assets/{asset}/{image}")

# RANDOM_FROM_ASSETS_JSON:assets/asset_directory.json
# Picks a random item from assets/assets_directory.json and returns it.
def pick_from_json_array(json_array_path):
    if not json_array_path.endswith(".json"):
        json_array_path += ".json"

    if DEBUG_PRINTS: log.debug(f"RANDOM_FROM_ASSETS_JSON:{json_array_path}")
    if not os.path.exists(f"assets/{json_array_path}"):
        log.fatal("Failure at RANDOM_FROM_ASSETS_JSON")
        log.fatal(f"assets/{json_array_path} does not exist. Exiting.")
        exit()
    if json_array_path in json_cache:
        if (DEBUG_PRINTS): log.debug(f"Using cached JSON array {json_array_path}.")
        return random.choice(json_cache[json_array_path])
    
    if (DEBUG_PRINTS): log.debug(f"Loading JSON array {json_array_path} from file.")
    with open(f"assets/{json_array_path}") as f:
        json_array = json.load(f)
    if not type(json_array) == list:
        log.fatal("Failure at RANDOM_FROM_ASSETS_JSON")
        log.fatal(f"assets/{json_array_path} is not a JSON array. Exiting.")
        exit()
    if len(json_array) == 0:
        log.fatal("Failure at RANDOM_FROM_ASSETS_JSON")
        log.fatal(f"assets/{json_array_path} is empty. Exiting.")
        exit()
    json_cache[json_array_path] = json_array
    return random.choice(json_array)

TEMPLATE_COMMANDS = {
    "IMG_FROM_ASSETS": lambda dir: image_from_assets(dir),
    "RANDOM_FROM_ASSETS_JSON": lambda path: pick_from_json_array(path)
}

# ---------------------
# Main:

if not os.path.exists('./settings.json'):
    log.fatal("No settings.json file found. Exiting.")
    exit()

with open('./settings.json') as f:
    settings = json.load(f)

if "-m" in sys.argv:
    threads = sys.argv[sys.argv.index("-m") + 1]
    if not threads.isnumeric():
        log.fatal("Invalid number of threads specified. Exiting.")
        exit()
    MAX_THREADS = int(threads)
if "-o" in sys.argv:
    dir = sys.argv[sys.argv.index("-o") + 1]
    create_dir_if_not_exists(dir)
    OUTPUT_DIR = dir
if "-c" in sys.argv:
    copies = sys.argv[sys.argv.index("-c") + 1]
    if not copies.isnumeric():
        log.fatal("Invalid number of copies specified. Exiting.")
        exit()
    copies_supplied_by_argv = True
    log.info(f"Making {copies} copies")
    COPIES = int(copies)
if "-g" in sys.argv:
    gateway = sys.argv[sys.argv.index("-g") + 1]
    if not type(gateway) == str:
        log.fatal("Invalid gateway specified. Exiting.")
        exit()
    gateway_supplied_by_argv = True
    log.info(f"Using IPFS gateway {gateway}")
    IPFS_GATEWAY = gateway
if "-t" in sys.argv:
    threads = sys.argv[sys.argv.index("-t") + 1]
    if not threads.isnumeric():
        log.fatal("Invalid number of threads specified. Exiting.")
        exit()
    MAX_THREADS = int(threads)

if not copies_supplied_by_argv:
    if "copies" in settings:
        COPIES = settings["copies"]
        log.info(f"Making {COPIES} copies")
    else:
        log.info(f"Couldn't find a setting for copies. Using the default of {COPIES} copies.")

if not gateway_supplied_by_argv:
    if "ipfsgateway" in settings:
        IPFS_GATEWAY = settings["ipfsgateway"]
        log.info(f"Using IPFS gateway {IPFS_GATEWAY}.")
    else:
        log.info(f"Couldn't find a setting for IPFS Gateway. Using default IPFS gateway {IPFS_GATEWAY}.")

if "uploadImage" in settings:
    UPLOAD_IMAGES_TO_IPFS = settings["uploadImage"]

if "uploadJson" in settings:
    UPLOAD_JSON_TO_IPFS = settings["uploadJson"]

if "maxThreads" in settings and not "-t" in sys.argv:
    MAX_THREADS = settings["maxThreads"]

if "outputDir" in settings and not "-o" in sys.argv:
    create_dir_if_not_exists(settings["outputDir"])
    OUTPUT_DIR = settings["outputDir"]

if not "template" in settings:
    log.fatal("No template specified. Exiting.")
    log.info("Hint: Make sure there is a field named template in settings.json that contains your template info.")
    exit()

if not type(settings["template"]) == dict:
    log.fatal("Invalid template specified. Exiting.")
    log.info("Hint: Make sure there your template is a JSON object.")
    exit()

if not IPFS_GATEWAY.endswith("/"):
    IPFS_GATEWAY += "/"

if UPLOAD_IMAGES_TO_IPFS or UPLOAD_JSON_TO_IPFS:
    if not "apiKey" in settings:
        log.fatal("No API key specified. Exiting.")
        log.info("Hint: Make sure there is a field named apiKey in settings.json that contains your IPFS API key.")
        exit()
    if not "apiSecret" in settings:
        log.fatal("No API secret specified. Exiting.")
        log.info("Hint: Make sure there is a field named apiSecret in settings.json that contains your IPFS API secret.")
        exit()
    apiKey = settings["apiKey"]
    apiSecret = settings["apiSecret"]

def create_copy(i):
    log.info(f"Creating copy {i + 1} of {COPIES}...")
    with open('./settings.json') as f:
        settings = json.load(f)
    current = settings["template"]
    current = iterate_json_object(current)
    
    path = f"{OUTPUT_DIR}/copy_{i + 1}.json"
    # Write to file
    with open(path, "w") as f:
        json.dump(current, f)
        log.info(f"JSON written to {path}.json")
        generated_json_paths.append(path)

# ---------------------
# Main:

create_dir_if_not_exists(OUTPUT_DIR)

with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
    for i in range(0, COPIES):
        futures.append(executor.submit(create_copy, i))

if not UPLOAD_JSON_TO_IPFS:
    log.info("Done!")
    exit()

log.info("--------")
log.info("Uploading JSON to IPFS...")

futures = []

with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor2:
    for i in range(0, len(generated_json_paths)):
        futures.append(executor2.submit(upload_to_ipfs, generated_json_paths[i], True))

concurrent.futures.wait(futures)

with open(f"{OUTPUT_DIR}/ipfs_paths.txt", "w") as f:
    f.write("\n---------\n")
    f.write(f"Timestamp: {datetime.datetime.now()}\n")
    for i in range(0, len(generated_ipfs_links)):
    # Write to file
        f.write(f"{generated_ipfs_links[i]}\n")

log.debug(generated_ipfs_links)
log.info("Done!")
log.info("You can find the IPFS links in ipfs_paths.txt")