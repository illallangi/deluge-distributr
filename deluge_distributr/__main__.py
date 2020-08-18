from os import makedirs, remove
from os.path import abspath, expandvars
from pathlib import Path
from sys import argv, stderr
from time import sleep

from click import Choice as CHOICE, INT, Path as PATH, STRING, command, get_app_dir, option

from loguru import logger

from .deluge_host_collection import DelugeHostCollection, TorrentAlreadyPresentInCollectionException


def resolve_path(ctx,
                 param,
                 value):
    value = abspath(expandvars(value))
    makedirs(value, exist_ok=True)
    return value


@command()
@option('--config-path',
        type=PATH(file_okay=False,
                  dir_okay=True,
                  writable=True,
                  readable=True,
                  resolve_path=False,
                  allow_dash=False),
        envvar='DELUGE_WATCH_PATH',
        default=get_app_dir('deluge'),
        callback=resolve_path)
@option('--watch-path',
        type=PATH(file_okay=False,
                  dir_okay=True,
                  writable=True,
                  readable=True,
                  resolve_path=False,
                  allow_dash=False),
        envvar='DELUGE_WATCH_PATH',
        default=get_app_dir('watch'),
        callback=resolve_path)
@option('--host-filter',
        type=STRING,
        envvar='DELUGE_HOST_FILTER',
        default='.*')
@option('--max-torrents',
        type=INT,
        envvar='DELUGE_MAX_TORRENTS',
        default=100)
@option('--sleep-time',
        type=INT,
        envvar='DELUGE_SLEEP_TIME',
        default=5)
@option('--log-level',
        type=CHOICE(['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'SUCCESS', 'TRACE'],
                    case_sensitive=False),
        envvar='DELUGE_LOG_LEVEL',
        default='DEBUG')
def main(config_path, watch_path, host_filter, max_torrents, sleep_time, log_level):
    """This script adds all torrents in a watch dir evenly to multiple deluge
    instances"""
    logger.remove()
    logger.add(stderr, level=log_level)

    logger.info(argv[0])
    logger.info('  --config-path "{}"', config_path)
    logger.info('  --watch-path "{}"', watch_path)
    logger.info('  --host-filter "{}"', host_filter)
    logger.info('  --max-torrents {}', max_torrents)
    logger.info('  --sleep-time {}', sleep_time)
    logger.info('  --log-level "{}"', log_level)

    while True:
        host = DelugeHostCollection(
            config_path=config_path,
            host_filter=host_filter,
            max_torrents=max_torrents)

        torrents = [
            torrent
            for torrent in Path(watch_path).rglob('*.torrent')
            if torrent.is_file()
        ]
        logger.info("{} .torrent files found", len(torrents))
        for torrent in torrents:
            try:
                host.add_torrent(torrent)
            except TorrentAlreadyPresentInCollectionException as err:
                logger.info(str(err))
            remove(torrent)
        sleep(sleep_time)


if __name__ == "__main__":
    main()
