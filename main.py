import sys
import os

# Ensure the parent directory is in the path if needed
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ui import cli

if __name__ == "__main__":
    cli.run()