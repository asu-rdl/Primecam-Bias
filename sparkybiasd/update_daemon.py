import requests
import os
from importlib import metadata
def get_current_version():
    try:
        version = metadata.version('sparkybiasd')
    except metadata.PackageNotFoundError:
        version = 'v0.0.0'  # Default version if package is not found
    return 'v'+version


def update():
    r = requests.get('https://api.github.com/repos/asu-rdl/Primecam-Bias/releases/latest')
    if r.status_code == 200:
        data = r.json()
        a = data['assets']
        assetdict = a[0]
        filename = assetdict['name']
        download_url = assetdict['browser_download_url']
        ourVersion = get_current_version()
        latestVersion = data['tag_name']
        if ourVersion == latestVersion:
            print("Versions match, no update needed.")
        else:
            print("New Version Available")
            print(f"Current Version: {ourVersion}")
            print(f"Latest Version: {latestVersion}")

            print(f"Downloading from: {download_url}")
            r = requests.get(download_url)
            if r.status_code == 200:
                with open(filename, 'wb') as f:
                    f.write(r.content)
                print("Download complete.")
                os.system("pip install --upgrade ./" + filename)
                os.system("rm " + filename)
            else:
                print(f"Failed to download the file: {r.status_code}")

if __name__ == "__main__":
    update()