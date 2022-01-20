"""
The Alert module
"""
from ._alerts import alert, catalog

import yaml
from pathlib import Path
import re


def validateCatalogue(dev=False):
    """
    Check that every value in the catalogue corresponds to a yaml file.

    dev : If True, then missing entries will be created from template. Useful when writing alerts.
    """
    # Define root folder
    root = Path(__file__).parent / "alertsCatalogue"
    # Make template object
    with open(root / "alertTemplate.yaml") as f:
        template = f.read()
    # Create blank array to store missing alert keys in
    missing = []

    def validate(spec):
        # Start off valid
        valid = True
        # Get category
        if "cat" in spec:
            cat = spec['cat']
        else:
            cat = "Unknown"
        for key, val in spec.items():
            if key == "cat" or key % 1000 == 0 or key == 9999:
                # Skip category tags
                continue
            if isinstance(val, str):
                # Check whether file exists
                file = root / f"{key}.yaml"
                valid = valid and file.is_file()
                # If in dev mode, make a new yaml file from template
                if dev and not file.is_file():
                    newAlert = template
                    # Replace whatever is possible at this stage
                    newAlert = re.sub(r"(?<=code\: )\d\d\d\d", str(key), newAlert)
                    newAlert = re.sub(r"(?<=cat\: ).*", str(cat), newAlert)
                    newAlert = re.sub(r"(?<=label\: ).*", str(val), newAlert)
                    # Save new file
                    with open(file, "w") as f:
                        f.write(newAlert)
                        f.close()
            # Store missing key
            if not valid:
                missing.append(key)
            if isinstance(val, dict):
                # Recursively search through dicts
                valid = valid and validate(val)
        return valid

    # Load catalog
    with open(root / "alertCategories.yaml") as f:
        spec = yaml.load(f, Loader=yaml.FullLoader)
    # Validate
    valid = validate(spec)
    return valid, missing
