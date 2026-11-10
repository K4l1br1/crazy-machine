"""Граничные дополнительные тест-кейсы ДТ-01---ДТ-11 (см. TEST_PLAN.md).

Все состояния подготавливаются только публичными командами ТЗ:
take_off(), move(dx, dy), ascend(meters), descend(meters), eat_cloud(),
tornado_portal(dx, dy), land(), applause(count). Внутренние поля и атрибуты
объекта не читаются и не изменяются. Ожидаемые состояния сравниваются
полными словарями get_state() с точными типами скалярных значений.
Ошибки состояния и ресурсов проверяются доменными типами из tornado_errors.
"""

from tests.helpers import ContractCase, INITIAL_STATE
from tornado_errors import InsufficientResourcesError, InvalidStateError


def state_of(x, y, altitude, energy, clouds, is_airborne):
    """Полный ожидаемый снимок get_state()."""
    return {
        "x": x,
        "y": y,
        "altitude": altitude,
        "energy": energy,
        "clouds": clouds,
        "is_airborne": is_airborne,
    }


def shift(axis, sign, distance):
    """Вектор перемещения вдоль оси ``axis`` с учётом знака."""
    if axis == "x":
        return (sign * distance, 0)
    return (0, sign * distance)


BAD_NUMERIC_VALUES = (
    ("bool True", True),
    ("bool False", False),
    ("float 1.0", 1.0),
    ("float 20.5", 20.5),
    ("str '5'", "5"),
    ("str ''", ""),
    ("None", None),
    ("list [5]", [5]),
    ("list []", []),
    ("complex (5+0j)", complex(5, 0)),
    ("float inf", float("inf")),
    ("float -inf", float("-inf")),
    ("float nan", float("nan")),
)


class TestBoundaries(ContractCase):
    """ДТ-01---ДТ-11: типы, диапазоны, приоритет ошибок, ресурсы и инварианты."""

    def _portal_ready(self, teapot):
        """Подготовка портала: (0, 0), altitude=30, clouds=2, energy=76."""
        self.command(teapot, "take_off")
        self.command(teapot, "ascend", 20)
        self.command(teapot, "eat_cloud")
        self.command(teapot, "eat_cloud")

    # ------------------------------------------------------------------
    # ДТ-01. Числовые типы аргументов
    # ------------------------------------------------------------------
    def test_dt01_numeric_argument_types(self):
        for label, value in BAD_NUMERIC_VALUES:
            with self.subTest(method="move", argument="dx", value=label,
                              condition="airborne altitude=10 energy=50"):
                teapot = self.make()
                self.command(teapot, "take_off")
                self.reject(teapot, ValueError, "move", value, 1)

            with self.subTest(method="move", argument="dy", value=label,
                              condition="airborne altitude=10 energy=50"):
                teapot = self.make()
                self.command(teapot, "take_off")
                self.reject(teapot, ValueError, "move", 1, value)

            with self.subTest(method="tornado_portal", argument="dx", value=label,
                              condition="altitude=30 clouds=2 energy=76"):
                teapot = self.make()
                self._portal_ready(teapot)
                self.reject(teapot, ValueError, "tornado_portal", value, 1)

            with self.subTest(method="tornado_portal", argument="dy", value=label,
                              condition="altitude=30 clouds=2 energy=76"):
                teapot = self.make()
                self._portal_ready(teapot)
                self.reject(teapot, ValueError, "tornado_portal", 1, value)

            with self.subTest(method="ascend", argument="meters", value=label,
                              condition="airborne altitude=10 energy=50"):
                teapot = self.make()
                self.command(teapot, "take_off")
                self.reject(teapot, ValueError, "ascend", value)

            with self.subTest(method="descend", argument="meters", value=label,
                              condition="airborne altitude=10 energy=50"):
                teapot = self.make()
                self.command(teapot, "take_off")
                self.reject(teapot, ValueError, "descend", value)

            with self.subTest(method="applause", argument="count", value=label,
                              condition="ground altitude=0 energy=60"):
                teapot = self.make()
                self.reject(teapot, ValueError, "applause", value)

    # ------------------------------------------------------------------
    # ДТ-02. Недопустимые диапазоны и нулевые векторы
    # ------------------------------------------------------------------
    def test_dt02_out_of_range_and_zero_vectors(self):
        for dx, dy in ((21, 0), (0, 21), (-21, 0), (0, -21), (21, 21), (-21, 21)):
            with self.subTest(method="move", argument="dx, dy", value=(dx, dy),
                              condition="airborne altitude=10 energy=50"):
                teapot = self.make()
                self.command(teapot, "take_off")
                self.reject(teapot, ValueError, "move", dx, dy)

        with self.subTest(method="move", argument="dx, dy", value=(0, 0),
                          condition="airborne altitude=10 energy=50"):
            teapot = self.make()
            self.command(teapot, "take_off")
            self.reject(teapot, ValueError, "move", 0, 0)

        for dx, dy in ((101, 0), (0, 101), (-101, 0), (0, -101), (101, 101), (-101, 101)):
            with self.subTest(method="tornado_portal", argument="dx, dy",
                              value=(dx, dy),
                              condition="altitude=30 clouds=2 energy=76"):
                teapot = self.make()
                self._portal_ready(teapot)
                self.reject(teapot, ValueError, "tornado_portal", dx, dy)

        with self.subTest(method="tornado_portal", argument="dx, dy", value=(0, 0),
                          condition="altitude=30 clouds=2 energy=76"):
            teapot = self.make()
            self._portal_ready(teapot)
            self.reject(teapot, ValueError, "tornado_portal", 0, 0)

        for meters in (0, 31, -1, -30):
            with self.subTest(method="ascend", argument="meters", value=meters,
                              condition="airborne altitude=10 energy=50"):
                teapot = self.make()
                self.command(teapot, "take_off")
                self.reject(teapot, ValueError, "ascend", meters)

        for meters in (0, 31, -1):
            with self.subTest(method="descend", argument="meters", value=meters,
                              condition="airborne altitude=10 energy=50"):
                teapot = self.make()
                self.command(teapot, "take_off")
                self.reject(teapot, ValueError, "descend", meters)

        for count in (0, 11, -1, 100):
            with self.subTest(method="applause", argument="count", value=count,
                              condition="ground altitude=0 energy=60"):
                teapot = self.make()
                self.reject(teapot, ValueError, "applause", count)

    # ------------------------------------------------------------------
    # ДТ-03. Допустимые границы и свободные координаты
    # ------------------------------------------------------------------
    def test_dt03_valid_boundaries_and_free_coordinates(self):
        for dx, dy in ((20, 0), (0, 20), (-20, 0), (0, -20),
                       (20, 20), (-20, -20), (20, -20), (-20, 20)):
            with self.subTest(method="move", argument="dx, dy", value=(dx, dy),
                              condition="airborne altitude=10 energy=50"):
                teapot = self.make()
                self.command(teapot, "take_off")
                self.command(teapot, "move", dx, dy)
                self.assert_state(teapot, state_of(
                    dx, dy, 10, 50 - abs(dx) - abs(dy), 0, True))

        for dx, dy in ((100, 0), (0, 100), (-100, 0), (0, -100),
                       (100, -100), (-100, 100)):
            with self.subTest(method="tornado_portal", argument="dx, dy",
                              value=(dx, dy),
                              condition="altitude=30 clouds=2 energy=76"):
                teapot = self.make()
                self._portal_ready(teapot)
                self.command(teapot, "tornado_portal", dx, dy)
                self.assert_state(teapot, state_of(dx, dy, 30, 51, 0, True))

        with self.subTest(method="applause", argument="count", value=1,
                          condition="ground altitude=0 energy=60"):
            teapot = self.make()
            self.command(teapot, "applause", 1)
            self.assert_state(teapot, state_of(0, 0, 0, 65, 0, False))

        with self.subTest(method="applause", argument="count", value=9,
                          condition="ground altitude=0 energy=60"):
            teapot = self.make()
            self.command(teapot, "applause", 9)
            self.assert_state(teapot, state_of(0, 0, 0, 100, 0, False))

        with self.subTest(method="applause", argument="count", value=10,
                          condition="ground altitude=0 energy=10"):
            teapot = self.make()
            self.command(teapot, "take_off")
            self.command(teapot, "move", 20, 20)
            self.command(teapot, "land")
            self.command(teapot, "applause", 10)
            self.assert_state(teapot, state_of(20, 20, 0, 60, 0, False))

        with self.subTest(method="ascend", argument="meters", value=1,
                          condition="airborne altitude=10 energy=50"):
            teapot = self.make()
            self.command(teapot, "take_off")
            self.command(teapot, "ascend", 1)
            self.assert_state(teapot, state_of(0, 0, 11, 49, 0, True))

        with self.subTest(method="ascend", argument="meters", value=5,
                          condition="airborne altitude=10 energy=50 "
                                    "(lower rounding step ceil(5/5)=1)"):
            teapot = self.make()
            self.command(teapot, "take_off")
            self.command(teapot, "ascend", 5)
            self.assert_state(teapot, state_of(0, 0, 15, 49, 0, True))

        with self.subTest(method="ascend", argument="meters", value=6,
                          condition="airborne altitude=10 energy=50 "
                                    "(lower rounding step ceil(6/5)=2)"):
            teapot = self.make()
            self.command(teapot, "take_off")
            self.command(teapot, "ascend", 6)
            self.assert_state(teapot, state_of(0, 0, 16, 48, 0, True))

        with self.subTest(method="ascend", argument="meters", value=30,
                          condition="airborne altitude=10 energy=50"):
            teapot = self.make()
            self.command(teapot, "take_off")
            self.command(teapot, "ascend", 30)
            self.assert_state(teapot, state_of(0, 0, 40, 44, 0, True))

        with self.subTest(method="ascend", argument="meters", value="29 then 1",
                          condition="airborne altitude=70 energy=38 (99 -> 100)"):
            teapot = self.make()
            self.command(teapot, "take_off")
            self.command(teapot, "ascend", 30)
            self.command(teapot, "ascend", 30)
            self.command(teapot, "ascend", 29)
            self.command(teapot, "ascend", 1)
            self.assert_state(teapot, state_of(0, 0, 100, 31, 0, True))

        with self.subTest(method="descend", argument="meters", value=1,
                          condition="airborne altitude=11 energy=49 (floor 10)"):
            teapot = self.make()
            self.command(teapot, "take_off")
            self.command(teapot, "ascend", 1)
            self.command(teapot, "descend", 1)
            self.assert_state(teapot, state_of(0, 0, 10, 49, 0, True))

        with self.subTest(method="descend", argument="meters", value=30,
                          condition="airborne altitude=40 energy=44"):
            teapot = self.make()
            self.command(teapot, "take_off")
            self.command(teapot, "ascend", 30)
            self.command(teapot, "descend", 30)
            self.assert_state(teapot, state_of(0, 0, 10, 44, 0, True))

        for axis, sign in (("x", 1), ("x", -1), ("y", 1), ("y", -1)):
            target = (110 * sign, 0) if axis == "x" else (0, 110 * sign)
            with self.subTest(method="move", argument="total %s" % axis,
                              value=target,
                              condition="three flight cycles with applause "
                                        "refills"):
                teapot = self.make()
                for method, args in (
                    ("take_off", ()),
                    ("move", shift(axis, sign, 20)),
                    ("move", shift(axis, sign, 20)),
                    ("land", ()),
                    ("applause", (10,)),
                    ("take_off", ()),
                    ("move", shift(axis, sign, 20)),
                    ("move", shift(axis, sign, 20)),
                    ("land", ()),
                    ("applause", (10,)),
                    ("take_off", ()),
                    ("move", shift(axis, sign, 20)),
                    ("move", shift(axis, sign, 10)),
                    ("land", ()),
                ):
                    self.command(teapot, method, *args)
                self.assert_state(teapot, state_of(
                    target[0], target[1], 0, 20, 0, False))

    # ------------------------------------------------------------------
    # ДТ-04. Приоритет ValueError, затем состояния, затем ресурсов
    # ------------------------------------------------------------------
    def test_dt04_validation_priority(self):
        cases = (
            ("ground altitude=0", "move", (21, 0)),
            ("ground altitude=0", "move", (0, 0)),
            ("ground altitude=0", "ascend", (0,)),
            ("ground altitude=0", "descend", (31,)),
            ("ground altitude=0", "tornado_portal", (101, 0)),
        )
        for condition, method, args in cases:
            with self.subTest(method=method, args=args, condition=condition):
                teapot = self.make()
                self.reject(teapot, ValueError, method, *args)

        with self.subTest(method="applause", argument="count", value=11,
                          condition="airborne altitude=10 energy=50"):
            teapot = self.make()
            self.command(teapot, "take_off")
            self.reject(teapot, ValueError, "applause", 11)

        with self.subTest(method="ascend", argument="meters", value=31,
                          condition="airborne altitude=100 (height limit)"):
            teapot = self.make()
            self.command(teapot, "take_off")
            for _ in range(3):
                self.command(teapot, "ascend", 30)
            self.reject(teapot, ValueError, "ascend", 31)

        with self.subTest(method="descend", argument="meters", value=31,
                          condition="airborne altitude=10 (floor limit)"):
            teapot = self.make()
            self.command(teapot, "take_off")
            self.reject(teapot, ValueError, "descend", 31)

        with self.subTest(method="move", argument="dx", value=21,
                          condition="airborne altitude=10 energy=10 (shortfall)"):
            teapot = self.make()
            self.command(teapot, "take_off")
            self.command(teapot, "move", 20, 20)
            self.reject(teapot, ValueError, "move", 21, 0)

        with self.subTest(method="move", argument="dx", value=True,
                          condition="airborne altitude=10 energy=10 "
                                    "(conditional cost 1+20=21 > 10)"):
            teapot = self.make()
            self.command(teapot, "take_off")
            self.command(teapot, "move", 20, 20)
            self.reject(teapot, ValueError, "move", True, 20)

        with self.subTest(method="tornado_portal", argument="dx, dy",
                          value=(101, 0),
                          condition="airborne altitude=10 clouds=0 (not eligible)"):
            teapot = self.make()
            self.command(teapot, "take_off")
            self.reject(teapot, ValueError, "tornado_portal", 101, 0)

        with self.subTest(method="tornado_portal", argument="dx, dy",
                          value=(0, 0),
                          condition="altitude=30 clouds=2 energy=24 (shortfall)"):
            teapot = self.make()
            self._portal_ready(teapot)
            self.command(teapot, "move", 20, 20)
            self.command(teapot, "move", 6, 6)
            self.reject(teapot, ValueError, "tornado_portal", 0, 0)

        with self.subTest(method="tornado_portal", argument="dx, dy",
                          value=(1, 1),
                          condition="altitude=29 energy=6 clouds=0 "
                                    "(state before resources)"):
            teapot = self.make()
            self.command(teapot, "take_off")
            self.command(teapot, "ascend", 19)
            self.command(teapot, "move", 20, 20)
            self.assert_state(teapot, state_of(20, 20, 29, 6, 0, True))
            self.reject(teapot, InvalidStateError, "tornado_portal", 1, 1)

        with self.subTest(method="ascend", argument="meters", value=1,
                          condition="altitude=100 energy=0 "
                                    "(state before resources)"):
            teapot = self.make()
            self.command(teapot, "take_off")
            for _ in range(3):
                self.command(teapot, "ascend", 30)
            self.command(teapot, "move", 16, 16)
            self.assert_state(teapot, state_of(16, 16, 100, 0, 0, True))
            self.reject(teapot, InvalidStateError, "ascend", 1)

    # ------------------------------------------------------------------
    # ДТ-05. Запреты состояний и пороги высоты 19/20, 29/30
    # ------------------------------------------------------------------
    def test_dt05_state_restrictions_and_altitude_thresholds(self):
        for method, args in (
            ("move", (1, 0)),
            ("ascend", (1,)),
            ("descend", (1,)),
            ("eat_cloud", ()),
            ("tornado_portal", (1, 1)),
            ("land", ()),
        ):
            with self.subTest(method=method, args=args,
                              condition="ground altitude=0 energy=60"):
                teapot = self.make()
                self.reject(teapot, InvalidStateError, method, *args)

        with self.subTest(method="land", args=(), condition="ground after landing"):
            teapot = self.make()
            self.command(teapot, "take_off")
            self.command(teapot, "land")
            self.reject(teapot, InvalidStateError, "land")
            self.assert_state(teapot, state_of(0, 0, 0, 50, 0, False))

        with self.subTest(method="applause", argument="count", value=1,
                          condition="airborne altitude=10"):
            teapot = self.make()
            self.command(teapot, "take_off")
            self.reject(teapot, InvalidStateError, "applause", 1)
            self.assert_state(teapot, state_of(0, 0, 10, 50, 0, True))

        with self.subTest(method="eat_cloud", argument="-", value="altitude=19",
                          condition="airborne below threshold"):
            teapot = self.make()
            self.command(teapot, "take_off")
            self.command(teapot, "ascend", 9)
            self.reject(teapot, InvalidStateError, "eat_cloud")
            self.assert_state(teapot, state_of(0, 0, 19, 48, 0, True))

        with self.subTest(method="eat_cloud", argument="-", value="altitude=20",
                          condition="airborne at threshold"):
            teapot = self.make()
            self.command(teapot, "take_off")
            self.command(teapot, "ascend", 10)
            self.command(teapot, "eat_cloud")
            self.assert_state(teapot, state_of(0, 0, 20, 63, 1, True))

        with self.subTest(method="tornado_portal", argument="clouds",
                          value="1 (below threshold 2)",
                          condition="altitude=30 energy=61 clouds=1"):
            teapot = self.make()
            self.command(teapot, "take_off")
            self.command(teapot, "ascend", 20)
            self.command(teapot, "eat_cloud")
            self.assert_state(teapot, state_of(0, 0, 30, 61, 1, True))
            self.reject(teapot, InsufficientResourcesError,
                        "tornado_portal", 1, 1)
            self.assert_state(teapot, state_of(0, 0, 30, 61, 1, True))

        with self.subTest(method="tornado_portal", argument="dx, dy",
                          value=(1, 1), condition="altitude=29 clouds=2 energy=76"):
            teapot = self.make()
            self.command(teapot, "take_off")
            self.command(teapot, "ascend", 19)
            self.command(teapot, "eat_cloud")
            self.command(teapot, "eat_cloud")
            self.reject(teapot, InvalidStateError, "tornado_portal", 1, 1)
            self.assert_state(teapot, state_of(0, 0, 29, 76, 2, True))

        with self.subTest(method="tornado_portal", argument="dx, dy",
                          value=(1, 1), condition="altitude=30 clouds=2 energy=76"):
            teapot = self.make()
            self.command(teapot, "take_off")
            self.command(teapot, "ascend", 20)
            self.command(teapot, "eat_cloud")
            self.command(teapot, "eat_cloud")
            self.command(teapot, "tornado_portal", 1, 1)
            self.assert_state(teapot, state_of(1, 1, 30, 51, 0, True))

    # ------------------------------------------------------------------
    # ДТ-06. Точный бюджет и недостача на 1
    # ------------------------------------------------------------------
    def test_dt06_exact_budget_and_shortfall_by_one(self):
        with self.subTest(method="take_off", argument="energy",
                          value="10 (exact)"):
            teapot = self.make()
            self.command(teapot, "take_off")
            self.command(teapot, "move", 20, 20)
            self.command(teapot, "land")
            self.command(teapot, "take_off")
            self.assert_state(teapot, state_of(20, 20, 10, 0, 0, True))

        with self.subTest(method="take_off", argument="energy",
                          value="9 (short by 1)"):
            teapot = self.make()
            self.command(teapot, "take_off")
            self.command(teapot, "move", 20, 20)
            self.command(teapot, "move", 1, 0)
            self.command(teapot, "land")
            self.reject(teapot, InsufficientResourcesError, "take_off")
            self.assert_state(teapot, state_of(21, 20, 0, 9, 0, False))

        with self.subTest(method="move", argument="dx, dy", value=(20, 20),
                          condition="energy=40 (exact cost 40)"):
            teapot = self.make()
            self.command(teapot, "take_off")
            self.command(teapot, "move", 5, 5)
            self.command(teapot, "move", 20, 20)
            self.assert_state(teapot, state_of(25, 25, 10, 0, 0, True))

        with self.subTest(method="move", argument="dx, dy", value=(20, 20),
                          condition="energy=39 (short by 1)"):
            teapot = self.make()
            self.command(teapot, "take_off")
            self.command(teapot, "move", 5, 5)
            self.command(teapot, "move", 1, 0)
            self.reject(teapot, InsufficientResourcesError, "move", 20, 20)
            self.assert_state(teapot, state_of(6, 5, 10, 39, 0, True))

        with self.subTest(method="ascend", argument="meters", value=11,
                          condition="energy=3 (exact cost ceil(11/5)=3)"):
            teapot = self.make()
            self.command(teapot, "take_off")
            self.command(teapot, "move", 20, 20)
            self.command(teapot, "move", 4, 3)
            self.command(teapot, "ascend", 11)
            self.assert_state(teapot, state_of(24, 23, 21, 0, 0, True))

        with self.subTest(method="ascend", argument="meters", value=11,
                          condition="energy=2 (short by 1)"):
            teapot = self.make()
            self.command(teapot, "take_off")
            self.command(teapot, "move", 20, 20)
            self.command(teapot, "move", 4, 4)
            self.reject(teapot, InsufficientResourcesError, "ascend", 11)
            self.assert_state(teapot, state_of(24, 24, 10, 2, 0, True))

        with self.subTest(method="tornado_portal", argument="dx, dy",
                          value=(1, 1),
                          condition="altitude=30 clouds=2 energy=25 (exact)"):
            teapot = self.make()
            self._portal_ready(teapot)
            self.command(teapot, "move", 20, 20)
            self.command(teapot, "move", 6, 5)
            self.command(teapot, "tornado_portal", 1, 1)
            self.assert_state(teapot, state_of(27, 26, 30, 0, 0, True))

        with self.subTest(method="tornado_portal", argument="dx, dy",
                          value=(1, 1),
                          condition="altitude=30 clouds=2 energy=24 (short by 1)"):
            teapot = self.make()
            self._portal_ready(teapot)
            self.command(teapot, "move", 20, 20)
            self.command(teapot, "move", 6, 6)
            self.reject(teapot, InsufficientResourcesError,
                        "tornado_portal", 1, 1)
            self.assert_state(teapot, state_of(26, 26, 30, 24, 2, True))

    # ------------------------------------------------------------------
    # ДТ-07. Потолок энергии от облаков и аплодисментов
    # ------------------------------------------------------------------
    def test_dt07_energy_caps(self):
        with self.subTest(method="eat_cloud", argument="energy",
                          value="88 + 15 -> 100"):
            teapot = self.make()
            self.command(teapot, "applause", 10)
            self.command(teapot, "take_off")
            self.command(teapot, "ascend", 10)
            self.command(teapot, "eat_cloud")
            self.assert_state(teapot, state_of(0, 0, 20, 100, 1, True))
            self.command(teapot, "eat_cloud")
            self.assert_state(teapot, state_of(0, 0, 20, 100, 2, True))

        with self.subTest(method="applause", argument="count", value=10,
                          condition="energy=100 (already full)"):
            teapot = self.make()
            self.command(teapot, "applause", 10)
            self.command(teapot, "applause", 10)
            self.assert_state(teapot, state_of(0, 0, 0, 100, 0, False))

        with self.subTest(method="applause", argument="count", value=1,
                          condition="energy=95 then 100"):
            teapot = self.make()
            self.command(teapot, "applause", 7)
            self.assert_state(teapot, state_of(0, 0, 0, 95, 0, False))
            self.command(teapot, "applause", 1)
            self.assert_state(teapot, state_of(0, 0, 0, 100, 0, False))
            self.command(teapot, "applause", 1)
            self.assert_state(teapot, state_of(0, 0, 0, 100, 0, False))

    # ------------------------------------------------------------------
    # ДТ-08. Полет с нулевой энергией, бесплатное снижение, сброс облаков
    # ------------------------------------------------------------------
    def test_dt08_zero_energy_flight_and_cloud_reset(self):
        with self.subTest(method="descend/land", argument="energy",
                          value="0 (free of charge)"):
            teapot = self.make()
            self.command(teapot, "take_off")
            self.command(teapot, "ascend", 10)
            self.command(teapot, "eat_cloud")
            self.command(teapot, "move", 20, 20)
            self.command(teapot, "move", 11, 11)
            self.command(teapot, "move", 1, 0)
            self.assert_state(teapot, state_of(32, 31, 20, 0, 1, True))
            self.reject(teapot, InsufficientResourcesError, "move", 1, 0)
            self.command(teapot, "descend", 10)
            self.assert_state(teapot, state_of(32, 31, 10, 0, 1, True))
            self.reject(teapot, InvalidStateError, "descend", 1)
            self.command(teapot, "land")
            self.assert_state(teapot, state_of(32, 31, 0, 0, 0, False))

        with self.subTest(method="land/applause/take_off", argument="clouds",
                          value="1 -> 0, energy 0 -> 10"):
            teapot = self.make()
            self.command(teapot, "take_off")
            self.command(teapot, "ascend", 10)
            self.command(teapot, "eat_cloud")
            self.command(teapot, "move", 20, 20)
            self.command(teapot, "move", 11, 11)
            self.command(teapot, "move", 1, 0)
            self.assert_state(teapot, state_of(32, 31, 20, 0, 1, True))
            self.command(teapot, "land")
            self.assert_state(teapot, state_of(32, 31, 0, 0, 0, False))
            self.command(teapot, "applause", 2)
            self.assert_state(teapot, state_of(32, 31, 0, 10, 0, False))
            self.command(teapot, "take_off")
            self.assert_state(teapot, state_of(32, 31, 10, 0, 0, True))

    # ------------------------------------------------------------------
    # ДТ-09. Успешные команды возвращают None и принимают keyword-аргументы
    # ------------------------------------------------------------------
    def test_dt09_none_results_and_keyword_arguments(self):
        teapot = self.make()
        self.assert_state(teapot, dict(INITIAL_STATE))

        steps = (
            ("take_off()", "take_off", {}, state_of(0, 0, 10, 50, 0, True)),
            ("move(dx=-2, dy=5)", "move", {"dx": -2, "dy": 5},
             state_of(-2, 5, 10, 43, 0, True)),
            ("ascend(meters=10)", "ascend", {"meters": 10},
             state_of(-2, 5, 20, 41, 0, True)),
            ("eat_cloud()", "eat_cloud", {}, state_of(-2, 5, 20, 56, 1, True)),
            ("descend(meters=5)", "descend", {"meters": 5},
             state_of(-2, 5, 15, 56, 1, True)),
            ("land()", "land", {}, state_of(-2, 5, 0, 56, 0, False)),
            ("applause(count=2)", "applause", {"count": 2},
             state_of(-2, 5, 0, 66, 0, False)),
            ("take_off()", "take_off", {}, state_of(-2, 5, 10, 56, 0, True)),
            ("ascend(meters=20)", "ascend", {"meters": 20},
             state_of(-2, 5, 30, 52, 0, True)),
            ("eat_cloud()", "eat_cloud", {}, state_of(-2, 5, 30, 67, 1, True)),
            ("eat_cloud()", "eat_cloud", {}, state_of(-2, 5, 30, 82, 2, True)),
            ("tornado_portal(dx=-10, dy=10)", "tornado_portal",
             {"dx": -10, "dy": 10}, state_of(-12, 15, 30, 57, 0, True)),
        )

        for label, method, kwargs, expected in steps:
            with self.subTest(method=method, value=label, condition="sequence"):
                self.command(teapot, method, **kwargs)
                self.assert_state(teapot, expected)

        with self.subTest(method="get_state", value="dict", condition="final"):
            state = teapot.get_state()
            self.assertIsInstance(state, dict)
            self.assertEqual(state, state_of(-12, 15, 30, 57, 0, True))

    # ------------------------------------------------------------------
    # ДТ-10. Детерминизм и инварианты на явной конечной последовательности
    # ------------------------------------------------------------------
    def test_dt10_deterministic_sequence_and_invariants(self):
        scenario = (
            ("command", None, "take_off", (),
             state_of(0, 0, 10, 50, 0, True)),
            ("command", None, "move", (7, -3),
             state_of(7, -3, 10, 40, 0, True)),
            ("command", None, "ascend", (9,),
             state_of(7, -3, 19, 38, 0, True)),
            ("reject", InvalidStateError, "eat_cloud", (),
             state_of(7, -3, 19, 38, 0, True)),
            ("command", None, "ascend", (1,),
             state_of(7, -3, 20, 37, 0, True)),
            ("command", None, "eat_cloud", (),
             state_of(7, -3, 20, 52, 1, True)),
            ("command", None, "eat_cloud", (),
             state_of(7, -3, 20, 67, 2, True)),
            ("reject", InvalidStateError, "tornado_portal", (-15, 20),
             state_of(7, -3, 20, 67, 2, True)),
            ("command", None, "ascend", (10,),
             state_of(7, -3, 30, 65, 2, True)),
            ("command", None, "eat_cloud", (),
             state_of(7, -3, 30, 80, 3, True)),
            ("command", None, "tornado_portal", (-15, 20),
             state_of(-8, 17, 30, 55, 1, True)),
            ("command", None, "descend", (20,),
             state_of(-8, 17, 10, 55, 1, True)),
            ("command", None, "land", (),
             state_of(-8, 17, 0, 55, 0, False)),
            ("command", None, "applause", (3,),
             state_of(-8, 17, 0, 70, 0, False)),
            ("command", None, "take_off", (),
             state_of(-8, 17, 10, 60, 0, True)),
            ("command", None, "move", (-1, 1),
             state_of(-9, 18, 10, 58, 0, True)),
        )

        first = self.make()
        second = self.make()
        self.assert_state(first, dict(INITIAL_STATE))
        self.assert_state(second, dict(INITIAL_STATE))

        for index, (action, exc_type, method, args, expected) in enumerate(
                scenario, start=1):
            with self.subTest(step=index, method=method, args=args,
                              condition="two independent instances"):
                if action == "reject":
                    self.reject(first, exc_type, method, *args)
                    self.reject(second, exc_type, method, *args)
                else:
                    self.command(first, method, *args)
                    self.command(second, method, *args)

                self.assert_state(first, expected)
                self.assert_state(second, expected)

                state_first = first.get_state()
                state_second = second.get_state()
                self.assertEqual(state_first, state_second)
                self.assertIsNot(state_first, state_second)

                for state in (state_first, state_second):
                    self.assertGreaterEqual(state["altitude"], 0)
                    self.assertLessEqual(state["altitude"], 100)
                    self.assertGreaterEqual(state["energy"], 0)
                    self.assertLessEqual(state["energy"], 100)
                    self.assertGreaterEqual(state["clouds"], 0)
                    self.assertLessEqual(state["clouds"], 3)
                    self.assertIs(state["is_airborne"], state["altitude"] > 0)

        with self.subTest(step="final", method="get_state", value="equal states"):
            self.assertEqual(first.get_state(), second.get_state())

    # ------------------------------------------------------------------
    # ДТ-11. Пополнение текущего запаса облаков после портала
    # ------------------------------------------------------------------
    def test_dt11_clouds_replenish_after_portal(self):
        teapot = self.make()

        steps = (
            ("take_off", (), state_of(0, 0, 10, 50, 0, True)),
            ("ascend", (20,), state_of(0, 0, 30, 46, 0, True)),
            ("eat_cloud", (), state_of(0, 0, 30, 61, 1, True)),
            ("eat_cloud", (), state_of(0, 0, 30, 76, 2, True)),
            ("eat_cloud", (), state_of(0, 0, 30, 91, 3, True)),
            ("tornado_portal", (1, 1), state_of(1, 1, 30, 66, 1, True)),
            ("eat_cloud", (), state_of(1, 1, 30, 81, 2, True)),
            ("tornado_portal", (1, 1), state_of(2, 2, 30, 56, 0, True)),
            ("eat_cloud", (), state_of(2, 2, 30, 71, 1, True)),
            ("eat_cloud", (), state_of(2, 2, 30, 86, 2, True)),
            ("eat_cloud", (), state_of(2, 2, 30, 100, 3, True)),
        )

        for index, (method, args, expected) in enumerate(steps, start=1):
            with self.subTest(step=index, method=method, args=args,
                              condition="clouds replenish after portal"):
                self.command(teapot, method, *args)
                self.assert_state(teapot, expected)
