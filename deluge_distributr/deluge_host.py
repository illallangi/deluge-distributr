from base64 import encodestring
from hashlib import sha1
from os.path import basename
from socket import timeout

from bencoding import bdecode, bencode

from deluge_client import DelugeRPCClient

from loguru import logger


class DelugeHost(object):
    def __init__(self, host, port, username, password):
        self.host = host
        self.port = port
        self.username = username
        self.password = password

    @property
    def display(self):
        if '_display' not in self.__dict__ or self._display is None:
            self._display = f'{self.username}@{self.host}:{self.port}'
            logger.debug('Calculated {}', self._display)
        return self._display

    @property
    def torrent_hashes(self):
        if '_torrent_hashes' not in self.__dict__ or self._torrent_hashes is None:
            client = DelugeRPCClient(
                self.host,
                self.port,
                self.username,
                self.password)
            try:
                client.connect()
            except timeout:
                logger.error('Timed out connecting to {}', self.display)
                return None

            if not client.connected:
                logger.error('Connection to {} failed', self.display)
                return None

            self._torrent_hashes = [
                key.decode("utf-8")
                for key
                in client.call('core.get_torrents_status', {}, []).keys()
            ]

        return self._torrent_hashes

    @property
    def torrent_count(self):
        return None if self.torrent_hashes is None else len(self.torrent_hashes)

    def add_torrent(self, torrent):
        with open(torrent, "rb") as file:
            data = bdecode(file.read())
        info = data[b'info']
        hash = sha1(bencode(info)).hexdigest()
        if hash in self.torrent_hashes or []:
            raise TorrentAlreadyPresentException(hash)

        client = DelugeRPCClient(
            self.host,
            self.port,
            self.username,
            self.password)
        try:
            client.connect()
        except timeout:
            logger.error('Timed out connecting to {}', self.display)
            return False
        if not client.connected:
            logger.error('Connection to {} failed', self.display)
            return False

        with open(torrent, 'rb') as file:
            filedump = encodestring(file.read())
        filename = basename(torrent)
        result = client.call(
            'core.add_torrent_file',
            filename,
            filedump,
            {})
        logger.debug('Returning {}', result.decode("utf-8"))
        if result.decode("utf-8") != hash:
            raise Exception(result.decode("utf-8"))
        self._torrent_hashes = None
        return True


class TorrentAlreadyPresentException(Exception):
    def __init__(self, hash):
        self.hash = hash
        super().__init__(f'Hash {hash} is already present on the host.')
