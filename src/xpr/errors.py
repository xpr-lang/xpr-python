class XprError(Exception):
    def __init__(self, message: str, position: int = -1):
        super().__init__(message)
        self.position = position
