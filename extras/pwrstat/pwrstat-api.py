#!/usr/bin/env python3
"""REST API wrapper for CyberPower pwrstat utility."""

import logging
import os
import re
import subprocess
from flask import Flask, jsonify, make_response

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("pwrstat-api")

app = Flask(__name__)

STATUS_PATTERN = re.compile(r"^\s*(.*?)\.{2,}\s*(.*)$")


def get_pwrstat_status() -> dict[str, str]:
    """Execute 'pwrstat -status' and parse the output into a dictionary."""
    proc = subprocess.run(
        ["pwrstat", "-status"],
        capture_output=True,
        text=True,
        timeout=5,
        check=True,
    )

    data: dict[str, str] = {}
    for line in proc.stdout.splitlines():
        match = STATUS_PATTERN.match(line)
        if match:
            key = match.group(1).strip()
            val = match.group(2).strip()
            data[key] = val

    return data


@app.get("/pwrstat")
def pwrstat_status():
    """Return all UPS parameters as a JSON object."""
    try:
        data = get_pwrstat_status()
        if not data:
            return make_response(
                jsonify({"error": "No UPS data returned from pwrstat"}), 503
            )
        return jsonify(data)
    except FileNotFoundError:
        logger.error("'pwrstat' binary not found. Ensure /usr/sbin/pwrstat is mounted.")
        return make_response(
            jsonify({"error": "pwrstat binary not found"}), 500
        )
    except subprocess.TimeoutExpired:
        logger.error("pwrstat command timed out.")
        return make_response(
            jsonify({"error": "pwrstat command timed out"}), 504
        )
    except subprocess.CalledProcessError as err:
        logger.error("pwrstat failed with exit code %s: %s", err.returncode, err.stderr)
        return make_response(
            jsonify({"error": "pwrstat execution failed", "details": err.stderr.strip()}), 503
        )
    except Exception as err:
        logger.exception("Unexpected error fetching pwrstat data")
        return make_response(jsonify({"error": str(err)}), 500)


@app.get("/health")
@app.get("/")
def health():
    """Healthcheck endpoint."""
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "5002"))
    logger.info("Starting pwrstat-api on %s:%s", host, port)
    app.run(host=host, port=port)
