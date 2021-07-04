import argparse
from app.app import app
import sys
import config
import os
import shutil

if __name__ == "__main__":

    sys.path.append(config.IMAGE_DIR)
    
    if os.path.exists(config.IMAGE_DIR):
        shutil.rmtree(config.IMAGE_DIR)

    shutil.copytree(config.INPUT_DIR, config.IMAGE_DIR)
    
    parser = argparse.ArgumentParser(description="Start the annotation server")
    parser.add_argument('--host', default="localhost")
    parser.add_argument('--port', default=5000)
    args = parser.parse_args()
    app.run(host=args.host, port=args.port, debug=True)
