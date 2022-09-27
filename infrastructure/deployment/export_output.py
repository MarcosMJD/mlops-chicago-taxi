"""
Script that will print the export commands to create env vars from Terraform output
Use:
    Windows: eval $(python.exe export_output.py) in GitBash
    Linux: eval $(python export_output.py)
"""

import os
import json

if __name__ == "__main__":

    COMMAND = "terraform.exe output --json > output.vars"
    os.system(COMMAND)

    with open("output.vars", "rt") as f_in:
        env_vars = json.load(f_in)
        for key, value in env_vars.items():
            print(f"export {key.upper()}={value['value']}")
