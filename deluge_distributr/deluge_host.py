from base64 import encodestring
from hashlib import sha1
from os.path import basename

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

    def get_torrent_hashes(self):
        client = DelugeRPCClient(
            self.host,
            self.port,
            self.username,
            self.password)
        client.connect()
        if not client.connected:
            logger.error('Connection to {} failed', self.display)
            return None
        result = client.call('core.get_torrents_status', {}, [])
        result = [
            key.decode("utf-8")
            for key
            in result.keys()
        ]
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
            raise TorrentAlreadyPresentException(hash)

        client = DelugeRPCClient(
            self.host,
            self.port,
            self.username,
            self.password)
        client.connect()
        if not client.connected:
            logger.error('Connection to {} failed', self.display)
            return None
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


class TorrentAlreadyPresentException(Exception):
    def __init__(self, hash):
        self.hash = hash
        super().__init__(f'Hash {hash} is already present on the host.')
