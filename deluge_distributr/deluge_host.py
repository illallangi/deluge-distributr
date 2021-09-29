from base64 import encodestring
from hashlib import sha1
from os.path import basename

from bencoding import bdecode, bencode

from deluge_client import DelugeRPCClient

from loguru import logger

from .exceptions import DelugeNotConnectedException, TorrentAlreadyPresentException


class DelugeHost(object):
    def __init__(self, host, port, username, password):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.client = DelugeRPCClient(
            self.host, self.port, self.username, self.password
        )
        self.client.connect()
        if not self.client.connected:
            raise DelugeNotConnectedException()

    @property
    def display(self):
        return f"{self.username}@{self.host}:{self.port}"

    @property
    def torrent_hashes(self):
        if "_torrent_hashes" not in self.__dict__ or self._torrent_hashes is None:
            logger.debug("Getting hashes from {}", self.display)

            self._torrent_hashes = [
                key.decode("utf-8")
                for key in self.client.call("core.get_torrents_status", {}, []).keys()
            ]

        return self._torrent_hashes

    @property
    def torrent_count(self):
        return len(self.torrent_hashes)

    def add_torrent(self, torrent):
        with open(torrent, "rb") as file:
            data = bdecode(file.read())
        info = data[b"info"]
        hash = sha1(bencode(info)).hexdigest()
        if hash in self.torrent_hashes or []:
            raise TorrentAlreadyPresentException(hash)

        with open(torrent, "rb") as file:
            filedump = encodestring(file.read())
        filename = basename(torrent)
        result = self.client.call("core.add_torrent_file", filename, filedump, {})
        logger.debug("Returning {}", result.decode("utf-8"))
        if result.decode("utf-8") != hash:
            raise Exception(result.decode("utf-8"))
        self._torrent_hashes = None
        return True
