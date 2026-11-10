"""Общие проверки состояния, результатов команд и исключений."""

import importlib
import unittest

INITIAL_STATE = {
    "x": 0,
    "y": 0,
    "altitude": 0,
    "energy": 60,
    "clouds": 0,
    "is_airborne": False,
}

STATE_KEYS = ("x", "y", "altitude", "energy", "clouds", "is_airborne")
INT_STATE_KEYS = ("x", "y", "altitude", "energy", "clouds")


class ContractCase(unittest.TestCase):
    """Базовый класс контрактных тестов.

    Класс не содержит методов с префиксом ``test_``, поэтому loader может
    безопасно обнаружить его как импортированный базовый класс.
    """

    def setUp(self):
        module = importlib.import_module("tornado_teapot")
        self.teapot_class = module.TornadoTeapot

    def make(self):
        """Создаёт новый экземпляр проверяемого транспортного средства."""
        return self.teapot_class()

    def command(self, teapot, method_name, *args, **kwargs):
        """Выполняет успешную команду и проверяет возврат ``None``."""
        method = getattr(teapot, method_name)
        result = method(*args, **kwargs)
        self.assertIsNone(
            result,
            "Успешная команда %s должна возвращать None" % method_name,
        )

    def reject(self, teapot, exc_type, method_name, *args, **kwargs):
        """Проверяет ошибочную команду и неизменность полного состояния.

        Снимок ``before`` копируется до вызова, а после отказа состояние
        сверяется через :meth:`assert_state`, поэтому сравниваются не только
        значения, но и точные типы полей. Возвращает пойманное исключение.
        """
        before = dict(teapot.get_state())
        method = getattr(teapot, method_name)
        with self.assertRaises(exc_type) as caught:
            method(*args, **kwargs)
        self.assert_state(teapot, before)
        return caught.exception

    def assert_state(self, teapot, expected):
        """Сравнивает полный словарь состояния и точные типы значений."""
        state = teapot.get_state()
        self.assertIsInstance(state, dict, "get_state() должен возвращать dict")
        self.assertEqual(set(state), set(STATE_KEYS), "Неверный набор ключей")
        for key in INT_STATE_KEYS:
            self.assertIs(
                type(state[key]),
                int,
                "Значение %s должно иметь точный тип int" % key,
            )
        self.assertIs(
            type(state["is_airborne"]),
            bool,
            "Значение is_airborne должно иметь точный тип bool",
        )
        self.assertEqual(state, expected, "Состояние не совпадает с ожидаемым")
