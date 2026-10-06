# GBO поставка

Каталог со **скринов Digitronic** + аудио установщиков (25.09 / 27.09) + сверка с инвойсом AutoChill и польским оптом.

## Открыть отчёт

После пуша:
- https://raw.githack.com/GithubRavilS/gbo/cursor/gbo-spec-order-0e4a/index.html

Локально (Mac):
- `/Users/ravilcrypto/Documents/Cursor/gbo/index.html`

## Файлы

- `ORDER.md` — заказ из инвойса, математика без заморозки, текст поставщику
- `zapros-assortiment.xlsx` — позиции, по которым её цены ещё нет
- `SPEC.md` — все 20 позиций и что из них было в инвойсе
- `index.html` — полный расклад
- `VARIANTS.md` — краткая таблица
- `FIELD_NOTES.md` — транскрипты WhatsApp
- `build.py` / `data.json` — пересчёт

```bash
python3 build.py
```

## Важно

- Касса = landed **один раз** (без двойной заморозки).
- Точные € — только позиции из инвойса AutoChill (редукторы + фильтры).
- Электроника / мультиклапаны / рейки / трубки — **PL-прокси**, уточнить у AutoChill.
- Рынок установщиков ≈ полка Digitronic **−20…30%**.
