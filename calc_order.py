#!/usr/bin/env python3
"""Первый заказ ГБО · цепочка с польским звеном + тарифы ПВ Бридж.

Последовательность денег:
  ① РФ → ПВ Бридж (₽): (Digitronic брутто с PL VAT 23% + выкуп 750 € + лог 1 350 €) × курс ЦБ
  ② ПВ Бридж EU → AutoChill (PL) в €
  ③ AutoChill → Digitronic: нетто + 23% VAT
  ④ Таможня РФ отдельно: пошлина 5% + НДС 22% + брокер + ФТС + Казань
  ⑤ Позже AutoChill возвращает входной PL VAT → экономика ≈ без 23%

Пик заморозки = платёж ПВБ + таможня РФ (до возврата PL VAT).
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
    """items: (name, art, eur_net, kg, liters, dealer_rub, qty)"""
    goods_eur = sum(e * q for _, _, e, _, _, _, q in items)
    weight = sum(k * q for _, _, _, k, _, _, q in items)
    liters = sum(L * q for _, _, _, _, L, _, q in items)
    gross_eur = round(goods_eur * (1 + VAT_PL), 2)  # AutoChill → Digitronic
    buyout = BUYOUT_EUR if goods_eur < 15_000 else goods_eur * 0.05
    # В чек ПВБ кладём брутто, чтобы PL закрыла Digitronic без кассового разрыва
    pv_eur = round(gross_eur + buyout + logistics_eur, 2)
    pv_rub = round(pv_eur * EUR)
    # ТС РФ: экспортная цена без PL VAT + фрахт
    cv = (goods_eur + logistics_eur) * EUR
    duty = round(cv * DUTY)
    vat_ru = round((cv + duty) * VAT_IMPORT)
    fee = fts_fee(cv)
    russia = duty + vat_ru + fee + BROKER + KAZAN
    peak = pv_rub + russia
    vat_pl = round(goods_eur * VAT_PL * EUR)
    economic = peak - vat_pl
    market = shelf = 0
    rows = []
    for name, art, e, k, L, d, q in items:
        sell = round(d * (1 - MKT_DISC))
        market += sell * q
        shelf += d * q
        share = (e * q) / goods_eur
        ep = economic * share / q
        rows.append(
            dict(
                name=name,
                art=art,
                qty=q,
                eur=e,
                sum_eur=round(e * q, 2),
                buy_rub=round(e * EUR),
                buy_gross_rub=round(e * (1 + VAT_PL) * EUR),
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
        vat_pl_rate=VAT_PL,
        goods_eur=round(goods_eur, 2),
        gross_eur=gross_eur,
        weight=round(weight, 1),
        liters=round(liters, 1),
        buyout_eur=buyout,
        logistics_eur=logistics_eur,
        pv_eur=pv_eur,
        to_autochill_eur=gross_eur,
        to_autochill_rub=round(gross_eur * EUR),
        buyout_rub=round(buyout * EUR),
        logistics_rub=round(logistics_eur * EUR),
        pv_rub=pv_rub,
        digitronic_pay_eur=gross_eur,
        cv_rub=round(cv),
        duty=duty,
        vat_ru=vat_ru,
        fee=fee,
        broker=BROKER,
        kazan=KAZAN,
        russia=russia,
        peak_freeze=peak,
        vat_pl_reclaim=vat_pl,
        economic=economic,
        market=market,
        shelf=shelf,
        profit=round(market - economic),
        pct=round((market - economic) / economic * 100, 1),
        profit_vs_peak=round(market - peak),
        pct_vs_peak=round((market - peak) / peak * 100, 1),
        rows=rows,
    )


# Пик заморозки ≤ 1 млн при брутто Digitronic в чеке ПВБ
REC = [
    ("AT13 XP", "RGDG3990", 46.0, 1.6, 6.667, 12800, 102),
    ("BLASTER Y", "BLASTER Y 12x2/12", 4.5, 0.18, 0.909, 1250, 50),
    ("Тип 33", "33.EVG.13", 20.0, 0.65, 1.5, 5550, 20),
    ("FLS 12×12", "FL01S 12/12", 0.7, 0.08, 0.4, 250, 100),
]
# Если готовы к пику ~1,13 млн до возврата PL VAT — больше AT13
REC_123 = [
    ("AT13 XP", "RGDG3990", 46.0, 1.6, 6.667, 12800, 123),
    ("BLASTER Y", "BLASTER Y 12x2/12", 4.5, 0.18, 0.909, 1250, 50),
    ("Тип 33", "33.EVG.13", 20.0, 0.65, 1.5, 5550, 20),
    ("FLS 12×12", "FL01S 12/12", 0.7, 0.08, 0.4, 250, 100),
]
AT13_ONLY = [("AT13 XP", "RGDG3990", 46.0, 1.6, 6.667, 12800, 117)]
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
        "rec123_peak_over": calc(REC_123),
        "at13": calc(AT13_ONLY),
        "kit": calc(KIT_B),
    }
    out = Path(__file__).resolve().parent / "order_calc.json"
    out.write_text(json.dumps(configs, ensure_ascii=False, indent=2), encoding="utf-8")
    for k, t in configs.items():
        print(
            f"{k}: net={t['goods_eur']}€ gross={t['gross_eur']}€  "
            f"pv={t['pv_rub']:,} peak={t['peak_freeze']:,} "
            f"ec={t['economic']:,} profit={t['profit']:+,} ({t['pct']}%)"
        )
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
