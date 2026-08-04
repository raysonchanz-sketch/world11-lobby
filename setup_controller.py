import os
import sys
import subprocess
import json
import urllib.request
import zipfile
import tempfile

GAME_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(GAME_DIR, "settings.json")
DS4_DIR = os.path.join(GAME_DIR, "ds4windows")
DS4_MARKER = os.path.join(DS4_DIR, ".installed")

DS4_URL = "https://github.com/ds4windowsapp/DS4Windows/releases/download/Official/DS4Windows-Official.zip"


def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    return {}


def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)


def find_ds4windows():
    if os.path.exists(DS4_MARKER):
        exe = os.path.join(DS4_DIR, "DS4Windows.exe")
        if os.path.exists(exe):
            return DS4_DIR

    search_paths = [
        os.path.join(GAME_DIR, "ds4windows"),
        os.path.join(GAME_DIR, "DS4Windows"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "DS4Windows"),
        os.path.join(os.environ.get("PROGRAMFILES", ""), "DS4Windows"),
        os.path.join(os.environ.get("PROGRAMFILES(X86)", ""), "DS4Windows"),
    ]

    for base in [GAME_DIR]:
        if not os.path.isdir(base):
            continue
        for name in os.listdir(base):
            full = os.path.join(base, name)
            if os.path.isdir(full) and "ds4" in name.lower():
                exe = os.path.join(full, "DS4Windows.exe")
                if os.path.exists(exe):
                    search_paths.insert(0, full)
                nested = os.path.join(full, "DS4Windows")
                if os.path.isdir(nested):
                    exe2 = os.path.join(nested, "DS4Windows.exe")
                    if os.path.exists(exe2):
                        search_paths.insert(0, nested)

    for path in search_paths:
        exe = os.path.join(path, "DS4Windows.exe")
        if os.path.exists(exe):
            return path
    return None


def download_and_extract():
    print("\n  Downloading DS4Windows...")
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, "DS4Windows.zip")
        try:
            urllib.request.urlretrieve(DS4_URL, zip_path)
        except Exception as e:
            print(f"  Download failed: {e}")
            return False

        print("  Extracting...")
        try:
            os.makedirs(DS4_DIR, exist_ok=True)
            with zipfile.ZipFile(zip_path, "r") as zf:
                for member in zf.namelist():
                    if member.startswith("DS4Windows/") or member.startswith("DS4Windows\\"):
                        rel = member.split("/", 1)[-1] if "/" in member else member.split("\\", 1)[-1]
                        if rel:
                            target = os.path.join(DS4_DIR, rel)
                            if member.endswith("/"):
                                os.makedirs(target, exist_ok=True)
                            else:
                                os.makedirs(os.path.dirname(target), exist_ok=True)
                                with zf.open(member) as src, open(target, "wb") as dst:
                                    dst.write(src.read())
        except Exception as e:
            print(f"  Extract failed: {e}")
            return False

        with open(DS4_MARKER, "w") as f:
            f.write("done")
    return True


def is_controller_available():
    try:
        import pygame
        return pygame.joystick.get_count() > 0
    except Exception:
        return False


def setup_controller():
    settings = load_settings()

    if settings.get("controller_setup_done"):
        if is_controller_available():
            return True

    ds4_path = find_ds4windows()
    if not ds4_path:
        print("\n  PS4 controller needs drivers. Installing DS4Windows...")
        if not download_and_extract():
            print("  Install failed. You may need to download manually.")
            return False
        ds4_path = DS4_DIR

    exe = os.path.join(ds4_path, "DS4Windows.exe")
    if os.path.exists(exe):
        running = False
        try:
            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq DS4Windows.exe"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            running = "DS4Windows.exe" in result.stdout
        except Exception:
            pass

        if not running:
            print("  Starting DS4Windows...")
            subprocess.Popen([exe], cwd=ds4_path)

        settings["controller_setup_done"] = True
        save_settings(settings)
        return True

    return False


if __name__ == "__main__":
    setup_controller()
