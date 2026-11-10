# Торнадочайник-3000
Безумное воздушное транспортное средство стихии «Воздух» из двумерного мира
без границ, оформленный как гигантский летающий чайник. Вместо двигателя он опирается на воздушные
потоки: взлетает, перемещается по плоскости, набирает и сбрасывает высоту, поглощает облака ради
энергии, проходит через торнадо-портал, садится и подзаряжается аплодисментами
![alt text](picture/Tornadotea.png)

## Карта файлов

| Путь | Назначение |
|---|---|
| `README.md` | этот файл: запуск, API, пример полёта |
| `SPEC.md` | техническое задание проекта № 3: ФТ-01–16, Н-01–03, ПТ-01–22 |
| `TEST_CASES.md` | тест-кейсы: приёмочные ПТ-01–22 и дополнительные граничные ДТ-01–11 |
| `TEST_PLAN.md` | план тестирования: уровни, окружение, порядок прогона, критерии |
| `REVIEW.md` | журнал независимого ревью (заполняется рецензентами) |
| [`REVIEW_Alzoabi.md`](REVIEW_Alzoabi.md) | ревью рецензента B: замечания B-01–B-03 |
| [`REVIEW_crazy_machine_Agapov.md`](REVIEW_crazy_machine_Agapov.md) | ревью рецензента C: замечания C01–C03 |
| `tests/` | автотесты `unittest`: `__init__.py`, `helpers.py`, `test_acceptance.py`, `test_boundaries.py` |
| `tornado_errors.py` | доменные исключения: `TornadoTeapotError`, `InvalidStateError`, `InsufficientResourcesError` |
| `tornado_teapot.py` | **планируется**: модуль с классом `TornadoTeapot`, появится после ревью |

## Требования к окружению

- Python **3.10 или новее** (см. п. 4.5 ТЗ).
- Никаких сторонних зависимостей устанавливать не нужно: тесты используют только стандартную
  библиотеку (`unittest`) и не требуют pytest.
- Кодировка файлов — UTF-8; сеть не требуется.

## Запуск проверок

Из корня репозитория:

```bash
python -m compileall -q tests tornado_errors.py
python -m unittest discover -s tests -t . -v
```

Точечный запуск отдельных модулей:

```bash
python -m unittest tests.test_acceptance -v
python -m unittest tests.test_boundaries -v
```

`compileall` проверяет синтаксис тестов. Discovery собирает **33 тест-метода**: 22 приёмочных
(`test_pt01_*` … `test_pt22_*`) и 11 дополнительных (`test_dt01_*` … `test_dt11_*`). Пока модуля нет, каждый
тест падает в `setUp` с `ModuleNotFoundError`.

Дополнительные тесты проверяют, в частности, достижение `y = ±110` вместе с проверками `x = ±110` (ДТ-03),
округление стоимости подъёма на соседних значениях `ascend(5)` и `ascend(6)` (ДТ-03) и пополнение запаса
облаков после портала в том же полёте (ДТ-11).

Общие помощники тестов (`tests/helpers.py`) задают начальное состояние
`{'x': 0, 'y': 0, 'altitude': 0, 'energy': 60, 'clouds': 0, 'is_airborne': False}`,
проверяют полное совпадение словарей состояния и точные типы значений, а неуспешные вызовы
проверяют так: исключение нужного типа **и** неизменность `get_state()` до и после вызова.
Состояние готовится только публичными командами из ТЗ.

## Публичный API

```python
from tornado_teapot import TornadoTeapot
from tornado_errors import (
    TornadoTeapotError,
    InvalidStateError,
    InsufficientResourcesError,
)

teapot = TornadoTeapot()
```

Класс создаётся без обязательных аргументов. Все успешные команды изменения состояния возвращают
`None`; состояние читается только через `get_state()`. Полные условия — в [`SPEC.md`](SPEC.md).

Отказы по состоянию и ресурсам выражаются доменными исключениями из `tornado_errors.py`.
`TornadoTeapotError` наследуется от `Exception` (не от `RuntimeError`), а `InvalidStateError`
и `InsufficientResourcesError` — от `TornadoTeapotError`.

| Метод | Аргументы | Действие | Исключения |
|---|---|---|---|
| `take_off()` | — | только с земли при `energy >= 10`: `altitude = 10`, `energy -= 10` | `InvalidStateError`: не на земле; `InsufficientResourcesError`: не хватает энергии |
| `move(dx, dy)` | целые −20…20, не оба нуля | в полёте: `x += dx`, `y += dy`, `energy -= \|dx\| + \|dy\|`; высота не меняется | `ValueError`: тип, диапазон, нулевой вектор; `InvalidStateError`: не в полёте; `InsufficientResourcesError`: не хватает энергии |
| `ascend(meters)` | целое 1…30 | в полёте: `altitude += meters` (не выше 100), `energy -= ceil(meters / 5)` | `ValueError`; `InvalidStateError`: не в полёте, выход за 100; `InsufficientResourcesError`: не хватает энергии |
| `descend(meters)` | целое 1…30 | в полёте: `altitude -= meters`, но не ниже 10; энергия не тратится | `ValueError`; `InvalidStateError`: не в полёте, результат ниже 10 |
| `eat_cloud()` | — | в полёте при `altitude >= 20` и `clouds < 3`: `clouds += 1`, `energy += 15` (не выше 100) | `InvalidStateError`: не в полёте, высота < 20, облаков уже 3 |
| `tornado_portal(dx, dy)` | целые −100…100, не оба нуля | в полёте при `altitude >= 30`, `clouds >= 2`, `energy >= 25`: координаты сдвигаются, `energy -= 25`, `clouds -= 2`; высота не меняется | `ValueError`: тип, диапазон, нулевой вектор; `InvalidStateError`: не в полёте, высота < 30; `InsufficientResourcesError`: облаков < 2 или энергии < 25 |
| `land()` | — | из полёта: `altitude = 0`, `clouds = 0`, `is_airborne = False`; координаты и энергия сохраняются | `InvalidStateError`: уже на земле |
| `applause(count)` | целое 1…10 | только на земле: `energy += 5 × count` (не выше 100) | `ValueError`; `InvalidStateError`: в полёте |
| `get_state()` | — | возвращает **новый независимый** словарь с ключами `x`, `y`, `altitude`, `energy`, `clouds`, `is_airborne`; ранее выданный снимок не изменяется последующими командами | — |

Порядок проверок фиксирован ТЗ (ФТ-15): сначала корректность аргументов (`ValueError`), затем
допустимость состояния (`InvalidStateError`), затем достаточность ресурсов
(`InsufficientResourcesError`). При конфликте состояния и ресурсов приоритет у `InvalidStateError`.
Тексты исключений не нормируются, поэтому тесты их не сверяют.

`clouds` — текущий расходуемый запас поглощённых, но ещё не израсходованных облаков. Портал тратит два
облака, после чего запас можно снова пополнять в том же полёте; суммарного лимита поглощений за полёт нет.

## Пример полёта

Воспроизводимый сценарий из приложения Б ТЗ. Выполняется после появления `tornado_teapot.py`.

```python
from tornado_teapot import TornadoTeapot

teapot = TornadoTeapot()
teapot.take_off()               # высота 10, энергия 50
teapot.ascend(20)               # высота 30, энергия 46
teapot.eat_cloud()              # 1 облако, энергия 61
teapot.eat_cloud()              # 2 облака, энергия 76
teapot.tornado_portal(70, -40)  # x=70, y=-40, энергия 51
teapot.land()                   # высота 0, облака 0
print(teapot.get_state())
```

Точный ожидаемый вывод:

```python
{'x': 70, 'y': -40, 'altitude': 0, 'energy': 51, 'clouds': 0, 'is_airborne': False}
```