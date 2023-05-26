class NotEnoughPlayersException(Exception):
    pass


class GameIsInProgressException(Exception):
    pass


class AlreadyInQueueException(Exception):
    def __init__(self, user):
        self.user = user


class PlayerNotFoundException(Exception):
    def __init__(self, player):
        self.player = player
