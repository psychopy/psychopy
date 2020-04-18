"""Build rst files appropriate for the **currently-installed** psychopy.alerts
"""
from pathlib import Path
from psychopy.alerts import catalog

thisFolder = Path(__file__).parent
alertDocsRoot = thisFolder / "source/alerts"

for ID in catalog.alert:
    alert = catalog.alert[ID]
    if 'label' in alert:
        label = alert['label']
    else:
        label = alert['synopsis']

    with open(alertDocsRoot / (str(ID)+'.rst'), 'w') as f:
        titleStr = f"{ID}: {label}\n"
        f.write(f"{ID}: {label}\n")
        f.write(f"="*len(titleStr) + "\n\n")
        if 'synopsis' in alert:
            f.write(f"Synopsis\n")
            f.write(f"-----------\n\n")
            f.write(alert["synopsis"] + "\n\n")
        if 'details' in alert:
            f.write(f"Details\n")
            f.write(f"-----------\n\n")
            f.write(alert["details"] + "\n\n")
        if 'versions' in alert:
            f.write(f"PsychoPy versions affected\n")
            f.write(f"---------------------------\n\n")
            f.write(alert["versions"] + "\n\n")
        if 'solutions' in alert:
            f.write(f"Solutions\n")
            f.write(f"-----------\n\n")
            f.write(alert["solutions"] + "\n\n")
