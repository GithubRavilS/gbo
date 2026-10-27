#!/usr/bin/env python3
"""Первый заказ ГБО · расчёт на круг после подтверждения ПВ Бридж (27.10.2026).

Схема (подтверждено):
  РФ → АЗИЗОГЛУ (HK) в ₽ за товар+комиссию
  РФ → ООО ПВ Бридж — ТЭУ (логистика)
  их EU → AutoChill → Digitronic → забор
  таможня на нас (ЕЛС ФТС), брокер по желанию

Комиссия: инвойс AutoChill в USD → 300 $ (до 15 000 $).
Логистика ориентир: 1 350 € на ~1 м³ / ~250 кг.
"""

from __future__ import annotations

import json
from pathlib import Path

EUR = 90.0935  # ЦБ 27.10.2026
USD = 80.4909
DATE = "27.10.2026"
VAT_PL = 0.23
LOGISTICS_EUR = 1350
COMM_USD = 300  # подтверждённый тариф при оплате в USD
BROKER = 25_000  # ответ Екатерины ~25 000
KAZAN = 12_000  # ориентир МСК→Казань
DUTY = 0.05
VAT_IMPORT = 0.22
MKT_DISC = 0.20


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
    invested = hk_rub + teu_rub + russia  # на круг, PL VAT возвращается
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
        land = invested * share / q
        rows.append(
            dict(
                name=name,
                art=art,
                kind=kind,
                qty=q,
                eur=e,
                sum_eur=round(e * q, 2),
                poland=round(pl),
                commission=round(comm_u),
                logistics=round(log_u),
                duty=round(duty_u),
                vat_ru=round(vat_u),
                other=round(fix_u),
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
        broker=BROKER,
        kazan=KAZAN,
        russia=round(russia),
        invested=round(invested),
        market=market,
        shelf=shelf,
        profit=round(market - invested),
        pct=round((market - invested) / invested * 100, 1),
        rows=rows,
    )


REC = [
    ("AT13 XP", "RGDG3990", "редуктор", 46.0, 1.6, 6.667, 12800, 123),
    ("BLASTER Y", "BLASTER Y 12x2/12", "фильтр", 4.5, 0.18, 0.909, 1250, 50),
    ("Тип 33", "33.EVG.13", "рейка 4 цил.", 20.0, 0.65, 1.5, 5550, 20),
    ("FLS 12×12", "FL01S 12/12", "фильтр", 0.7, 0.08, 0.4, 250, 100),
]


def main() -> None:
    t = calc(REC)
    Path("order_calc.json").write_text(
        json.dumps({"rec": t}, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        f"invested={t['invested']:,} market={t['market']:,} "
        f"profit={t['profit']:+,} ({t['pct']}%)"
    )


if __name__ == "__main__":
    main()
