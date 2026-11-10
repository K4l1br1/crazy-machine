"""Доменные исключения симулятора «Торнадочайник-3000»."""


class TornadoTeapotError(Exception):
    """Базовый тип отказов команд симулятора."""


class InvalidStateError(TornadoTeapotError):
    """Команда недопустима при текущем состоянии транспорта."""


class InsufficientResourcesError(TornadoTeapotError):
    """Для команды недостаточно энергии или запаса облаков."""
