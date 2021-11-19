class RegtestAlreadyRunning(Exception):
    pass


class RegtestNodeNotRunning(Exception):
    pass


class WalletNotFounded(Exception):
    pass


class WalletAlreadyLoaded(Exception):
    pass


class WalletNotLoaded(Exception):
    pass


class WalletAlreadyExist(Exception):
    pass


class UnknownException(Exception):
    pass


class InvalidAddressType(Exception):
    pass


class InvalidParameter(Exception):
    pass


class NoCoinbase(Exception):
    pass