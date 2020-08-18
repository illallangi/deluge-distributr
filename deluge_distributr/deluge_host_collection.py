from hashlib import sha1
from json import JSONDecoder
from os.path import isfile, join
from re import Pattern, compile

from bencoding import bdecode, bencode

from click import get_app_dir

from loguru import logger

from .deluge_host import DelugeHost

NOT_WHITESPACE = compile(r'[^\s]')


class DelugeHostCollection(object):
    def __init__(
            self,
            config_path=None,
            host_filter='.*',
            max_torrents=100):
        self.config_path = get_app_dir('deluge') if config_path is None else config_path
        self.host_filter = compile(host_filter) if not isinstance(host_filter, Pattern) else host_filter
        self.max_torrents = max_torrents

    @property
    def hostlist(self):
        if '_hostlist' not in self.__dict__ or self._hostlist is None:
            self._hostlist = join(self.config_path, 'hostlist.conf.1.2')
            logger.debug('Calculated {}', self._hostlist)
        return self._hostlist

    @property
    def hosts(self):
        if '_hosts' not in self.__dict__ or self._hosts is None:
            self._hosts = []
        if len(self._hosts) == 0 and isfile(self.hostlist):
            pos = 0
            decoder = JSONDecoder()
            with open(self.hostlist) as file:
                document = file.read()
                while True:
                    match = NOT_WHITESPACE.search(document, pos)
                    if not match:
                        break
                    pos = match.start()
                    obj, pos = decoder.raw_decode(document, pos)
                    if 'hosts' in obj.keys():
                        for h in obj['hosts']:
                            host = DelugeHost(
                                host=h[1],
                                port=h[2],
                                username=h[3],
                                password=h[4]
                            )
                            if self.host_filter.search(host.host):
                                self._hosts.append(host)
            logger.debug('Calculated [{}]', ','.join([host.display for host in self._hosts]))
        return self._hosts

    def get_torrent_hashes(self):
        result = []
        for host in self.hosts:
            for hash in host.get_torrent_hashes():
                if hash in result:
                    raise DuplicateTorrentInCollectionException(host.display, hash)
                result.append(hash)
        logger.debug('Calculated [{}]', ','.join(result))
        return result

    def get_torrent_count(self):
        result = len(self.get_torrent_hashes())
        logger.debug('Calculated {}', result)
        return result

    def add_torrent(self, torrent):
        with open(torrent, "rb") as file:
            data = bdecode(file.read())
        info = data[b'info']
        hash = sha1(bencode(info)).hexdigest()
        if hash in self.get_torrent_hashes():
            raise TorrentAlreadyPresentInCollectionException(hash)

        if len(self.hosts) == 0:
            raise NoDelugeHostsInCollectionException()

        host = min(self.hosts, key=lambda host: host.get_torrent_count())
        if host.get_torrent_count() >= self.max_torrents:
            raise AllDelugeHostsInCollectionFullException()

        logger.info('Adding {} to {}', torrent, host.display)
        host.add_torrent(torrent)


class TorrentAlreadyPresentInCollectionException(Exception):
    def __init__(self, hash):
        self.hash = hash
        super().__init__(f'Hash {hash} is already present on a host in the collection.')


class NoDelugeHostsInCollectionException(Exception):
    def __init__(self):
        super().__init__('No hosts in the collection')


class AllDelugeHostsInCollectionFullException(Exception):
    def __init__(self):
        super().__init__('All hosts in the collection have more than the permitted number of torrents')


class DuplicateTorrentInCollectionException(Exception):
    def __init__(self, host, hash):
        self.host = host
        self.hash = hash
        super().__init__(f'Hash {hash} on {host} is already present on another host in the collection')
