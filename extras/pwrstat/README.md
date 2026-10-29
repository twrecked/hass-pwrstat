# PowerPanel (pwrstat) API Docker Service

This lightweight REST API wraps CyberPower's `pwrstat` utility and serves UPS status as a clean JSON object on a configurable port (default: `5002`).

Rather than bundling proprietary `.deb` packages inside the image, this container uses volume mounts to access the host's installed `pwrstat` binary and its IPC communication sockets.

---

## Prerequisites

1. **Host Setup**:
   Install **CyberPower PowerPanel for Linux** (`pwrstatd`) on the host machine connected via USB to your UPS.
   * [Download PowerPanel for Linux from CyberPower](https://www.cyberpowersystems.com/product/software/powerpanel-for-linux/)
   * Verify on your host that `pwrstat -status` works and `/var/pwrstatd.ipc` exists.

2. **Docker & Docker Compose**:
   Ensure Docker and Docker Compose (v2) are installed on the host.

---

## Quick Start with Docker Compose

1. Navigate to this directory:
   ```bash
   cd extras/pwrstat
   ```

2. Build and start the container:
   ```bash
   # Default port 5002
   HOME_NAME=office docker compose up -d --build

   # Custom port (e.g. 5003)
   PORT=5003 HOME_NAME=office docker compose up -d --build
   ```

3. Test the API:
   ```bash
   # Health check
   curl http://127.0.0.1:5002/health
   # {"status":"ok"}

   # UPS Status JSON
   curl http://127.0.0.1:5002/pwrstat
   ```

   Example output:
   ```json
   {
     "Battery Capacity": "100 %",
     "Firmware Number": "BF01902B1D1z",
     "Last Power Event": "None",
     "Line Interaction": "None",
     "Load": "86 Watt(23 %)",
     "Model Name": "ST Series",
     "Output Voltage": "120 V",
     "Power Supply by": "Utility Power",
     "Rating Power": "375 Watt",
     "Rating Voltage": "120 V",
     "Remaining Runtime": "19 min.",
     "State": "Normal",
     "Test Result": "Passed at 2024/01/01 12:00:00",
     "Utility Voltage": "120 V"
   }
   ```

---

## Environment Variables

| Variable | Default | Description |
| :--- | :--- | :--- |
| `PORT` | `5002` | Port on which the API listens |
| `HOME_NAME` | `ups` | Prefix for the Docker container name (`${HOME_NAME}-status`) |
| `LOG_LEVEL` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

You can set these via inline environment variables or in a local `.env` file:
```bash
echo "PORT=5003" >> .env
echo "HOME_NAME=office" >> .env
docker compose up -d
```

---

## Volume Mounts Explained

`docker-compose.yaml` mounts the following paths from the host:

| Host Path | Container Path | Purpose |
| :--- | :--- | :--- |
| `/usr/sbin/pwrstat` | `/usr/sbin/pwrstat:ro` | The CyberPower client binary |
| `/var/pwrstatd.ipc` | `/var/pwrstatd.ipc:ro` | IPC domain socket used by `pwrstat` to communicate with the daemon |
| `/var/pwrstatd.dev` | `/var/pwrstatd.dev:ro` | Device node communication link |
| `/etc/localtime` | `/etc/localtime:ro` | Host timezone synchronization |

`network_mode: host` is configured by default so the container binds directly to the host's network interfaces on the configured `PORT`.

---

## Standalone Docker Build & Run

If you prefer building and running manually without Docker Compose:

```bash
docker build -t ups-status:latest -f dockerfile .

docker run -d \
  --name ups-status \
  --restart unless-stopped \
  --network host \
  -e PORT=5003 \
  -v /etc/localtime:/etc/localtime:ro \
  -v /usr/sbin/pwrstat:/usr/sbin/pwrstat:ro \
  -v /var/pwrstatd.ipc:/var/pwrstatd.ipc:ro \
  -v /var/pwrstatd.dev:/var/pwrstatd.dev:ro \
  ups-status:latest
```
