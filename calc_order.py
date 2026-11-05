#!/usr/bin/env python3
"""Заказ ГБО · 3 ноября 2026.

Потолки: до российского НДС не больше 750 тыс. ₽, заморозка с НДС не больше 1 млн ₽,
вес ≤ 250 кг, объём ≤ 1 м³. В заказе только строки в плюсе при продаже «полка −20%».
В строке не меньше 20 штук. Меньше — позицию не ставим, инвойс не раздуваем.

Фрахт 1 800 € — ставка на эту партию из трёх позиций.
Пошлина 7% от таможенной стоимости (товар + доставка).
Комиссия выкупа в расчёт не входит.
Конверсия 5% сидит сверху на всю кассу круга: товар, доставку, пошлину, НДС,
брокера, сбор и Казань. В таможенную стоимость она не входит.
"""

from __future__ import annotations

import json
from pathlib import Path

EUR = 90.4635  # ЦБ с 3.11.2026
USD = 80.9734
DATE = "03.11.2026"
VAT_PL = 0.23
LOGISTICS_EUR = 1800
COMM_USD = 0  # выкуп через посредника в эту заявку не входит
BROKER = 25_000
KAZAN = 24_000
DUTY = 0.07
VAT_IMPORT = 0.22
MKT_DISC = 0.20
CONV = 0.05  # конверсионные потери на весь круг, сверху


def fts_fee(ts: float) -> int:
    if ts <= 200_000:
        return 1231
    if ts <= 450_000:
        return 2462
    if ts <= 1_200_000:
        return 4924
    if ts <= 2_700_000:
        return 13_541
    return 18_465


def calc(items: list[tuple]) -> dict:
    """items: (name, art, kind, eur, kg, liters, dealer, qty)"""
    goods_eur = sum(e * q for *_, e, k, L, d, q in items)
    weight = sum(k * q for *_, e, k, L, d, q in items)
    liters = sum(L * q for *_, e, k, L, d, q in items)
    goods_rub = goods_eur * EUR
    comm_rub = COMM_USD * USD
    log_rub = LOGISTICS_EUR * EUR
    hk_rub = goods_rub + comm_rub
    teu_rub = log_rub
    pl_vat = goods_eur * VAT_PL * EUR
    cv = goods_rub + log_rub
    duty = cv * DUTY
    vat_ru = (cv + duty) * VAT_IMPORT
    fee = fts_fee(cv)
    russia = duty + vat_ru + fee + BROKER + KAZAN
    base = hk_rub + teu_rub + russia
    conv = base * CONV
    invested = base + conv
    market = shelf = 0
    rows = []
    for name, art, kind, e, k, L, d, q in items:
        sell = round(d * (1 - MKT_DISC))
        market += sell * q
        shelf += d * q
        share = (e * q) / goods_eur
        pl = e * EUR
        comm_u = comm_rub * share / q
        log_u = log_rub * share / q
        duty_u = duty * share / q
        vat_u = vat_ru * share / q
        fix_u = (fee + BROKER + KAZAN) * share / q
        conv_u = conv * share / q
        land = invested * share / q
        rows.append(
            dict(
                name=name,
                art=art,
                kind=kind,
                qty=q,
                eur=e,
                kg=k,
                liters=L,
                sum_eur=round(e * q, 2),
                weight=round(k * q, 2),
                volume_l=round(L * q, 1),
                poland=round(pl),
                commission=round(comm_u),
                logistics=round(log_u),
                duty=round(duty_u),
                vat_ru=round(vat_u),
                other=round(fix_u),
                fx=round(conv_u),
                cost=round(land),
                shelf=d,
                sell=sell,
                margin=round(sell - land),
                pct=round((sell - land) / land * 100, 1),
                profit_line=round((sell - land) * q),
            )
        )
    return dict(
        date=DATE,
        eur=EUR,
        usd=USD,
        goods_eur=round(goods_eur, 2),
        weight=round(weight, 1),
        liters=round(liters, 1),
        m3=round(liters / 1000, 3),
        goods_rub=round(goods_rub),
        commission_usd=COMM_USD,
        commission_rub=round(comm_rub),
        logistics_eur=LOGISTICS_EUR,
        logistics_rub=round(log_rub),
        hk_rub=round(hk_rub),
        teu_rub=round(teu_rub),
        pl_vat_float=round(pl_vat),
        duty=round(duty),
        vat_ru=round(vat_ru),
        fee=fee,
        conv_rate=CONV,
        conv_rub=round(conv),
        broker=BROKER,
        kazan=KAZAN,
        russia=round(russia),
        invested=round(invested),
        pre_vat=round(invested - vat_ru),
        market=market,
        shelf=shelf,
        profit=round(market - invested),
        pct=round((market - invested) / invested * 100, 1),
        rows=rows,
    )


# Три строки, в каждой от 20 штук. Круглые количества.
# AT13 100 и FLS 200 — новые цены ноября, запас ограничен (завод так писал на 130 и на 200).
# Тип 33 × 50 — в наличии, без пометки об ограниченном запасе. Цена 19.10.
# AT02 / AEB / MP48 в плюсе и в наличии, но коробка от 20 штук рядом с этим ядром
# уже не влезает в 750 тыс. до НДС. В инвойс их не ставим.
REC = [
    ("AT13 XP", "RGDG3990", "редуктор", 47.0, 1.6, 6.667, 12800, 100),
    ("Тип 33", "33.EVG.13", "рейка 4 цил.", 20.0, 0.65, 1.5, 5550, 50),
    ("FLS 12×12", "FL01S 12/12", "фильтр", 0.8, 0.08, 0.4, 250, 200),
]


def main() -> None:
    t = calc(REC)
    Path("order_calc.json").write_text(
        json.dumps({"rec": t}, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        f"invested={t['invested']:,} market={t['market']:,} "
        f"profit={t['profit']:+,} ({t['pct']}%) "
        f"kg={t['weight']} m3={t['m3']} eur={t['goods_eur']}"
    )


if __name__ == "__main__":
    main()
