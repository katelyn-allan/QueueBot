class NotEnoughPlayersException(Exception):
    pass


class GameIsInProgressException(Exception):
    pass


class AlreadyInQueueException(Exception):
    def __init__(self, user):
        self.user = user


class PlayerNotFoundException(Exception):
    def __init__(self, user):
        self.user = user


class NoValidGameException(Exception):
    pass


class GameInProgressException(Exception):
    pass


class NoGameInProgressException(Exception):
    pass


class NotAdminException(Exception):
    pass


class NoMainRoleException(Exception):
    def __init__(self, user):
        self.user = user


class NoGuildException(Exception):
    pass


class CouldNotFindChannelException(Exception):
    def __init__(self, name: str, channel_id: int):
        self.name = name
        self.channel_id = channel_id
