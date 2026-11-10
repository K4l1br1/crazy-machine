"""Приёмочные тесты ПТ-01–ПТ-22 (приложение А технического задания).

Каждый сценарий выполняется на новом экземпляре ``TornadoTeapot``.
Успешные команды обязаны возвращать ``None``; ошибочные команды
проверяются с полным сравнением словаря ``get_state()`` до и после вызова,
включая точные типы значений. Отказы состояния и ресурсов выражаются
доменными исключениями из ``tornado_errors``.
"""

import unittest

from tests.helpers import INITIAL_STATE, ContractCase
from tornado_errors import InsufficientResourcesError, InvalidStateError


class TestAcceptance(ContractCase):
    """Обязательные приёмочные сценарии приложения А."""

    def test_pt01_initialization(self):
        """ПТ-01. Начальная инициализация: get_state() возвращает исходные значения."""
        teapot = self.make()
        self.assert_state(teapot, INITIAL_STATE)

    def test_pt02_take_off(self):
        """ПТ-02. Взлёт: altitude=10, energy=50, is_airborne=True."""
        teapot = self.make()
        self.command(teapot, "take_off")
        self.assert_state(
            teapot,
            dict(INITIAL_STATE, altitude=10, energy=50, is_airborne=True),
        )

    def test_pt03_repeated_take_off(self):
        """ПТ-03. Повторный взлёт вызывает InvalidStateError без изменения состояния."""
        teapot = self.make()
        self.command(teapot, "take_off")
        self.assert_state(
            teapot,
            dict(INITIAL_STATE, altitude=10, energy=50, is_airborne=True),
        )
        self.reject(teapot, InvalidStateError, "take_off")
        self.assert_state(
            teapot,
            dict(INITIAL_STATE, altitude=10, energy=50, is_airborne=True),
        )

    def test_pt04_move(self):
        """ПТ-04. Перемещение: x=3, y=-4, energy=43, altitude=10."""
        teapot = self.make()
        self.command(teapot, "take_off")
        self.command(teapot, "move", dx=3, dy=-4)
        self.assert_state(
            teapot,
            dict(
                INITIAL_STATE,
                x=3,
                y=-4,
                altitude=10,
                energy=43,
                is_airborne=True,
            ),
        )

    def test_pt05_zero_vector(self):
        """ПТ-05. Нулевой вектор move(0, 0) вызывает ValueError."""
        teapot = self.make()
        self.command(teapot, "take_off")
        self.assert_state(
            teapot,
            dict(INITIAL_STATE, altitude=10, energy=50, is_airborne=True),
        )
        self.reject(teapot, ValueError, "move", dx=0, dy=0)
        self.assert_state(
            teapot,
            dict(INITIAL_STATE, altitude=10, energy=50, is_airborne=True),
        )

    def test_pt06_invalid_type(self):
        """ПТ-06. Аргумент bool вместо int вызывает ValueError."""
        teapot = self.make()
        self.command(teapot, "take_off")
        self.assert_state(
            teapot,
            dict(INITIAL_STATE, altitude=10, energy=50, is_airborne=True),
        )
        self.reject(teapot, ValueError, "move", dx=True, dy=1)
        self.assert_state(
            teapot,
            dict(INITIAL_STATE, altitude=10, energy=50, is_airborne=True),
        )

    def test_pt07_insufficient_energy(self):
        """ПТ-07. Второе перемещение при energy=10 вызывает InsufficientResourcesError."""
        teapot = self.make()
        self.command(teapot, "take_off")
        self.command(teapot, "move", dx=20, dy=20)
        self.assert_state(
            teapot,
            dict(
                INITIAL_STATE,
                x=20,
                y=20,
                altitude=10,
                energy=10,
                is_airborne=True,
            ),
        )
        self.reject(teapot, InsufficientResourcesError, "move", dx=10, dy=10)
        self.assert_state(
            teapot,
            dict(
                INITIAL_STATE,
                x=20,
                y=20,
                altitude=10,
                energy=10,
                is_airborne=True,
            ),
        )

    def test_pt08_ascend_rounding(self):
        """ПТ-08. ascend(11) поднимает на 21 м и тратит 3 единицы энергии."""
        teapot = self.make()
        self.command(teapot, "take_off")
        self.command(teapot, "ascend", meters=11)
        self.assert_state(
            teapot,
            dict(INITIAL_STATE, altitude=21, energy=47, is_airborne=True),
        )

    def test_pt09_altitude_limit(self):
        """ПТ-09. Подъём выше 100 м вызывает InvalidStateError без изменения состояния."""
        teapot = self.make()
        self.command(teapot, "take_off")
        for _ in range(3):
            self.command(teapot, "ascend", meters=30)
        self.assert_state(
            teapot,
            dict(INITIAL_STATE, altitude=100, energy=32, is_airborne=True),
        )
        self.reject(teapot, InvalidStateError, "ascend", meters=1)
        self.assert_state(
            teapot,
            dict(INITIAL_STATE, altitude=100, energy=32, is_airborne=True),
        )

    def test_pt10_descent_limit(self):
        """ПТ-10. Снижение ниже 10 м вызывает InvalidStateError без изменения состояния."""
        teapot = self.make()
        self.command(teapot, "take_off")
        self.command(teapot, "ascend", meters=10)
        self.command(teapot, "descend", meters=10)
        self.assert_state(
            teapot,
            dict(INITIAL_STATE, altitude=10, energy=48, is_airborne=True),
        )
        self.reject(teapot, InvalidStateError, "descend", meters=1)
        self.assert_state(
            teapot,
            dict(INITIAL_STATE, altitude=10, energy=48, is_airborne=True),
        )

    def test_pt11_eat_cloud(self):
        """ПТ-11. Поглощение облака: altitude=20, clouds=1, energy=63."""
        teapot = self.make()
        self.command(teapot, "take_off")
        self.command(teapot, "ascend", meters=10)
        self.command(teapot, "eat_cloud")
        self.assert_state(
            teapot,
            dict(
                INITIAL_STATE,
                altitude=20,
                energy=63,
                clouds=1,
                is_airborne=True,
            ),
        )

    def test_pt12_cloud_too_low(self):
        """ПТ-12. Поглощение облака на высоте 10 м вызывает InvalidStateError."""
        teapot = self.make()
        self.command(teapot, "take_off")
        self.assert_state(
            teapot,
            dict(INITIAL_STATE, altitude=10, energy=50, is_airborne=True),
        )
        self.reject(teapot, InvalidStateError, "eat_cloud")
        self.assert_state(
            teapot,
            dict(INITIAL_STATE, altitude=10, energy=50, is_airborne=True),
        )

    def test_pt13_cloud_limit(self):
        """ПТ-13. Четвёртое облако вызывает InvalidStateError без изменения состояния."""
        teapot = self.make()
        self.command(teapot, "take_off")
        self.command(teapot, "ascend", meters=10)
        for _ in range(3):
            self.command(teapot, "eat_cloud")
        self.assert_state(
            teapot,
            dict(
                INITIAL_STATE,
                altitude=20,
                energy=93,
                clouds=3,
                is_airborne=True,
            ),
        )
        self.reject(teapot, InvalidStateError, "eat_cloud")
        self.assert_state(
            teapot,
            dict(
                INITIAL_STATE,
                altitude=20,
                energy=93,
                clouds=3,
                is_airborne=True,
            ),
        )

    def test_pt14_tornado_portal(self):
        """ПТ-14. Портал: x=70, y=-40, altitude=30, energy=51, clouds=0."""
        teapot = self.make()
        self.command(teapot, "take_off")
        self.command(teapot, "ascend", meters=20)
        self.command(teapot, "eat_cloud")
        self.command(teapot, "eat_cloud")
        self.command(teapot, "tornado_portal", dx=70, dy=-40)
        self.assert_state(
            teapot,
            dict(
                INITIAL_STATE,
                x=70,
                y=-40,
                altitude=30,
                energy=51,
                clouds=0,
                is_airborne=True,
            ),
        )

    def test_pt15_portal_without_clouds(self):
        """ПТ-15. Портал без двух облаков вызывает InsufficientResourcesError."""
        teapot = self.make()
        self.command(teapot, "take_off")
        self.command(teapot, "ascend", meters=20)
        self.assert_state(
            teapot,
            dict(INITIAL_STATE, altitude=30, energy=46, is_airborne=True),
        )
        self.reject(teapot, InsufficientResourcesError, "tornado_portal", dx=1, dy=1)
        self.assert_state(
            teapot,
            dict(INITIAL_STATE, altitude=30, energy=46, is_airborne=True),
        )

    def test_pt16_land(self):
        """ПТ-16. Посадка: altitude=0, clouds=0, is_airborne=False."""
        teapot = self.make()
        self.command(teapot, "take_off")
        self.command(teapot, "ascend", meters=10)
        self.command(teapot, "eat_cloud")
        self.command(teapot, "land")
        self.assert_state(
            teapot,
            dict(INITIAL_STATE, altitude=0, energy=63, clouds=0),
        )

    def test_pt17_applause(self):
        """ПТ-17. applause(10) повышает energy до 100, но не выше."""
        teapot = self.make()
        self.command(teapot, "applause", count=10)
        self.assert_state(teapot, dict(INITIAL_STATE, energy=100))

    def test_pt18_applause_in_air(self):
        """ПТ-18. Аплодисменты в полёте вызывают InvalidStateError."""
        teapot = self.make()
        self.command(teapot, "take_off")
        self.assert_state(
            teapot,
            dict(INITIAL_STATE, altitude=10, energy=50, is_airborne=True),
        )
        self.reject(teapot, InvalidStateError, "applause", count=2)
        self.assert_state(
            teapot,
            dict(INITIAL_STATE, altitude=10, energy=50, is_airborne=True),
        )

    def test_pt19_take_off_without_energy(self):
        """ПТ-19. Взлёт при energy=0 на земле вызывает InsufficientResourcesError."""
        teapot = self.make()
        self.command(teapot, "take_off")
        self.command(teapot, "move", dx=20, dy=20)
        self.command(teapot, "move", dx=10, dy=0)
        self.command(teapot, "land")
        self.assert_state(
            teapot,
            dict(INITIAL_STATE, x=30, y=20, altitude=0, energy=0),
        )
        self.reject(teapot, InsufficientResourcesError, "take_off")
        self.assert_state(
            teapot,
            dict(INITIAL_STATE, x=30, y=20, altitude=0, energy=0),
        )

    def test_pt20_instance_independence(self):
        """ПТ-20. Изменение первого экземпляра не меняет второй."""
        first = self.make()
        second = self.make()
        self.command(first, "take_off")
        self.assert_state(
            first,
            dict(INITIAL_STATE, altitude=10, energy=50, is_airborne=True),
        )
        self.assert_state(second, INITIAL_STATE)

    def test_pt21_state_protection(self):
        """ПТ-21. Снимки get_state() независимы и не меняются после команд."""
        teapot = self.make()
        first = teapot.get_state()
        second = teapot.get_state()
        self.assertIsNot(first, second)
        self.assertEqual(first, INITIAL_STATE)
        self.assertEqual(second, INITIAL_STATE)
        first["energy"] = 0
        self.assert_state(teapot, INITIAL_STATE)
        self.assertEqual(second, INITIAL_STATE)
        self.command(teapot, "take_off")
        self.assertEqual(first, dict(INITIAL_STATE, energy=0))
        self.assertEqual(second, INITIAL_STATE)
        for snapshot in (first, second):
            for key, value in snapshot.items():
                expected_type = bool if key == "is_airborne" else int
                self.assertIs(
                    type(value),
                    expected_type,
                    "Значение %s в снимке должно иметь точный тип" % key,
                )
        expected = dict(INITIAL_STATE, altitude=10, energy=50, is_airborne=True)
        self.assert_state(teapot, expected)
        fresh = teapot.get_state()
        self.assertIsNot(fresh, first)
        self.assertIsNot(fresh, second)
        self.assertEqual(fresh, expected)

    def test_pt22_portal_bounds(self):
        """ПТ-22. tornado_portal(101, 0) вызывает ValueError."""
        teapot = self.make()
        self.command(teapot, "take_off")
        self.command(teapot, "ascend", meters=20)
        self.command(teapot, "eat_cloud")
        self.command(teapot, "eat_cloud")
        self.assert_state(
            teapot,
            dict(
                INITIAL_STATE,
                altitude=30,
                energy=76,
                clouds=2,
                is_airborne=True,
            ),
        )
        self.reject(teapot, ValueError, "tornado_portal", dx=101, dy=0)
        self.assert_state(
            teapot,
            dict(
                INITIAL_STATE,
                altitude=30,
                energy=76,
                clouds=2,
                is_airborne=True,
            ),
        )


if __name__ == "__main__":
    unittest.main()
