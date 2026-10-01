# GBO поставка (PL → RU)

Отдельный проект расчёта поставки газового оборудования: фильтры / редукторы AutoChill → Казань.

Раньше жил внутри Private Assistant (`projects/15_gas-equipment-ru` / старый `gbo-investor`). Здесь — канон на компьютере с живой моделью.

## Открыть

- `index.html` — сводка SKU + варианты рейса
- `VARIANTS.md` — конкретный ответ: go/no-go, НДС/не НДС, логистика
- `data.json` — цифры после `python3 build.py`
- `build.py` — модель landed / freeze / маржа

## Пересчёт

```bash
python3 build.py
```

Курс EUR и полки Digitronic правятся в `build.py`, затем пересборка.

## Live

Старый деплой: https://gbo-seven.vercel.app (обновить после мержа, если нужен live).
