#!/usr/bin/env python3
"""GBO · на круг с раздельным PL VAT float.

ПВБ в ₽ = (инвойс AutoChill нетто 0% VAT + выкуп 750 + лог 1350) × курс.
AutoChill → Digitronic с VAT 23%: разница — оборотные PL до возврата VAT.
На круг: вложено = платёж ПВБ + таможня РФ + PL VAT − возврат PL VAT
        = платёж ПВБ + таможня РФ  (VAT сокращается).
"""

from __future__ import annotations

import json
from pathlib import Path

EUR = 90.2429
DATE = "26.10.2026"
VAT_PL = 0.23
BUYOUT_EUR = 750
LOGISTICS_EUR = 1350
BROKER = 20_000
KAZAN = 12_000
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
    if ts <= 4_200_000:
        return 18_465
    if ts <= 5_500_000:
        return 21_344
    if ts <= 10_000_000:
        return 49_240
    return 73_860


def calc(items: list[tuple], logistics_eur: float = LOGISTICS_EUR) -> dict:
    goods_eur = sum(e * q for _, _, e, _, _, _, q in items)
    weight = sum(k * q for _, _, _, k, _, _, q in items)
    liters = sum(L * q for _, _, _, _, L, _, q in items)
    gross_eur = round(goods_eur * (1 + VAT_PL), 2)
    buyout = BUYOUT_EUR if goods_eur < 15_000 else goods_eur * 0.05
    # ПВБ платит AutoChill по инвойсу без VAT = нетто
    pv_eur = round(goods_eur + buyout + logistics_eur, 2)
    pv_rub = round(pv_eur * EUR)
    vat_pl = round(goods_eur * VAT_PL * EUR)  # float на AutoChill
    cv = (goods_eur + logistics_eur) * EUR
    duty = round(cv * DUTY)
    vat_ru = round((cv + duty) * VAT_IMPORT)
    fee = fts_fee(cv)
    russia = duty + vat_ru + fee + BROKER + KAZAN
    # Пик группы: ПВБ + PL VAT float + таможня; на круг VAT возвращается
    cash_peak = pv_rub + vat_pl + russia
    invested = cash_peak - vat_pl  # = pv_rub + russia
    market = shelf = 0
    rows = []
    for name, art, e, k, L, d, q in items:
        sell = round(d * (1 - MKT_DISC))
        market += sell * q
        shelf += d * q
        share = (e * q) / goods_eur
        ep = invested * share / q
        rows.append(
            dict(
                name=name,
                art=art,
                qty=q,
                eur=e,
                sum_eur=round(e * q, 2),
                buy_rub=round(e * EUR),
                ep=round(ep),
                dealer=d,
                sell=sell,
                margin_u=round(sell - ep),
                pct=round((sell - ep) / ep * 100, 1),
                profit_line=round((sell - ep) * q),
            )
        )
    profit = market - invested
    return dict(
        date=DATE,
        eur=EUR,
        goods_eur=round(goods_eur, 2),
        gross_digitronic_eur=gross_eur,
        invoice_to_pvb_eur=round(goods_eur, 2),  # 0% VAT
        weight=round(weight, 1),
        liters=round(liters, 1),
        buyout_eur=buyout,
        logistics_eur=logistics_eur,
        pv_eur=pv_eur,
        to_autochill_eur=round(goods_eur, 2),
        to_autochill_rub=round(goods_eur * EUR),
        buyout_rub=round(buyout * EUR),
        logistics_rub=round(logistics_eur * EUR),
        pv_rub=pv_rub,
        pl_vat_float=vat_pl,
        duty=duty,
        vat_ru=vat_ru,
        fee=fee,
        broker=BROKER,
        kazan=KAZAN,
        russia=russia,
        cash_peak=cash_peak,
        invested=invested,
        market=market,
        shelf=shelf,
        profit=profit,
        pct=round(profit / invested * 100, 1),
        rows=rows,
    )


REC = [
    ("AT13 XP", "RGDG3990", 46.0, 1.6, 6.667, 12800, 123),
    ("BLASTER Y", "BLASTER Y 12x2/12", 4.5, 0.18, 0.909, 1250, 50),
    ("Тип 33", "33.EVG.13", 20.0, 0.65, 1.5, 5550, 20),
    ("FLS 12×12", "FL01S 12/12", 0.7, 0.08, 0.4, 250, 100),
]
AT13_ONLY = [("AT13 XP", "RGDG3990", 46.0, 1.6, 6.667, 12800, 139)]
KIT_B = [
    ("BLASTER Y", "BLASTER Y 12x2/12", 4.5, 0.18, 0.909, 1250, 450),
    ("FLS 12×12", "FL01S 12/12", 0.7, 0.08, 0.4, 250, 200),
    ("Nordic", "RGDG3890", 26.0, 1.3, 5.0, 7000, 20),
    ("Nordic XP", "RGDG3895", 34.0, 1.4, 5.556, 9200, 25),
    ("AT13 XP", "RGDG3990", 46.0, 1.6, 6.667, 12800, 40),
]


def main() -> None:
    configs = {"rec": calc(REC), "at13": calc(AT13_ONLY), "kit": calc(KIT_B)}
    Path("order_calc.json").write_text(
        json.dumps(configs, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    for k, t in configs.items():
        print(
            f"{k}: pv={t['pv_rub']:,} pl_vat={t['pl_vat_float']:,} "
            f"ru={t['russia']:,} invested={t['invested']:,} "
            f"profit={t['profit']:+,} ({t['pct']}%)"
        )


if __name__ == "__main__":
    main()
