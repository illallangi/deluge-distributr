from hashlib import sha1
from json import JSONDecoder
from os.path import isfile, join
from re import Pattern, compile
from socket import timeout

from bencoding import bdecode, bencode

from click import get_app_dir

from loguru import logger

from .deluge_host import DelugeHost
from .exceptions import DelugeNotConnectedException

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
        return join(self.config_path, 'hostlist.conf.1.2')

    @property
    def hosts(self):
        if '_hosts' not in self.__dict__ or self._hosts is None:
            self._hosts = []
        if len(self._hosts) == 0 and isfile(self.hostlist):
            logger.debug('Getting hosts', len(self._hosts))
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
                        for host in [
                            host
                            for host in obj['hosts']
                            if self.host_filter.search(host[1])
                        ]:
                            logger.debug('Adding {}@{}:{}', host[3], host[1], host[2])
                            try:
                                result = DelugeHost(
                                    host=host[1],
                                    port=host[2],
                                    username=host[3],
                                    password=host[4]
                                )
                                self._hosts.append(result)
                            except timeout:
                                logger.error('Timeout connecting to {}@{}:{}', host[3], host[1], host[2])
                            except BrokenPipeError:
                                logger.error('Broken Pipe connecting to {}@{}:{}', host[3], host[1], host[2])
                            except ConnectionAbortedError:
                                logger.error('Connection Aborted connecting to {}@{}:{}', host[3], host[1], host[2])
                            except ConnectionRefusedError:
                                logger.error('Connection Refused connecting to {}@{}:{}', host[3], host[1], host[2])
                            except ConnectionResetError:
                                logger.error('Connection Reset connecting to {}@{}:{}', host[3], host[1], host[2])
                            except DelugeNotConnectedException:
                                logger.error('Connection to {}@{}:{} failed', host[3], host[1], host[2])
            logger.debug('Got {} hosts', len(self._hosts))
        return self._hosts

    @property
    def torrent_hashes(self):
        result = []
        for host in self.hosts:
            for hash in host.torrent_hashes or []:
                if hash in result:
                    raise DuplicateTorrentInCollectionException(host.display, hash)
                result.append(hash)
        return result

    @property
    def torrent_count(self):
        return len(self.torrent_hashes)

    def add_torrent(
            self,
            torrent):
        with open(torrent, "rb") as file:
            data = bdecode(file.read())
        info = data[b'info']
        hash = sha1(bencode(info)).hexdigest()
        if hash in self.torrent_hashes:
            raise TorrentAlreadyPresentInCollectionException(hash)

        host = min(self.hosts, key=lambda host: host.torrent_count)
        if host.torrent_count >= self.max_torrents:
            raise AllDelugeHostsInCollectionFullException()

        if host.add_torrent(torrent):
            logger.success('Added {} to {}', torrent, host.display)
            self._torrent_hashes = None
            return True
        return False


class TorrentAlreadyPresentInCollectionException(Exception):
    def __init__(
            self,
            hash):
        self.hash = hash
        super().__init__(f'Hash {hash} is already present on a host in the collection.')


class AllDelugeHostsInCollectionFullException(Exception):
    def __init__(self):
        super().__init__('All hosts in the collection have more than the permitted number of torrents')


class DuplicateTorrentInCollectionException(Exception):
    def __init__(
            self,
            host,
            hash):
        self.host = host
        self.hash = hash
        super().__init__(f'Hash {hash} on {host} is already present on another host in the collection')
