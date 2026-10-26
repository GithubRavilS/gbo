#!/usr/bin/env python3
"""Первый заказ ГБО · тарифы ПВ Бридж (Telegram 24.06 / 21.08.2026).

Платёж партнёру в ₽ сразу:
  (товар нетто € + выкуп 750 € + логистика 1 350 €) × курс ЦБ дня оплаты
Таможня РФ — отдельно импортёром: пошлина 5% + НДС 22% + брокер + ФТС + Казань.
"""

from __future__ import annotations

import json
from pathlib import Path

EUR = 90.2429  # ЦБ 24.10.2026
DATE = "26.10.2026"
BUYOUT_EUR = 750  # ≤ 15 000 € инвойса; иначе 5%
LOGISTICS_EUR = 1350  # котировка ГБО Белосток→Москва ~1 м³ / 250 кг
BROKER = 20_000  # партнёрский брокер из котировки ГБО (июнь)
KAZAN = 12_000  # местный перевозчик МСК→Казань (ПВБ до Москвы/СПб)
DUTY = 0.05
VAT_IMPORT = 0.22
MKT_DISC = 0.20
PARTNER = "ПВ Бридж"


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
    """items: (name, art, eur, kg, liters, dealer_rub, qty)"""
    goods_eur = sum(e * q for _, _, e, _, _, _, q in items)
    weight = sum(k * q for _, _, _, k, _, _, q in items)
    liters = sum(L * q for _, _, _, _, L, _, q in items)
    buyout = BUYOUT_EUR if goods_eur < 15_000 else goods_eur * 0.05
    pv_eur = goods_eur + buyout + logistics_eur
    pv_rub = pv_eur * EUR
    cv = (goods_eur + logistics_eur) * EUR  # ТС ≈ товар + фрахт (агентский выкуп вне ТС)
    duty = cv * DUTY
    vat = (cv + duty) * VAT_IMPORT
    fee = fts_fee(cv)
    russia = duty + vat + fee + BROKER + KAZAN
    landed = pv_rub + russia
    market = shelf = 0
    rows = []
    for name, art, e, k, L, d, q in items:
        sell = round(d * (1 - MKT_DISC))
        market += sell * q
        shelf += d * q
        share = (e * q) / goods_eur
        ep = landed * share / q
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
    return dict(
        partner=PARTNER,
        eur=EUR,
        date=DATE,
        goods_eur=round(goods_eur, 2),
        weight=round(weight, 1),
        liters=round(liters, 1),
        buyout_eur=buyout,
        logistics_eur=logistics_eur,
        pv_eur=round(pv_eur, 2),
        goods_rub=round(goods_eur * EUR),
        buyout_rub=round(buyout * EUR),
        logistics_rub=round(logistics_eur * EUR),
        pv_rub=round(pv_rub),
        cv_rub=round(cv),
        duty=round(duty),
        vat=round(vat),
        fee=fee,
        broker=BROKER,
        kazan=KAZAN,
        russia=round(russia),
        landed=round(landed),
        market=market,
        shelf=shelf,
        profit=round(market - landed),
        pct=round((market - landed) / landed * 100, 1),
        rows=rows,
    )


# Рекомендация: AT13×123 — чтобы чек ≤ 1 млн при логистике 1 350 €
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
    configs = {
        "rec": calc(REC),
        "at13": calc(AT13_ONLY),
        "kit": calc(KIT_B),
        "rec125_over": calc(
            [
                ("AT13 XP", "RGDG3990", 46.0, 1.6, 6.667, 12800, 125),
                ("BLASTER Y", "BLASTER Y 12x2/12", 4.5, 0.18, 0.909, 1250, 50),
                ("Тип 33", "33.EVG.13", 20.0, 0.65, 1.5, 5550, 20),
                ("FLS 12×12", "FL01S 12/12", 0.7, 0.08, 0.4, 250, 100),
            ]
        ),
    }
    out = Path(__file__).resolve().parent / "order_calc.json"
    out.write_text(json.dumps(configs, ensure_ascii=False, indent=2), encoding="utf-8")
    for k, t in configs.items():
        print(
            f"{k}: goods={t['goods_eur']}€  pv={t['pv_rub']:,}  "
            f"landed={t['landed']:,}  profit={t['profit']:+,} ({t['pct']}%)"
        )
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
