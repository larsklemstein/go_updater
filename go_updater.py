#!/usr/bin/env python3

"""
Auto updater for a local Golang installation

"""

# bugs and hints: lrsklemstein@gmail.com

import argparse
import logging
import logging.config
import os.path
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile

import requests
from bs4 import BeautifulSoup

from typing import Any, Dict  # , List, Tuple, Callable

GO_BASE_URL = 'https://go.dev'
GO_DOWNLOAD_URL = GO_BASE_URL + '/dl/'


__log_level_default = logging.INFO


def main() -> None:
    setup = get_prog_setup_or_exit_with_usage()

    init_logging(setup)
    logger = logging.getLogger(__name__)

    try:
        sys.exit(run(setup))
    except Exception:
        logger.critical("Abort, rc=3", exc_info=True)
        sys.exit(3)


def get_prog_setup_or_exit_with_usage() -> Dict[str, Any]:
    parser = argparse.ArgumentParser(
                description=get_prog_doc(),
                formatter_class=argparse.RawTextHelpFormatter,
            )

    log_group = parser.add_mutually_exclusive_group()

    parser.add_argument(
        '--force', default=False, action='store_true',
        help='enforce installation',
    )

    parser.add_argument(
        'GO_PATH', help='the golang installation path',
    )

    log_group.add_argument(
        '--debug', action='store_true',
        help='enable debug log level',
    )

    log_group.add_argument(
        '--log_cfg', dest='log_cfg',
        help='optional logging cfg in ini format',
    )

    args = vars(parser.parse_args())
    args = {k: '' if v is None else v for k, v in args.items()}

    return args


def get_prog_doc() -> str:
    doc_str = sys.modules['__main__'].__doc__

    if doc_str is not None:
        return doc_str.strip()
    else:
        return '<???>'


def init_logging(setup: Dict[str, Any]) -> None:
    """Creates either a logger by cfg file or a default instance
    with given log level by arg --log_level (otherwise irgnored)

    """
    if setup['log_cfg'] == '':
        if setup['debug']:
            level = logging.DEBUG
            format = '%(levelname)s - %(message)s'
        else:
            level = __log_level_default
            format = '%(message)s'

        logging.basicConfig(level=level, format=format)
    else:
        logging.config.fileConfig(setup['log_cfg'])


def run(setup: Dict[str, Any]) -> int:
    logger = logging.getLogger(__name__)

    logger.info('Scan golang download page...')
    url, version_downloadable = get_latest_go_url_and_version()
    logger.info('Downloadable: ' + version_downloadable)

    version_installed = get_installed_go_version(setup['GO_PATH'])
    log_installed_version(version_installed)

    if version_downloadable == version_installed and not setup['force']:
        logger.info('Nothing to do')
        return 0

    install_go(url, setup['GO_PATH'])

    return 0


def log_installed_version(version_installed: str):
    logger = logging.getLogger(__name__)

    if version_installed == '':
        logger.info('Installed: None.')
    else:
        logger.info('Installed: ' + version_installed)


def get_latest_go_url_and_version() -> list[str,str]:
    pattern_linux_href = re.compile(
        r'/dl/(?P<version>go\d+\.\d+\.\d+)\.linux-amd64\.tar\.gz$')

    session = requests.Session()

    response = session.get(GO_DOWNLOAD_URL)

    page = response.content.decode()

    soup = BeautifulSoup(page, "html.parser")

    dw = soup.find_all('a', {'class': 'download downloadBox'})

    for e in dw:
        href = e.get('href')
        match = pattern_linux_href.match(href)
        if match:
            url = match.string
            version = match.group('version')
            url = GO_BASE_URL + url
            return url, version
    else:
        raise ValueError('unable to get Linux download link')


def get_installed_go_version(path: str) -> str:
    """Get version of installed go, return empty string when path is absent
    """
    if not os.path.isdir(path):
        return ''

    go_binary = os.path.join(path, 'bin', 'go')

    if not os.path.isfile(go_binary):
        raise IOError(f'assumed go binary "{go_binary}" not found')

    output = subprocess.run([go_binary, 'version'], stdout=subprocess.PIPE)

    version_complete = output.stdout.decode()

    version = version_complete.split()[2]

    return version


def download_go_archive(
        url: str, dest_dir: str, *, chunk_size: int = 8192) -> str:
    go_basename = url.split('/')[-1]
    download_path = os.path.join(dest_dir, go_basename)

    with requests.get(url, stream=True) as r:
        r.raise_for_status()

        with open(download_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=chunk_size):
                f.write(chunk)

    assert os.path.isfile(download_path)
    return download_path


def remove_installed_go(path: str):
    expected_go_bin = os.path.join(path, 'bin', 'go')
    assert os.path.isfile(expected_go_bin)

    shutil.rmtree(path)


def extract_tgz_to(archiv: str, path: str):
    tf = tarfile.open(archiv)

    sub_path = os.path.dirname(path)

    tf.extractall(sub_path)
    assert os.path.isdir(sub_path)


def install_go(url: str, path: str):
    logger = logging.getLogger(__name__)

    with tempfile.TemporaryDirectory() as tmpd:
        archive = download_go_archive(url, tmpd)
        logger.info(f'Downloaded {url}')

        if os.path.isdir(path):
            logger.info(f'Found old go installation...')
            remove_installed_go(path)
            logger.info(f'-> Removed.')

        extract_tgz_to(archive, path)
        logger.info(f'Installed  new go version')


if __name__ == '__main__':
    main()
