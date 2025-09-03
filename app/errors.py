class NoMessagesFoundError(Exception):
    """Exception raised when no messages are found for a conversation id"""

    pass


class DatabaseError(Exception):
    """Exception raised when a database error occurs"""

    pass


class ModelExecutionError(Exception):
    """Exception raised when a model error occurs"""

    pass
