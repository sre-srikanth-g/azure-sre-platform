#!/usr/bin/env python3
"""
=============================================================================
alert_handler.py — Automated Alert Response Script
Author: Srikanth Gandikota
Project: azure-sre-platform

PURPOSE:
    Automatically fixes common Azure infrastructure problems.
    Instead of paging an engineer for every known issue,
    this script attempts a safe fix first.
    Only escalates to a human if the automatic fix fails.

ACTIONS THIS SCRIPT CAN PERFORM:
    1. restart-vm   — Restart a stopped or unresponsive VM
    2. disk-cleanup — Clean up old log files when disk is full

HOW TO RUN:
    python3 scripts/alert_handler.py --action restart-vm --rg my-rg --vm my-vm
    python3 scripts/alert_handler.py --action disk-cleanup --rg my-rg --vm my-vm

SRE CONTEXT:
    Every action is logged to audit_trail.jsonl
    This audit trail is critical in healthcare environments —
    you must be able to prove what the automation did and when.
=============================================================================
"""

import subprocess
import json
import datetime
import sys
import argparse
import logging
import os

# =============================================================================
# LOGGING SETUP
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("alert_handler.log"),
    ]
)
logger = logging.getLogger(__name__)


# =============================================================================
# AUDIT TRAIL
# Every automated action is recorded here — who did what, when, and why
# =============================================================================

def write_audit_log(action, resource, outcome, details=""):
    """
    Write a record of every automated action to the audit trail.

    WHY THIS MATTERS:
        In healthcare SaaS, automated systems must be auditable.
        If something goes wrong, you need to prove exactly what
        the automation did, when it did it, and what the result was.
        This is not optional — it is a compliance requirement.
    """
    entry = {
        "timestamp":    datetime.datetime.utcnow().isoformat(),
        "action":       action,
        "resource":     resource,
        "outcome":      outcome,
        "details":      details,
        "triggered_by": "alert_handler.py (automated)",
        "operator":     os.environ.get("GITHUB_ACTOR", "local-run")
    }

    # Append to the audit file — one JSON object per line
    with open("audit_trail.jsonl", "a") as f:
        f.write(json.dumps(entry) + "\n")

    logger.info(
        f"AUDIT LOGGED — "
        f"action={action} resource={resource} outcome={outcome}"
    )


# =============================================================================
# ACTION 1 — RESTART VM
# Safe to run automatically — restarting a VM fixes many common issues
# like hung processes, out-of-memory crashes, kernel panics
# =============================================================================

def restart_vm(resource_group, vm_name):
    """
    Safely restart an Azure VM.

    Steps:
        1. Check current state so we know what we started with
        2. Send the restart command
        3. Log the outcome to the audit trail
        4. Return True if successful, False if failed

    Args:
        resource_group: Azure resource group name
        vm_name: Name of the VM to restart

    Returns:
        True if restart succeeded, False if it failed
    """
    logger.info(f"ACTION: Restarting VM {vm_name}")
    logger.info(f"Reason: VM health check failed or availability alert fired")

    try:
        # Step 1 — Check current state before we do anything
        check = subprocess.run(
            [
                "az", "vm", "show",
                "--resource-group", resource_group,
                "--name", vm_name,
                "--show-details",
                "--output", "json"
            ],
            capture_output=True, text=True, timeout=30
        )
        vm_info      = json.loads(check.stdout)
        before_state = vm_info.get("powerState", "Unknown")
        logger.info(f"VM state before restart: {before_state}")

        # Step 2 — Send the restart command
        restart = subprocess.run(
            [
                "az", "vm", "restart",
                "--resource-group", resource_group,
                "--name", vm_name
            ],
            capture_output=True, text=True, timeout=120
        )

        # Step 3 — Check if it worked
        if restart.returncode == 0:
            logger.info(f"VM {vm_name} restarted successfully")
            write_audit_log(
                action="vm_restart",
                resource=vm_name,
                outcome="success",
                details=f"Restarted from state: {before_state}"
            )
            return True
        else:
            logger.error(f"VM restart failed: {restart.stderr}")
            write_audit_log(
                action="vm_restart",
                resource=vm_name,
                outcome="failed",
                details=restart.stderr
            )
            return False

    except Exception as e:
        logger.error(f"VM restart error: {e}")
        write_audit_log(
            action="vm_restart",
            resource=vm_name,
            outcome="error",
            details=str(e)
        )
        return False


# =============================================================================
# ACTION 2 — DISK CLEANUP
# Runs a cleanup script ON the VM remotely using Azure Run Command
# Azure Run Command = run a shell script on a VM without SSH
# =============================================================================

def disk_cleanup(resource_group, vm_name):
    """
    Clean up old log files on a VM when disk space is running low.

    Uses Azure Run Command to execute a shell script remotely.
    No SSH needed — Azure handles the connection securely.

    Args:
        resource_group: Azure resource group name
        vm_name: Name of the VM to clean

    Returns:
        True if cleanup succeeded, False if it failed
    """
    logger.info(f"ACTION: Running disk cleanup on {vm_name}")

    # Shell script that runs ON the VM
    # It cleans up old logs and reports disk usage before and after
    cleanup_script = """
#!/bin/bash
echo "=== Disk usage BEFORE cleanup ==="
df -h /

echo "=== Removing old log files (older than 7 days) ==="
find /var/log -name "*.gz" -mtime +7 -delete 2>/dev/null
find /var/log -name "*.1"  -mtime +7 -delete 2>/dev/null

echo "=== Cleaning package cache ==="
apt-get clean 2>/dev/null

echo "=== Removing temp files ==="
find /tmp -mtime +1 -delete 2>/dev/null

echo "=== Disk usage AFTER cleanup ==="
df -h /

DISK_USED=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
echo "Current disk usage: ${DISK_USED}%"

if [ "$DISK_USED" -gt 85 ]; then
    echo "WARNING: Disk still above 85% after cleanup"
    exit 1
else
    echo "OK: Disk is now below 85%"
    exit 0
fi
"""

    try:
        result = subprocess.run(
            [
                "az", "vm", "run-command", "invoke",
                "--resource-group", resource_group,
                "--name", vm_name,
                "--command-id", "RunShellScript",
                "--scripts", cleanup_script,
                "--output", "json"
            ],
            capture_output=True, text=True, timeout=120
        )

        output_data = json.loads(result.stdout)
        stdout_text = (
            output_data
            .get("value", [{}])[0]
            .get("message", "No output")
        )

        logger.info(f"Disk cleanup output:\n{stdout_text}")

        success = result.returncode == 0
        write_audit_log(
            action="disk_cleanup",
            resource=vm_name,
            outcome="success" if success else "failed",
            details=stdout_text[:300]
        )
        return success

    except Exception as e:
        logger.error(f"Disk cleanup error: {e}")
        write_audit_log(
            action="disk_cleanup",
            resource=vm_name,
            outcome="error",
            details=str(e)
        )
        return False


# =============================================================================
# ARGUMENT PARSER
# Makes the script accept command line arguments
# Example: python3 alert_handler.py --action restart-vm --rg my-rg --vm my-vm
# =============================================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description="Azure Alert Handler — Automated Remediation"
    )
    parser.add_argument(
        "--action", "-a",
        required=True,
        choices=["restart-vm", "disk-cleanup"],
        help="Which remediation action to perform"
    )
    parser.add_argument(
        "--rg", "-g",
        required=True,
        help="Azure resource group name"
    )
    parser.add_argument(
        "--vm", "-v",
        required=True,
        help="VM name to act on"
    )
    return parser.parse_args()


# =============================================================================
# MAIN
# =============================================================================

def main():
    args = parse_args()

    logger.info("=" * 50)
    logger.info(f"Alert Handler — Action: {args.action}")
    logger.info(f"Target VM: {args.vm} in {args.rg}")
    logger.info("=" * 50)

    success = False

    if args.action == "restart-vm":
        success = restart_vm(args.rg, args.vm)

    elif args.action == "disk-cleanup":
        success = disk_cleanup(args.rg, args.vm)

    logger.info("=" * 50)

    # Exit with error code if the action failed
    # This tells GitHub Actions the remediation did not work
    # and a human needs to be paged
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
