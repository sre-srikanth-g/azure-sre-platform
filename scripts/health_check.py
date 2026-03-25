#!/usr/bin/env python3
"""
=============================================================================
health_check.py — Azure VM Health Check Script
Author: Srikanth Gandikota
Project: azure-sre-platform

PURPOSE:
    Checks if Azure VMs are healthy by querying Azure CLI.
    Logs results to a file and exits with error code if any VM is unhealthy.
    Used as an automated gate in the CI/CD pipeline — runs every hour.

SRE CONTEXT:
    This script is the automated equivalent of an on-call engineer
    manually checking if VMs are running. Instead of waking someone
    up at 2am to check, this runs automatically and only creates an
    alert if something is actually wrong.

HOW TO RUN:
    python3 scripts/health_check.py

=============================================================================
"""

import subprocess   # Lets Python run command line tools like Azure CLI
import json         # Lets Python read JSON responses from Azure CLI
import datetime     # Lets Python work with dates and times
import sys          # Lets Python exit with a specific exit code
import logging      # Lets Python write structured log messages

# =============================================================================
# LOGGING SETUP
# Writes messages to both the screen AND a log file at the same time
# This is important for SRE work — you always want a written record
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),       # Print to screen
        logging.FileHandler("health_check.log"), # Save to file
    ]
)
logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# List of VMs to check — add more VMs here as your infrastructure grows
# =============================================================================

VMS_TO_CHECK = [
    {
        "resource_group": "sre-demo-dev-rg",
        "vm_name":        "sre-demo-dev-vm",
        "environment":    "dev"
    }
]


# =============================================================================
# FUNCTIONS
# Each function does one specific job — this is good Python practice
# =============================================================================

def get_vm_status(resource_group, vm_name):
    """
    Ask Azure what state a VM is in right now.

    Possible states:
        VM running      = healthy, everything is fine
        VM stopped      = stopped but still costing money
        VM deallocated  = fully stopped, no cost
        VM starting     = starting up, wait a moment
        Unknown         = we could not get the status

    Returns the state as a text string.
    """
    logger.info(f"Checking VM: {vm_name} in resource group: {resource_group}")

    try:
        # Run the Azure CLI command from inside Python
        # This is the same as typing this in your terminal:
        # az vm get-instance-view --resource-group X --name Y --output json
        result = subprocess.run(
            [
                "az", "vm", "get-instance-view",
                "--resource-group", resource_group,
                "--name", vm_name,
                "--output", "json"
            ],
            capture_output=True,  # Capture the output instead of printing it
            text=True,            # Return text instead of bytes
            timeout=30            # Give up after 30 seconds
        )

        # Check if the command failed
        if result.returncode != 0:
            logger.error(f"Azure CLI error: {result.stderr}")
            return "Unknown"

        # Convert the JSON text response into a Python dictionary
        vm_data = json.loads(result.stdout)

        # The response contains a list of statuses
        # We want the one that starts with "PowerState"
        statuses = vm_data.get("instanceView", {}).get("statuses", [])

        power_state = next(
            (
                s["displayStatus"]          # Get the human readable status
                for s in statuses           # Loop through each status
                if s.get("code", "")        # Find the one where code
                   .startswith("PowerState") # starts with PowerState
            ),
            "Unknown"  # Default value if nothing found
        )

        return power_state

    except subprocess.TimeoutExpired:
        logger.error(f"Timed out waiting for Azure CLI response")
        return "Unknown"

    except json.JSONDecodeError:
        logger.error(f"Could not read Azure CLI response as JSON")
        return "Unknown"

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return "Unknown"


def is_healthy(power_state):
    """
    Decide if a VM is healthy based on its power state.
    Only 'VM running' counts as healthy.
    """
    return power_state == "VM running"


def write_health_report(results):
    """
    Write a summary report to a JSON file.
    This file can be read by dashboards or CI/CD pipelines.
    """
    report = {
        "report_time":  datetime.datetime.utcnow().isoformat(),
        "total_vms":    len(results),
        "healthy_vms":  sum(1 for r in results if r["healthy"]),
        "unhealthy_vms": sum(1 for r in results if not r["healthy"]),
        "results":      results
    }

    # Write the report to a JSON file
    import json as json_module
    with open("health_report.json", "w") as f:
        json_module.dump(report, f, indent=2)

    logger.info(
        f"Report written — "
        f"{report['healthy_vms']}/{report['total_vms']} VMs healthy"
    )


# =============================================================================
# MAIN — this runs when you execute the script
# =============================================================================

def main():
    logger.info("=" * 50)
    logger.info("Azure VM Health Check — Starting")
    logger.info("=" * 50)

    results = []

    # Check each VM in the list
    for vm_config in VMS_TO_CHECK:
        # Get the current status from Azure
        status = get_vm_status(
            vm_config["resource_group"],
            vm_config["vm_name"]
        )

        # Decide if it is healthy
        healthy = is_healthy(status)

        # Log the result with the right level
        if healthy:
            logger.info(
                f"HEALTHY — {vm_config['vm_name']} "
                f"({vm_config['environment']}): {status}"
            )
        else:
            logger.error(
                f"UNHEALTHY — {vm_config['vm_name']} "
                f"({vm_config['environment']}): {status}"
            )

        # Save the result
        results.append({
            "vm_name":     vm_config["vm_name"],
            "environment": vm_config["environment"],
            "status":      status,
            "healthy":     healthy,
            "checked_at":  datetime.datetime.utcnow().isoformat()
        })

    # Write the full report to a file
    write_health_report(results)

    logger.info("=" * 50)

    # Check if any VM was unhealthy
    unhealthy = [r for r in results if not r["healthy"]]

    if unhealthy:
        # Exit with code 1 = failure
        # This causes the GitHub Actions pipeline to FAIL
        # Which triggers a notification to the on-call engineer
        logger.error(
            f"HEALTH CHECK FAILED — "
            f"{len(unhealthy)} VM(s) are unhealthy"
        )
        sys.exit(1)
    else:
        # Exit with code 0 = success
        logger.info("HEALTH CHECK PASSED — All VMs healthy")
        sys.exit(0)


# This line means: only run main() if this file is executed directly
# Not if it is imported by another script
if __name__ == "__main__":
    main()
