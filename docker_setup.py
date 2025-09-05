#!/usr/bin/env python3
import os
import subprocess
import time
import requests

# ===== CONFIG =====
PROJECT_DIR = os.path.expanduser("~/media-server")
PUID = os.getuid()
PGID = os.getgid()
TZ = "Asia/Colombo"


# Ports
QBIT_PORT = 8080
SONARR_PORT = 8989
RADARR_PORT = 7878
JELLYFIN_PORT = 8096
OMBI_PORT = 3579
JACKETT_PORT = 9117
PROWLARR_PORT = 9696
NAVIDROME_PORT = 4533
LIDARR_PORT = 8686

DOCKER_NETWORK = "media-server-net"

QBIT_USER = "admin"
QBIT_PASS = "adminadmin"

# ==================

def run(cmd, check=True):
    print(f"→ {cmd}")
    result = subprocess.run(cmd, shell=True)
    if check and result.returncode != 0:
        raise SystemExit(f"❌ Command failed: {cmd}")

def create_folders():
    print(f"📁 Creating project folders under {PROJECT_DIR}")
    folders = [
        "downloads",
        "media/movies",
        "media/tv",
        "media/music",
        "qbittorrent/config",
        "sonarr/config",
        "radarr/config",
        "jellyfin/config",
        "ombi/config",
        "jackett/config",
        "prowlarr/config",
        "navidrome/data",
        "lidarr/config"
    ]
    for f in folders:
        os.makedirs(os.path.join(PROJECT_DIR, f), exist_ok=True)

def clean_old_containers():
    containers = [
        "qbittorrent", "sonarr", "radarr", "jellyfin", "ombi", "jackett",
        "prowlarr", "navidrome", "lidarr"
    ]
    for c in containers:
        run(f"docker rm -f {c}", check=False)

def create_network():
    print(f"🌐 Creating Docker network '{DOCKER_NETWORK}'...")
    result = subprocess.run(f"docker network inspect {DOCKER_NETWORK}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if result.returncode != 0:
        run(f"docker network create {DOCKER_NETWORK}")

def wait_for_service(url, timeout=120):
    print(f"⏳ Waiting for {url}")
    for _ in range(timeout):
        try:
            r = requests.get(url, timeout=3)
            if r.status_code < 500:
                print(f"✅ {url} is ready")
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(2)
    print(f"⚠️ Timeout waiting for {url}")
    return False

def start_qbittorrent():
    print("🚀 Starting qBittorrent...")
    run(f"""
    docker run -d --name=qbittorrent --network={DOCKER_NETWORK} \
      -e PUID={PUID} -e PGID={PGID} -e TZ={TZ} -e WEBUI_PORT={QBIT_PORT} \
      -p {QBIT_PORT}:8080 -p 6881:6881 -p 6881:6881/udp \
      -v {PROJECT_DIR}/qbittorrent/config:/config \
      -v {PROJECT_DIR}/downloads:/downloads \
      lscr.io/linuxserver/qbittorrent:latest
    """)
    wait_for_service(f"http://localhost:{QBIT_PORT}")

def start_jackett():
    print("🚀 Starting Jackett...")
    run(f"""
    docker run -d --name=jackett --network={DOCKER_NETWORK} \
      -e PUID={PUID} -e PGID={PGID} -e TZ={TZ} \
      -p {JACKETT_PORT}:9117 \
      -v {PROJECT_DIR}/jackett/config:/config \
      lscr.io/linuxserver/jackett:latest
    """)
    wait_for_service(f"http://localhost:{JACKETT_PORT}")

def start_other_containers():
        print("🚀 Starting Sonarr, Radarr, Jellyfin, Ombi, Prowlarr, Navidrome, Lidarr...")
        # Sonarr
        run(f"""
        docker run -d --name=sonarr --network={DOCKER_NETWORK} \
            -e PUID={PUID} -e PGID={PGID} -e TZ={TZ} \
            -v {PROJECT_DIR}/sonarr/config:/config \
            -v {PROJECT_DIR}/downloads:/downloads \
            -v {PROJECT_DIR}/media/tv:/tv \
            -p {SONARR_PORT}:8989 \
            lscr.io/linuxserver/sonarr:latest
        """)
        # Radarr
        run(f"""
        docker run -d --name=radarr --network={DOCKER_NETWORK} \
            -e PUID={PUID} -e PGID={PGID} -e TZ={TZ} \
            -v {PROJECT_DIR}/radarr/config:/config \
            -v {PROJECT_DIR}/downloads:/downloads \
            -v {PROJECT_DIR}/media/movies:/movies \
            -p {RADARR_PORT}:7878 \
            lscr.io/linuxserver/radarr:latest
        """)
        # Jellyfin
        run(f"""
        docker run -d --name=jellyfin --network={DOCKER_NETWORK} \
            -e PUID={PUID} -e PGID={PGID} -e TZ={TZ} \
            -v {PROJECT_DIR}/jellyfin/config:/config \
            -v {PROJECT_DIR}/media:/media \
            -p {JELLYFIN_PORT}:8096 \
            lscr.io/linuxserver/jellyfin:latest
        """)
        # Ombi
        run(f"""
        docker run -d --name=ombi --network={DOCKER_NETWORK} \
            -e PUID={PUID} -e PGID={PGID} -e TZ={TZ} \
            -v {PROJECT_DIR}/ombi/config:/config \
            -p {OMBI_PORT}:3579 \
            lscr.io/linuxserver/ombi:latest
        """)
        # Prowlarr
        run(f"""
        docker run -d --name=prowlarr --network={DOCKER_NETWORK} \
            -e PUID={PUID} -e PGID={PGID} -e TZ={TZ} \
            -v {PROJECT_DIR}/prowlarr/config:/config \
            -p {PROWLARR_PORT}:9696 \
            lscr.io/linuxserver/prowlarr:latest
        """)
        # Navidrome
        run(f"""
        docker run -d --name=navidrome --network={DOCKER_NETWORK} \
            -e PUID={PUID} -e PGID={PGID} -e TZ={TZ} \
            -v {PROJECT_DIR}/navidrome/data:/data \
            -v {PROJECT_DIR}/media/music:/music \
            -p {NAVIDROME_PORT}:4533 \
            deluan/navidrome:latest
        """)
        # Lidarr
        run(f"""
        docker run -d --name=lidarr --network={DOCKER_NETWORK} \
            -e PUID={PUID} -e PGID={PGID} -e TZ={TZ} \
            -v {PROJECT_DIR}/lidarr/config:/config \
            -v {PROJECT_DIR}/downloads:/downloads \
            -v {PROJECT_DIR}/media/music:/music \
            -p {LIDARR_PORT}:8686 \
            lscr.io/linuxserver/lidarr:latest
        """)

def main():
    print("=== Media Server Setup ===")
    create_folders()
    clean_old_containers()
    create_network()
    start_qbittorrent()
    start_jackett()
    start_other_containers()

    print("\n✅ Media server stack started!")
    print(f"qBittorrent: http://localhost:{QBIT_PORT}")
    print(f"Jackett:     http://localhost:{JACKETT_PORT}")
    print(f"Sonarr:      http://localhost:{SONARR_PORT}")
    print(f"Radarr:      http://localhost:{RADARR_PORT}")
    print(f"Jellyfin:    http://localhost:{JELLYFIN_PORT}")
    print(f"Ombi:        http://localhost:{OMBI_PORT}")
    print(f"Prowlarr:    http://localhost:{PROWLARR_PORT}")
    print(f"Navidrome:   http://localhost:{NAVIDROME_PORT}")
    print(f"Lidarr:      http://localhost:{LIDARR_PORT}")
    print("\n⚠️ First login to qBittorrent and Jackett WebUI to set passwords and add indexers.")
    print("Then in Radarr/Sonarr/Lidarr, add Jackett and Prowlarr as indexers and connect qBittorrent as download client.")

if __name__ == "__main__":
    main()
