"""Транспортное средство «Торнадочайник-3000» (ТЗ-ТЧ3000-03-2026).

Реализация роли D (разработчик). Класс :class:`TornadoTeapot` моделирует
воздушное транспортное средство: взлёт, горизонтальное перемещение,
изменение высоты, поглощение облаков, торнадо-портал, посадку и подзарядку
аплодисментами.

Контракт (SPEC.md, ФТ-01 — ФТ-16):

* успешные команды изменения состояния возвращают ``None`` и не имеют
  других возвращаемых значений;
* при любом отказе состояние объекта не изменяется (Н-01);
* порядок проверок фиксирован: корректность аргументов (``ValueError``),
  допустимость состояния (:class:`InvalidStateError`), достаточность
  ресурсов (:class:`InsufficientResourcesError`) — ФТ-15;
* поведение детерминировано: никаких случайных чисел и внешних сервисов
  (ФТ-16).
"""

from __future__ import annotations

from tornado_errors import InsufficientResourcesError, InvalidStateError

# --- Границы аргументов команд (ФТ-05, ФТ-06, ФТ-07, ФТ-09, ФТ-11) -------
_MOVE_LIMIT = 20
_PORTAL_LIMIT = 100
_METERS_MIN, _METERS_MAX = 1, 30
_APPLAUSE_MIN, _APPLAUSE_MAX = 1, 10

# --- Константы модели состояния (ФТ-01, ФТ-04 — ФТ-11) -------------------
_INITIAL_ENERGY = 60
_MAX_ALTITUDE = 100
_MIN_FLIGHT_ALTITUDE = 10
_CLOUD_ALTITUDE = 20
_PORTAL_ALTITUDE = 30
_MAX_CLOUDS = 3
_MAX_ENERGY = 100
_TAKE_OFF_COST = 10
_TAKE_OFF_ALTITUDE = 10
_CLOUD_ENERGY = 15
_PORTAL_COST = 25
_PORTAL_CLOUDS = 2
_APPLAUSE_ENERGY = 5


def _require_int(value: object, name: str) -> None:
    """Проверяет, что аргумент имеет точный тип ``int`` (ФТ-14).

    ``bool`` запрещён явно, хотя и наследуется от ``int``: тесты (ДТ-01)
    требуют ``ValueError`` для ``True``/``False``. Подклассы ``int`` также
    отклоняются, так как контракт требует точный тип.
    """
    if type(value) is not int:
        raise ValueError(
            "Аргумент %s должен быть целым числом int, получен %s"
            % (name, type(value).__name__)
        )


def _require_range(value: int, name: str, low: int, high: int) -> None:
    """Проверяет, что целочисленный аргумент лежит в диапазоне (ФТ-14)."""
    if not low <= value <= high:
        raise ValueError(
            "Аргумент %s должен быть в диапазоне %d..%d, получен %d"
            % (name, low, high, value)
        )


def _require_vector(dx: object, dy: object, limit: int, name: str) -> None:
    """Проверяет вектор смещения: типы, диапазон и ненулевой вектор.

    Применяется к ``move`` (лимит 20) и ``tornado_portal`` (лимит 100).
    Нулевой вектор запрещён для обеих команд (ФТ-05, ФТ-09) и даёт
    ``ValueError`` в силу ФТ-14.
    """
    _require_int(dx, "dx")
    _require_int(dy, "dy")
    _require_range(dx, "dx", -limit, limit)
    _require_range(dy, "dy", -limit, limit)
    if dx == 0 and dy == 0:
        raise ValueError("Вектор %s не может быть нулевым" % name)


class TornadoTeapot:
    """Летающий чайник на воздушных потоках (стихия «Воздух»).

    Вместо двигателя использует воздушные потоки, поглощает облака
    для пополнения энергии и перемещается через торнадо-портал.
    Все правила детерминированы и описаны в SPEC.md.

    Состояние хранит координаты ``x`` и ``y`` (без границ мира, ФТ-02),
    высоту ``altitude`` (0..100), энергию ``energy`` (0..100) и текущий
    запас облаков ``clouds`` (0..3). Признак полёта ``is_airborne``
    выводится как ``altitude > 0`` (ФТ-01).
    """

    def __init__(self) -> None:
        """Создаёт чайник в исходном состоянии (ФТ-01)."""
        self._x = 0
        self._y = 0
        self._altitude = 0
        self._energy = _INITIAL_ENERGY
        self._clouds = 0

    # --- Вспомогательные методы -----------------------------------------

    @property
    def _is_airborne(self) -> bool:
        """Признак полёта: инвариант ``altitude > 0`` (ФТ-01)."""
        return self._altitude > 0

    def _spend_energy(self, amount: int) -> None:
        """Списывает энергию. Вызывается только после успешной проверки."""
        self._energy -= amount

    def _charge_energy(self, amount: int) -> None:
        """Пополняет энергию с потолком 100 (ФТ-08, ФТ-11)."""
        self._energy = min(_MAX_ENERGY, self._energy + amount)

    # --- Команды (ФТ-04 — ФТ-12) ----------------------------------------

    def take_off(self) -> None:
        """Взлёт с земли (ФТ-04): ``altitude = 10``, расход энергии 10."""
        if self._is_airborne:
            raise InvalidStateError("Взлёт возможен только с земли")
        if self._energy < _TAKE_OFF_COST:
            raise InsufficientResourcesError(
                "Для взлёта нужно не менее %d энергии" % _TAKE_OFF_COST
            )
        self._altitude = _TAKE_OFF_ALTITUDE
        self._spend_energy(_TAKE_OFF_COST)

    def move(self, dx: int, dy: int) -> None:
        """Горизонтальное перемещение в полёте (ФТ-05).

        Аргументы: целые числа от -20 до 20, не оба нуля. Расход энергии
        равен ``|dx| + |dy|``. Высота не меняется.
        """
        _require_vector(dx, dy, _MOVE_LIMIT, "перемещения")
        if not self._is_airborne:
            raise InvalidStateError("Перемещение возможно только в полёте")
        cost = abs(dx) + abs(dy)
        if self._energy < cost:
            raise InsufficientResourcesError(
                "Для перемещения нужно %d энергии, есть %d" % (cost, self._energy)
            )
        self._x += dx
        self._y += dy
        self._spend_energy(cost)

    def ascend(self, meters: int) -> None:
        """Подъём в полёте (ФТ-06): аргумент 1..30, потолок высоты 100.

        Расход энергии — округлённое вверх ``meters / 5``.
        """
        _require_int(meters, "meters")
        _require_range(meters, "meters", _METERS_MIN, _METERS_MAX)
        if not self._is_airborne:
            raise InvalidStateError("Подъём возможен только в полёте")
        new_altitude = self._altitude + meters
        if new_altitude > _MAX_ALTITUDE:
            raise InvalidStateError(
                "Высота %d превышает потолок %d" % (new_altitude, _MAX_ALTITUDE)
            )
        cost = -(-meters // 5)  # округление вверх без дробей
        if self._energy < cost:
            raise InsufficientResourcesError(
                "Для подъёма нужно %d энергии, есть %d" % (cost, self._energy)
            )
        self._altitude = new_altitude
        self._spend_energy(cost)

    def descend(self, meters: int) -> None:
        """Снижение в полёте (ФТ-07): аргумент 1..30, минимум высоты 10.

        Снижение бесплатно; на землю переходит только ``land()``.
        """
        _require_int(meters, "meters")
        _require_range(meters, "meters", _METERS_MIN, _METERS_MAX)
        if not self._is_airborne:
            raise InvalidStateError("Снижение возможно только в полёте")
        new_altitude = self._altitude - meters
        if new_altitude < _MIN_FLIGHT_ALTITUDE:
            raise InvalidStateError(
                "Высота %d ниже минимума полёта %d"
                % (new_altitude, _MIN_FLIGHT_ALTITUDE)
            )
        self._altitude = new_altitude

    def eat_cloud(self) -> None:
        """Поглощение облака в полёте (ФТ-08): ``altitude >= 20``, ``clouds < 3``.

        Дает ``clouds += 1`` и ``energy +15``, но не выше 100.
        """
        if not self._is_airborne:
            raise InvalidStateError("Облака поглощаются только в полёте")
        if self._altitude < _CLOUD_ALTITUDE:
            raise InvalidStateError(
                "Облака поглощаются не ниже высоты %d" % _CLOUD_ALTITUDE
            )
        if self._clouds >= _MAX_CLOUDS:
            raise InvalidStateError(
                "Запас облаков полон: %d из %d" % (self._clouds, _MAX_CLOUDS)
            )
        self._clouds += 1
        self._charge_energy(_CLOUD_ENERGY)

    def tornado_portal(self, dx: int, dy: int) -> None:
        """Мгновенное перемещение через портал (ФТ-09).

        Аргументы: целые числа от -100 до 100, не оба нуля. Условия:
        в полёте, ``altitude >= 30``, ``clouds >= 2``, ``energy >= 25``.
        Любая нехватка ресурсов даёт один ``InsufficientResourcesError``.
        """
        _require_vector(dx, dy, _PORTAL_LIMIT, "портала")
        if not self._is_airborne:
            raise InvalidStateError("Портал доступен только в полёте")
        if self._altitude < _PORTAL_ALTITUDE:
            raise InvalidStateError(
                "Портал доступен не ниже высоты %d" % _PORTAL_ALTITUDE
            )
        if self._energy < _PORTAL_COST or self._clouds < _PORTAL_CLOUDS:
            raise InsufficientResourcesError(
                "Для портала нужно не менее %d энергии и %d облаков"
                % (_PORTAL_COST, _PORTAL_CLOUDS)
            )
        self._x += dx
        self._y += dy
        self._spend_energy(_PORTAL_COST)
        self._clouds -= _PORTAL_CLOUDS

    def land(self) -> None:
        """Посадка из любого состояния полёта (ФТ-10).

        Обнуляет высоту и запас облаков; координаты и энергия сохраняются.
        """
        if not self._is_airborne:
            raise InvalidStateError("Посадка возможна только из полёта")
        self._altitude = 0
        self._clouds = 0

    def applause(self, count: int) -> None:
        """Подзарядка аплодисментами на земле (ФТ-11): аргумент 1..10.

        Дает ``energy + 5 * count``, но не выше 100.
        """
        _require_int(count, "count")
        _require_range(count, "count", _APPLAUSE_MIN, _APPLAUSE_MAX)
        if self._is_airborne:
            raise InvalidStateError("Аплодисменты принимаются только на земле")
        self._charge_energy(_APPLAUSE_ENERGY * count)

    def get_state(self) -> dict[str, int | bool]:
        """Возвращает новый независимый снимок состояния (ФТ-12).

        Каждый вызов создаёт отдельный словарь: изменение снимка не влияет
        на объект и на ранее выданные снимки.
        """
        return {
            "x": self._x,
            "y": self._y,
            "altitude": self._altitude,
            "energy": self._energy,
            "clouds": self._clouds,
            "is_airborne": self._is_airborne,
        }
