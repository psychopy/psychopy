"""Build rst files appropriate for the **currently-installed** psychopy.alerts
"""
from pathlib import Path
from psychopy.alerts import catalog

alertDocsRoot = Path("./source/alerts")

for ID in catalog.alert:
    alert = catalog.alert[ID]
    print(f"alert {ID}: {alert['synopsis']}")
    with open(alertDocsRoot / str(ID)+'.rst', 'w') as f:
        f.write(f"PsychoPy Alert {ID}\n")
        f.write(f"======================\n\n")
        f.write(f"Synopsis\n")
        f.write(f"-----------\n\n")
        f.write(alert["synopsis"] + "\n")
