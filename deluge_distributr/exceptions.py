class DelugeNotConnectedException(Exception):
    pass


class TorrentAlreadyPresentException(Exception):
    def __init__(self, hash):
        self.hash = hash
        super().__init__(f'Hash {hash} is already present on the host.')
