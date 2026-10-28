import json
import os
from time import time
from sys import argv
from os.path import getmtime
from zipfile import ZipFile, ZIP_DEFLATED

BRANCH = os.environ.get('GITHUB_REF', 'refs/heads/master').split('refs/heads/')[-1]
REPOSITORY = os.environ.get('GITHUB_REPOSITORY', 'raindeer21/MyDalamudPlugins')
DOWNLOAD_URL = 'https://github.com/' + REPOSITORY + '/raw/{branch}/plugins/{plugin_name}/latest.zip'

DEFAULTS = {
    'IsHide': False,
    'IsTestingExclusive': False,
    'ApplicableVersion': 'any',
}

DUPLICATES = {
    'DownloadLinkInstall': ['DownloadLinkTesting', 'DownloadLinkUpdate'],
}

TRIMMED_KEYS = [
    'Author',
    'Name',
    'Punchline',
    'Description',
    'Changelog',
    'InternalName',
    'AssemblyVersion',
    'RepoUrl',
    'ApplicableVersion',
    'Tags',
    'CategoryTags',
    'AcceptsFeedback',
    'DalamudApiLevel',
    'LoadPriority',
    'IconUrl',
    'ImageUrls',
    'DownloadLinkInstall',
    'DownloadLinkUpdate',
    'DownloadLinkTesting',
]

def main():
    # Prefer the curated manifests; retain ZIP support for older entries.
    master = extract_manifests()

    # trim the manifests
    master = [trim_manifest(manifest) for manifest in master]

    # convert the list of manifests into a master list
    add_extra_fields(master)

    # write the master
    write_master(master)

    # update the LastUpdated field in master
    last_updated()

def extract_manifests():
    manifests = []

    for dirpath, dirnames, filenames in os.walk('./plugins'):
        dirnames.sort()
        plugin_name = dirpath.split('/')[-1]
        manifest_path = f'{dirpath}/{plugin_name}.json'
        if os.path.isfile(manifest_path):
            with open(manifest_path, encoding='utf-8') as f:
                manifests.append(json.load(f))
            continue
        if 'latest.zip' not in filenames:
            continue
        latest_zip = f'{dirpath}/latest.zip'
        with ZipFile(latest_zip) as z:
            manifest = json.loads(z.read(f'{plugin_name}.json').decode('utf-8'))
            manifests.append(manifest)

    return manifests

def add_extra_fields(manifests):
    for manifest in manifests:
        # generate the download link from the internal assembly name
        manifest.setdefault('DownloadLinkInstall', DOWNLOAD_URL.format(branch=BRANCH, plugin_name=manifest["InternalName"]))
        # add default values if missing
        for k, v in DEFAULTS.items():
            if k not in manifest:
                manifest[k] = v
        # duplicate keys as specified in DUPLICATES
        for source, keys in DUPLICATES.items():
            for k in keys:
                if k not in manifest:
                    manifest[k] = manifest[source]
        manifest['DownloadCount'] = 0

def write_master(master):
    # write as pretty json
    with open('pluginmaster.json', 'w', encoding='utf-8') as f:
        json.dump(master, f, indent=4, ensure_ascii=False)
        f.write('\n')

def trim_manifest(plugin):
    return {k: plugin[k] for k in TRIMMED_KEYS if k in plugin}

def last_updated():
    with open('pluginmaster.json', encoding='utf-8') as f:
        master = json.load(f)

    for plugin in master:
        latest = f'plugins/{plugin["InternalName"]}/latest.zip'
        manifest_path = f'plugins/{plugin["InternalName"]}/{plugin["InternalName"]}.json'
        modified = int(getmtime(manifest_path if os.path.isfile(manifest_path) else latest))

        if 'LastUpdate' not in plugin or modified != int(plugin['LastUpdate']):
            plugin['LastUpdate'] = str(modified)

    with open('pluginmaster.json', 'w', encoding='utf-8') as f:
        json.dump(master, f, indent=4, ensure_ascii=False)
        f.write('\n')

if __name__ == '__main__':
    main()
