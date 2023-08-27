from typing import Self

from discord import Member


class NotEnoughPlayersException(Exception):
    """Exception that is called when there are not enough players in the queue to start a game."""

    pass


class GameInProgressException(Exception):
    """Exception that is called when a game is already in progress."""

    pass


class AlreadyInQueueException(Exception):
    """Exception that is called when a player is already in the queue."""

    def __init__(self: Self, user: Member) -> None:
        """Init that takes in a user argument to return a descriptive message."""
        self.user = user


class PlayerNotFoundException(Exception):
    """Exception that is called when a player is not found in the queue, but a user attempts to remove them."""

    def __init__(self: Self, user: Member) -> None:
        """Init that takes in a user argument to return a descriptive message."""
        self.user = user


class NoValidGameException(Exception):
    """Exception that is called when there is no valid game able to be created."""

    pass


class NoGameInProgressException(Exception):
    """Exception that is called when there is no game in progress."""

    pass


class NotAdminException(Exception):
    """Exception that is called when a user is not an admin, but tries to use a protected command."""

    pass


class NoMainRoleException(Exception):
    """Exception that is called when a user does not have a main role, but attempts to join the queue."""

    def __init__(self: Self, user: Member) -> None:
        """Init that takes in a user argument to return a descriptive message."""
        self.user = user


class NoGuildException(Exception):
    """Exception that is called when a guild is not found."""

    pass


class ChannelNotFoundException(Exception):
    """Exception that is called when a channel is not found by its ID."""

    def __init__(self: Self, name: str, channel_id: int) -> None:
        """Init that takes in a name and channel_id argument to return a descriptive message."""
        self.name = name
        self.channel_id = channel_id
