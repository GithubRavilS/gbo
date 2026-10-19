#!/usr/bin/env python3
"""GBO поставка PL→RU — каталог со скринов Digitronic + аудио установщиков.

Цены закупки:
  - invoice  = AutoChill EUR (есть в инвойсе)
  - pl_proxy = польский опт нетто / 4.25 × 0.94 (калибровка по Nordic 26€ vs PL)
  - none     = только полка, маржу не считаем (нет цены закупки)
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EUR = 94.8810  # ЦБ РФ ~01.10.2026
PLN_EUR = 4.25
PL_TO_INVOICE = 0.94  # Nordic: 26€ / (117.89zł/4.25) ≈ 0.94
DATE = "01.10.2026"
BUYOUT_EUR = 750
BROKER = 25000
KAZAN = 12000
DUTY = 0.05
VAT_IMPORT = 0.22


def fts_fee(ts: float) -> int:
    if ts <= 200000:
        return 1231
    if ts <= 450000:
        return 2462
    if ts <= 1200000:
        return 4924
    if ts <= 2700000:
        return 13541
    if ts <= 4200000:
        return 18465
    if ts <= 5500000:
        return 21344
    if ts <= 10000000:
        return 49240
    return 73860


def logistics_eur(kg: float) -> float:
    return 162.5 + 4.75 * kg


def pl_proxy(pln_net: float) -> float:
    return round(pln_net / PLN_EUR * PL_TO_INVOICE, 2)


def calc(eur_unit: float, qty: int, kg_unit: float) -> dict:
    """Один платёжный контур: аванс → товар с аванса. Касса = landed один раз."""
    goods_eur = eur_unit * qty
    goods_rub = goods_eur * EUR
    weight = qty * kg_unit
    log_eur = logistics_eur(weight)
    log_rub = log_eur * EUR
    buyout_eur = BUYOUT_EUR if goods_eur < 15000 else goods_eur * 0.05
    buyout_rub = buyout_eur * EUR
    ts = goods_rub + log_rub
    duty = ts * DUTY
    vat = (ts + duty) * VAT_IMPORT
    fee = fts_fee(ts)
    fixed = BROKER + fee + KAZAN
    partner = buyout_rub + log_rub
    customs = duty + vat + fixed
    landed = goods_rub + partner + customs
    ep = landed / qty
    ep_ex_vat = (landed - vat) / qty
    return dict(
        qty=qty,
        weight=weight,
        goods_eur=goods_eur,
        goods_rub=goods_rub,
        log_eur=log_eur,
        log_rub=log_rub,
        buyout_rub=buyout_rub,
        partner=partner,
        duty=duty,
        vat=vat,
        fee=fee,
        fixed=fixed,
        customs=customs,
        landed=landed,
        ep=ep,
        ep_ex_vat=ep_ex_vat,
        buy_unit_rub=eur_unit * EUR,
    )


# Каталог = скрины digitronicgas.ru (01.10) + известный инвойс AutoChill + PL-прокси.
# eur=None → только полка (нет закупки).
SKUS = [
    # --- Электроника (скрины) ---
    dict(
        id="mp32",
        group="Электроника",
        name="MP32 PT-MAP 4 цил.",
        art="616000573",
        eur=pl_proxy(284.55),  # ZAMEL PL netto
        eur_src="pl_proxy",
        kg=1.05,
        dealer=13200,
        shelf_vat=5,
        stock="много",
        base_qty=80,
        in_invoice=False,
        on_shelf=True,
        url="https://www.digitronicgas.ru/",
        note="Скрин. PL-прокси ZAMEL MP32. Ходовой комплект 4 цил.",
    ),
    dict(
        id="mp48",
        group="Электроника",
        name="MP48 4 цил.",
        art="616000087",
        eur=pl_proxy(294.31),  # Jacuś netto
        eur_src="pl_proxy",
        kg=1.10,
        dealer=15600,
        shelf_vat=5,
        stock="много",
        base_qty=70,
        in_invoice=False,
        on_shelf=True,
        url="https://www.digitronicgas.ru/",
        note="Скрин. PL-прокси Jacuś MP48. В наличии на Digitronic.",
    ),
    dict(
        id="mp48_obd",
        group="Электроника",
        name="MP48 OBD 4 цил.",
        art="616000089",
        eur=pl_proxy(334.96),  # Jacuś netto
        eur_src="pl_proxy",
        kg=1.15,
        dealer=18200,
        shelf_vat=5,
        stock="много",
        base_qty=60,
        in_invoice=False,
        on_shelf=True,
        url="https://www.digitronicgas.ru/",
        note="Скрин. PL-прокси Jacuś MP48 OBD. Дороже обычного MP48.",
    ),
    dict(
        id="maxi2",
        group="Электроника",
        name="Maxi-2 TITAN 4 цил.",
        art="WEG-AMD024409999-000",
        eur=None,
        eur_src="none",
        kg=1.20,
        dealer=13300,
        shelf_vat=5,
        stock="нет",
        base_qty=40,
        in_invoice=False,
        on_shelf=True,
        url="https://www.digitronicgas.ru/",
        note="Скрин. Временно нет в наличии. Нет цены PL/инвойса — маржу не считаем.",
    ),
    dict(
        id="iq4",
        group="Электроника",
        name="iQ 4 цил.",
        art="WEG-AMD028409999-300",
        eur=None,
        eur_src="none",
        kg=1.30,
        dealer=23500,
        shelf_vat=5,
        stock="нет",
        base_qty=30,
        in_invoice=False,
        on_shelf=True,
        url="https://www.digitronicgas.ru/",
        note="Скрин. OOS. Премиум линейка — без цены закупки.",
    ),
    dict(
        id="iq3d6",
        group="Электроника",
        name="iQ 3D-6 ц.",
        art="WEG-AMD030609999-300",
        eur=None,
        eur_src="none",
        kg=1.40,
        dealer=23300,
        shelf_vat=0,
        stock="нет",
        base_qty=25,
        in_invoice=False,
        on_shelf=True,
        url="https://www.digitronicgas.ru/",
        note="Скрин. OOS. НДС полки 0%.",
    ),
    dict(
        id="iq3d8",
        group="Электроника",
        name="iQ 3D-8 ц.",
        art="WEG-AMD030809999-300",
        eur=None,
        eur_src="none",
        kg=1.50,
        dealer=28000,
        shelf_vat=5,
        stock="нет",
        base_qty=20,
        in_invoice=False,
        on_shelf=True,
        url="https://www.digitronicgas.ru/",
        note="Скрин. OOS.",
    ),
    # --- Редукторы (скрин + инвойс) ---
    dict(
        id="nordic",
        group="Редуктор",
        name="AT09 Nordic",
        art="RGDG3890",
        eur=26.0,
        eur_src="invoice",
        kg=1.30,
        dealer=7000,
        shelf_vat=5,
        stock="много",
        base_qty=200,
        in_invoice=True,
        on_shelf=True,
        url="https://www.digitronicgas.ru/catalog/d/reduktor_tomasetto_at09_nordic/",
        note="Скрин + инвойс AutoChill 26€. До ~170 л.с.",
    ),
    dict(
        id="nordic_xp",
        group="Редуктор",
        name="AT09 Nordic XP",
        art="RGDG3895",
        eur=34.0,
        eur_src="invoice",
        kg=1.40,
        dealer=9200,
        shelf_vat=20,
        stock="много",
        base_qty=180,
        in_invoice=True,
        on_shelf=True,
        url="https://www.digitronicgas.ru/catalog/d/reduktor_tomasetto_at09_nordic_xp_do_250_l_s/",
        note="Скрин + инвойс 34€. Полка с НДС 20%.",
    ),
    dict(
        id="at13",
        group="Редуктор",
        name="AT13 XP",
        art="RGDG3990",
        eur=46.0,
        eur_src="invoice",
        kg=1.60,
        dealer=12800,
        shelf_vat=5,
        stock="много",
        base_qty=150,
        in_invoice=True,
        on_shelf=True,
        url="https://www.digitronicgas.ru/catalog/d/reduktor_tomasetto_at13_xp/",
        note="Скрин + инвойс 46€. Лучшая маржа среди редукторов.",
    ),
    # --- Мультиклапаны ---
    dict(
        id="mv_315",
        group="Мультиклапан",
        name="AT02 Sprint A 315-30°",
        art="MVDG0205.1",
        eur=pl_proxy(103.66),  # Jacuś близкий AT02 Sprint netto
        eur_src="pl_proxy",
        kg=0.85,
        dealer=5550,
        shelf_vat=5,
        stock="много",
        base_qty=100,
        in_invoice=False,
        on_shelf=True,
        url="https://www.digitronicgas.ru/",
        note="Скрин. PL-прокси по AT02 Sprint. Класс A.",
    ),
    dict(
        id="mv_vzu",
        group="Мультиклапан",
        name="Sprint+ВЗУ A 220/225-30°",
        art="MVDG0012",
        eur=pl_proxy(116.67),  # ~143.50 brutto / 1.23 ≈ 116.7
        eur_src="pl_proxy",
        kg=1.00,
        dealer=4150,
        shelf_vat=5,
        stock="много",
        base_qty=100,
        in_invoice=False,
        on_shelf=True,
        url="https://www.digitronicgas.ru/",
        note="Скрин. С ВЗУ. Полка дешевле 315 — проверить комплектацию.",
    ),
    # --- Рейки ---
    dict(
        id="aeb_rail",
        group="Рейка",
        name="AEB полимер 4 цил. 1,9 Ом",
        art="620500170",
        eur=pl_proxy(180.0),  # оценка PL нетто ~180zł (нет точного совпадения)
        eur_src="pl_proxy",
        kg=0.55,
        dealer=8000,
        shelf_vat=5,
        stock="много",
        base_qty=80,
        in_invoice=False,
        on_shelf=True,
        url="https://www.digitronicgas.ru/",
        note="Скрин. PL-прокси оценка — уточнить у AutoChill.",
    ),
    dict(
        id="type33",
        group="Рейка",
        name="Тип 33 · 4 цил. 2 Ом BFC",
        art="33.EVG.13",
        eur=pl_proxy(130.0),
        eur_src="pl_proxy",
        kg=0.65,
        dealer=5550,
        shelf_vat=5,
        stock="много",
        base_qty=80,
        in_invoice=False,
        on_shelf=True,
        url="https://www.digitronicgas.ru/",
        note="Скрин. PL-прокси оценка.",
    ),
    # --- Трубки ---
    dict(
        id="tp6",
        group="Трубка",
        name="Трубка 6×1 мм · 48 м IT",
        art="TP6-48",
        eur=pl_proxy(220.0),
        eur_src="pl_proxy",
        kg=3.2,
        dealer=11300,
        shelf_vat=0,
        stock="много",
        base_qty=40,
        in_invoice=False,
        on_shelf=True,
        url="https://www.digitronicgas.ru/",
        note="Скрин. Бухта 48 м. НДС полки 0%. PL-прокси оценка.",
    ),
    dict(
        id="tp8",
        group="Трубка",
        name="Трубка 8×1 мм · 48 м IT",
        art="ТР8-48",
        eur=pl_proxy(270.0),
        eur_src="pl_proxy",
        kg=4.5,
        dealer=13900,
        shelf_vat=5,
        stock="много",
        base_qty=30,
        in_invoice=False,
        on_shelf=True,
        url="https://www.digitronicgas.ru/",
        note="Скрин. Бухта 48 м. PL-прокси оценка.",
    ),
    # --- Фильтры (скрин + инвойс) ---
    dict(
        id="fls",
        group="Фильтр",
        name="FLS 12×12",
        art="FL01S 12/12",
        eur=0.70,
        eur_src="invoice",
        kg=0.08,
        dealer=250,
        shelf_vat=0,
        stock="много",
        base_qty=2500,
        in_invoice=True,
        on_shelf=True,
        url="https://www.digitronicgas.ru/catalog/d/filtr_nizkogo_davleniya_nerazbornyy_fls_12x12_mm/",
        note="Скрин + инвойс 0.70€. Ходовой расходник.",
    ),
    dict(
        id="blaster",
        group="Фильтр",
        name="BLASTER 12×12",
        art="BLASTER 12х12",
        eur=3.50,
        eur_src="invoice",
        kg=0.15,
        dealer=880,
        shelf_vat=5,
        stock="много",
        base_qty=1400,
        in_invoice=True,
        on_shelf=True,
        url="https://www.digitronicgas.ru/catalog/d/filtr_razbornyy_tsentrobezhnyy_blaster_12_x12/",
        note="Скрин + инвойс 3.50€.",
    ),
    # --- Ещё в инвойсе, на этих скринах не было ---
    dict(
        id="blaster_y",
        group="Фильтр",
        name="BLASTER Y 12×2/12",
        art="BLASTER Y 12x2/12",
        eur=4.50,
        eur_src="invoice",
        kg=0.18,
        dealer=1250,
        shelf_vat=5,
        stock="сайт",
        base_qty=1100,
        in_invoice=True,
        on_shelf=True,
        url="https://www.digitronicgas.ru/catalog/d/filtr_razbornyy_tsentrobezhnyy_blaster_y_12_x_2_12/",
        note="В инвойсе и на сайте Digitronic; в присланных скринах не было.",
    ),
    dict(
        id="fly",
        group="Фильтр",
        name="FLY 12 / 2×12",
        art="FL01Y 12/12",
        eur=2.00,
        eur_src="invoice",
        kg=0.10,
        dealer=440,
        shelf_vat=5,
        stock="сайт",
        base_qty=2000,
        in_invoice=True,
        on_shelf=True,
        url="https://www.digitronicgas.ru/catalog/d/filtr_nizkogo_davleniya_nerazbornyy_fly_12_2x12/",
        note="В инвойсе. Dedicated слабо; в миксе без него.",
    ),
]

VOLUME_FACTORS = [
    ("−50%", 0.50),
    ("−30%", 0.70),
    ("BASE", 1.00),
    ("+30%", 1.30),
    ("+50%", 1.50),
]

# Полевые заметки из WhatsApp аудио 25.09 и 27.09
FIELD = {
    "a25": (
        "25.09: доехал до установщика ГБО. Говорит ходовые позиции — до ~500 шт/мес "
        "микс. Китай есть, оригинал/Digitronic/Польша — дефицит. Берут дешевле, чем "
        "написано на сайте Digitronic."
    ),
    "a27": (
        "27.09: Марат дал 3 контакта — все заинтересованы. Доехал до одного сервиса "
        "(~4 бокса, очередь машин, ажиотаж). Оригинал редко в наличии — вопрос не цены. "
        "Когда появляется — берут на 20–30% дешевле полки Digitronic. По сайту ткнул "
        "позиции «берут до хера» (~100 шт отдельных). Остальных — на пн/вт."
    ),
    "sell_discount": 0.25,  # рынок установщиков ≈ −25% от полки
}


def verdict_of(m_pct: float) -> str:
    if m_pct >= 40:
        return "выгодно"
    if m_pct >= 20:
        return "норм"
    if m_pct >= 0:
        return "слабо"
    return "в минус"


def rnd(v):
    return round(v, 2) if isinstance(v, float) else v


def enrich(r: dict, dealer: int, sell_market: int | None = None) -> dict:
    m_cash = (dealer - r["ep"]) * r["qty"]
    m_cash_pct = (dealer - r["ep"]) / r["ep"] * 100
    m_osno = (dealer - r["ep_ex_vat"]) * r["qty"]
    m_osno_pct = (dealer - r["ep_ex_vat"]) / r["ep_ex_vat"] * 100
    out = {
        **{k: rnd(v) for k, v in r.items()},
        "ep": round(r["ep"]),
        "ep_ex_vat": round(r["ep_ex_vat"]),
        "buy_unit_rub": round(r["buy_unit_rub"]),
        "m_cash": round(m_cash),
        "m_cash_pct": round(m_cash_pct, 1),
        "m_osno": round(m_osno),
        "m_osno_pct": round(m_osno_pct, 1),
        "verdict": verdict_of(m_cash_pct),
    }
    if sell_market is not None:
        mm = (sell_market - r["ep"]) * r["qty"]
        mm_pct = (sell_market - r["ep"]) / r["ep"] * 100
        out["sell_market"] = sell_market
        out["m_mkt"] = round(mm)
        out["m_mkt_pct"] = round(mm_pct, 1)
        out["verdict_mkt"] = verdict_of(mm_pct)
    return out


def trip_from_lines(by_id: dict, lines: list[tuple[str, int]], meta: dict) -> dict:
    items = []
    for sid, qty in lines:
        s = by_id[sid]
        if s.get("eur") is None:
            raise ValueError(f"no eur for {sid}")
        items.append((s, qty))
    goods_eur = sum(s["eur"] * q for s, q in items)
    goods_rub = goods_eur * EUR
    weight = sum(s["kg"] * q for s, q in items)
    log_eur = logistics_eur(weight)
    log_rub = log_eur * EUR
    buyout_eur = BUYOUT_EUR if goods_eur < 15000 else goods_eur * 0.05
    buyout_rub = buyout_eur * EUR
    ts = goods_rub + log_rub
    duty = ts * DUTY
    vat = (ts + duty) * VAT_IMPORT
    fee = fts_fee(ts)
    fixed = BROKER + fee + KAZAN
    partner = buyout_rub + log_rub
    customs = duty + vat + fixed
    landed = goods_rub + partner + customs
    shelf = sum(s["dealer"] * q for s, q in items)
    market = sum(round(s["dealer"] * (1 - FIELD["sell_discount"])) * q for s, q in items)
    lines_out = []
    profit_cash = 0.0
    profit_osno = 0.0
    profit_mkt = 0.0
    for s, q in items:
        share = (s["eur"] * q) / goods_eur
        part_landed = landed * share
        part_vat = vat * share
        ep = part_landed / q
        ep_ex = (part_landed - part_vat) / q
        mc = (s["dealer"] - ep) * q
        mo = (s["dealer"] - ep_ex) * q
        sm = round(s["dealer"] * (1 - FIELD["sell_discount"]))
        mm = (sm - ep) * q
        profit_cash += mc
        profit_osno += mo
        profit_mkt += mm
        lines_out.append(
            dict(
                id=s["id"],
                name=s["name"],
                group=s["group"],
                qty=q,
                eur=s["eur"],
                eur_src=s["eur_src"],
                dealer=s["dealer"],
                sell_market=sm,
                ep=round(ep),
                ep_ex_vat=round(ep_ex),
                m_cash=round(mc),
                m_osno=round(mo),
                m_mkt=round(mm),
                m_cash_pct=round((s["dealer"] - ep) / ep * 100, 1),
                m_mkt_pct=round((sm - ep) / ep * 100, 1),
                verdict=verdict_of((s["dealer"] - ep) / ep * 100),
            )
        )
    return dict(
        **meta,
        goods_eur=round(goods_eur, 2),
        goods_rub=round(goods_rub, 2),
        weight=round(weight, 2),
        log_eur=round(log_eur, 2),
        log_rub=round(log_rub, 2),
        buyout_rub=round(buyout_rub, 2),
        partner=round(partner, 2),
        duty=round(duty, 2),
        vat=round(vat, 2),
        fee=fee,
        fixed=fixed,
        customs=round(customs, 2),
        landed=round(landed, 2),
        capital=round(landed, 2),
        shelf=shelf,
        market=market,
        m_cash=round(profit_cash),
        m_osno=round(profit_osno),
        m_mkt=round(profit_mkt),
        m_cash_pct=round(profit_cash / landed * 100, 1),
        m_osno_pct=round(profit_osno / (landed - vat) * 100, 1),
        m_mkt_pct=round(profit_mkt / landed * 100, 1),
        verdict=verdict_of(profit_cash / landed * 100),
        verdict_mkt=verdict_of(profit_mkt / landed * 100),
        lines=lines_out,
    )


def build_data():
    by_id = {s["id"]: s for s in SKUS}
    priced = [s for s in SKUS if s.get("eur") is not None]
    skus_out = []
    for s in SKUS:
        sell_mkt = round(s["dealer"] * (1 - FIELD["sell_discount"]))
        if s.get("eur") is None:
            skus_out.append(
                {
                    **s,
                    "sell_market": sell_mkt,
                    "volumes": [],
                    "base": None,
                    "calcable": False,
                }
            )
            continue
        volumes = []
        for label, factor in VOLUME_FACTORS:
            qty = max(1, int(round(s["base_qty"] * factor)))
            volumes.append(
                {
                    "label": label,
                    "factor": factor,
                    **enrich(calc(s["eur"], qty, s["kg"]), s["dealer"], sell_mkt),
                }
            )
        base = next(v for v in volumes if v["label"] == "BASE")
        skus_out.append({**s, "sell_market": sell_mkt, "volumes": volumes, "base": base, "calcable": True})

    trips = []

    # Solo: только calcable + в наличии (или сайт)
    for s in priced:
        if s["stock"] == "нет":
            continue
        trips.append(
            trip_from_lines(
                by_id,
                [(s["id"], s["base_qty"])],
                dict(
                    id=f"solo_{s['id']}",
                    kind="solo",
                    title=f"Отдельно · {s['name']}",
                    blurb=f"Только этот SKU, qty BASE {s['base_qty']}. Источник €: {s['eur_src']}.",
                ),
            )
        )

    # Комбо: ходовой микс со скринов (в наличии) — то, что ткнул установщик
    trips.append(
        trip_from_lines(
            by_id,
            [
                ("mp32", 40),
                ("mp48", 30),
                ("mp48_obd", 20),
                ("nordic", 40),
                ("nordic_xp", 30),
                ("at13", 25),
                ("mv_315", 40),
                ("mv_vzu", 40),
                ("aeb_rail", 30),
                ("type33", 30),
                ("blaster", 200),
                ("fls", 400),
            ],
            dict(
                id="screen_hot",
                kind="combo",
                title="Ходовой микс со скринов (~½ месяца сервиса)",
                blurb="Электроника + редукторы + мультиклапаны + рейки + фильтры. "
                "Ориентир на «берут до хера» из аудио 27.09. OOS iQ/Maxi не включены.",
            ),
        )
    )

    trips.append(
        trip_from_lines(
            by_id,
            [
                ("mp48", 50),
                ("mp48_obd", 30),
                ("mp32", 50),
                ("nordic_xp", 40),
                ("at13", 40),
                ("blaster", 300),
                ("fls", 500),
            ],
            dict(
                id="electronics_heavy",
                kind="combo",
                title="Электроника + сильные редукторы + расходники",
                blurb="Упор на комплекты MP (в наличии на Digitronic) + AT13/XP + фильтры.",
            ),
        )
    )

    trips.append(
        trip_from_lines(
            by_id,
            [("blaster_y", 800), ("nordic_xp", 60), ("at13", 80)],
            dict(
                id="top3_invoice",
                kind="combo",
                title="Топ-3 инвойс · Y 800 + Nordic XP 60 + AT13 80",
                blurb="Старый сильный комплект только из AutoChill-инвойса (точные €).",
            ),
        )
    )

    trips.append(
        trip_from_lines(
            by_id,
            [("nordic", 80), ("nordic_xp", 60), ("at13", 50), ("mv_315", 60), ("mv_vzu", 60)],
            dict(
                id="mech_mix",
                kind="combo",
                title="Механика · редукторы + мультиклапаны",
                blurb="Без электроники. Высокий чек, медленнее оборот фильтров.",
            ),
        )
    )

    trips.append(
        trip_from_lines(
            by_id,
            [("blaster_y", 600), ("blaster", 400), ("fls", 800), ("nordic", 60), ("nordic_xp", 50), ("at13", 50)],
            dict(
                id="invoice_no_fly",
                kind="combo",
                title="Инвойс широкий без FLY",
                blurb="Все точные € из AutoChill, FLY выкинут.",
            ),
        )
    )

    # Полный «месяц сервиса» ~500 шт микс (аудио 25.09)
    trips.append(
        trip_from_lines(
            by_id,
            [
                ("mp32", 60),
                ("mp48", 50),
                ("mp48_obd", 40),
                ("nordic", 60),
                ("nordic_xp", 50),
                ("at13", 40),
                ("mv_315", 50),
                ("mv_vzu", 50),
                ("aeb_rail", 40),
                ("type33", 40),
                ("tp6", 10),
                ("tp8", 8),
                ("blaster", 400),
                ("fls", 600),
                ("blaster_y", 200),
            ],
            dict(
                id="month_500",
                kind="combo",
                title="Месяц сервиса · ~500+ шт микс",
                blurb="Ориентир аудио 25.09 «до 500 шт/мес разных». Крупный рейс.",
            ),
        )
    )

    catalog = []
    for s in skus_out:
        catalog.append(
            dict(
                id=s["id"],
                group=s["group"],
                name=s["name"],
                art=s["art"],
                dealer=s["dealer"],
                shelf_vat=s["shelf_vat"],
                stock=s["stock"],
                eur=s.get("eur"),
                eur_src=s["eur_src"],
                in_invoice=s["in_invoice"],
                on_shelf=s["on_shelf"],
                sell_market=s["sell_market"],
                calcable=s["calcable"],
                note=s["note"],
            )
        )

    return {
        "eur": EUR,
        "pln_eur": PLN_EUR,
        "date": DATE,
        "note_capital": "Аванс → оплата товара с аванса. Касса = landed один раз. Двойной оплаты товара нет.",
        "field": FIELD,
        "catalog": catalog,
        "skus": skus_out,
        "trips": trips,
    }


# ---------- formatting / HTML ----------

def r(n, d=0):
    n = float(n)
    return f"{n:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", " ")


def k(n):
    sign = "+" if n >= 0 else ""
    return sign + r(n / 1000, 0) + "k"


def vclass(verdict: str) -> str:
    return {
        "выгодно": "good",
        "норм": "ok",
        "слабо": "weak",
        "в минус": "bad",
    }.get(verdict, "")


def src_label(src: str) -> str:
    return {
        "invoice": "инвойс AutoChill",
        "pl_proxy": "PL-прокси",
        "none": "нет €",
    }.get(src, src)


def render(data: dict) -> str:
    calcable = [s for s in data["skus"] if s.get("calcable") and s.get("base")]
    skus = sorted(calcable, key=lambda s: s["base"]["m_cash_pct"], reverse=True)
    solos = [t for t in data["trips"] if t["kind"] == "solo"]
    combos = [t for t in data["trips"] if t["kind"] == "combo"]
    oos = [s for s in data["skus"] if s["stock"] == "нет"]

    cat_rows = ""
    for c in data["catalog"]:
        eur_s = f"{c['eur']:.2f} €" if c["eur"] is not None else "—"
        stock_cls = "bad" if c["stock"] == "нет" else "good"
        cat_rows += f"""<tr>
          <td><b>{c["name"]}</b><div class="muted tiny">{c["group"]} · {c["art"]}</div></td>
          <td class="num">{r(c["dealer"])}<div class="muted tiny">НДС {c["shelf_vat"]}%</div></td>
          <td class="{stock_cls}">{c["stock"]}</td>
          <td class="num">{eur_s}<div class="muted tiny">{src_label(c["eur_src"])}</div></td>
          <td class="num">{r(c["sell_market"])}<div class="muted tiny">−25% полки</div></td>
          <td class="muted tiny">{c["note"]}</td>
        </tr>"""

    sku_rows = ""
    for s in skus:
        b = s["base"]
        sku_rows += f"""<tr>
          <td><a href="{s["url"]}" target="_blank" rel="noopener">{s["name"]}</a>
            <div class="muted tiny">{s["group"]} · {s["eur"]:.2f} € · {src_label(s["eur_src"])}</div></td>
          <td class="num">{r(s["dealer"])}</td>
          <td class="num">{r(s["sell_market"])}</td>
          <td class="num">{r(b["ep"])}</td>
          <td class="num {vclass(b["verdict"])}">{b["m_cash_pct"]:+.0f}%</td>
          <td class="num {vclass(b.get("verdict_mkt",""))}">{b.get("m_mkt_pct",0):+.0f}%</td>
          <td class="num">{k(b["m_cash"])}</td>
          <td class="num">{k(b.get("m_mkt",0))}</td>
          <td><span class="pill {vclass(b["verdict"])}">{b["verdict"]}</span></td>
        </tr>"""

    oos_html = "".join(
        f"<li><b>{s['name']}</b> · полка {r(s['dealer'])} ₽ · {s['art']}</li>" for s in oos
    )

    vol_sections = ""
    for s in skus:
        rows = ""
        for v in s["volumes"]:
            rows += f"""<tr>
              <td>{v["label"]}</td>
              <td class="num">{r(v["qty"])}</td>
              <td class="num">{r(v["goods_eur"],0)} €</td>
              <td class="num">{r(v["ep"])}</td>
              <td class="num {vclass(v["verdict"])}">{v["m_cash_pct"]:+.1f}%</td>
              <td class="num {vclass(v.get("verdict_mkt",""))}">{v.get("m_mkt_pct",0):+.1f}%</td>
              <td class="num">{k(v["m_cash"])}</td>
              <td class="num">{k(v.get("m_mkt",0))}</td>
              <td class="num">{r(v["landed"]/1000,0)}k</td>
            </tr>"""
        vol_sections += f"""
        <article class="card" id="{s["id"]}">
          <header>
            <div>
              <span class="tag">{s["group"]}</span>
              <h3>{s["name"]}</h3>
              <p class="lead">{s["note"]}</p>
            </div>
            <div class="right">
              <div>€ <b>{s["eur"]:.2f}</b> ({src_label(s["eur_src"])}) · полка <b>{r(s["dealer"])} ₽</b></div>
              <span class="pill {vclass(s["base"]["verdict"])}">{s["base"]["verdict"]} vs полка</span>
            </div>
          </header>
          <table>
            <thead><tr><th>Объём</th><th>шт</th><th>закуп</th><th>земля</th>
            <th>vs полка</th><th>vs рынок−25%</th><th>₽ полка</th><th>₽ рынок</th><th>касса</th></tr></thead>
            <tbody>{rows}</tbody>
          </table>
        </article>"""

    def trip_card(t):
        lines = "".join(
            f"<li><b>{x['name']}</b> ×{r(x['qty'])} · земля {r(x['ep'])} ₽ · "
            f"полка <span class='{vclass(x['verdict'])}'>{x['m_cash_pct']:+.0f}%</span> · "
            f"рынок {x['m_mkt_pct']:+.0f}% · {k(x['m_cash'])}</li>"
            for x in t["lines"]
        )
        return f"""
        <article class="card trip">
          <header>
            <div>
              <h3>{t["title"]}</h3>
              <p class="lead">{t["blurb"]}</p>
            </div>
            <span class="pill {vclass(t["verdict"])}">{t["verdict"]} vs полка</span>
          </header>
          <div class="grid4">
            <div><small>Закуп</small><b>{r(t["goods_eur"],0)} € · {r(t["goods_rub"]/1000,0)}k</b></div>
            <div><small>Логистика</small><b>{r(t["log_eur"],0)} € · {r(t["weight"],0)} кг</b></div>
            <div><small>Касса</small><b>{r(t["capital"]/1000,0)}k ₽</b></div>
            <div><small>НДС 22%</small><b>{r(t["vat"]/1000,0)}k ₽</b></div>
            <div><small>Полка Digitronic</small><b>{r(t["shelf"]/1000,0)}k ₽</b></div>
            <div><small>Рынок установщиков −25%</small><b>{r(t["market"]/1000,0)}k ₽</b></div>
            <div><small>Прибыль vs полка</small><b class="good">{k(t["m_cash"])} · {t["m_cash_pct"]:+.0f}%</b></div>
            <div><small>Прибыль vs рынок</small><b class="{vclass(t["verdict_mkt"])}">{k(t["m_mkt"])} · {t["m_mkt_pct"]:+.0f}%</b></div>
          </div>
          <ul class="lines">{lines}</ul>
        </article>"""

    solo_html = "".join(trip_card(t) for t in sorted(solos, key=lambda x: -x["m_cash_pct"]))
    combo_html = "".join(trip_card(t) for t in combos)

    best = skus[0]
    weak = [s for s in skus if s["base"]["verdict"] in ("слабо", "в минус")]
    weak_names = ", ".join(s["name"] for s in weak) or "—"
    best_mkt = max(skus, key=lambda s: s["base"].get("m_mkt_pct", -999))

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>GBO · скрины Digitronic + поле</title>
<style>
  :root {{
    --bg:#0c1016; --card:#141a22; --line:#273041; --text:#e8eef7; --muted:#8b97a8;
    --good:#34d399; --ok:#fbbf24; --weak:#fb923c; --bad:#f87171; --link:#93c5fd;
  }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; font:15px/1.45 "IBM Plex Sans", ui-sans-serif, system-ui, sans-serif; background:var(--bg); color:var(--text); }}
  .wrap {{ max-width:1080px; margin:0 auto; padding:22px 14px 72px; }}
  h1 {{ font-size:clamp(22px,4.5vw,30px); letter-spacing:-.03em; margin:0 0 8px; }}
  h2 {{ font-size:13px; text-transform:uppercase; letter-spacing:.08em; color:var(--muted); margin:28px 0 12px; }}
  h3 {{ font-size:17px; margin:0 0 4px; }}
  p, .lead {{ color:var(--muted); margin:0; }}
  a {{ color:var(--link); text-decoration:none; }}
  .hero {{ background:linear-gradient(160deg,#152033,#10161f 55%,#0c1016); border:1px solid var(--line); border-radius:14px; padding:16px 16px 14px; margin-bottom:18px; }}
  .hero .sub {{ margin-top:6px; font-size:14px; }}
  .callouts {{ display:grid; gap:8px; margin-top:12px; }}
  .callout {{ background:rgba(255,255,255,.03); border:1px solid var(--line); border-radius:10px; padding:10px 12px; font-size:13.5px; }}
  .callout b {{ color:var(--text); }}
  .card {{ background:var(--card); border:1px solid var(--line); border-radius:12px; padding:12px 12px 10px; margin-bottom:10px; }}
  .card header {{ display:flex; justify-content:space-between; gap:12px; align-items:flex-start; margin-bottom:10px; }}
  .right {{ text-align:right; font-size:12.5px; color:var(--muted); }}
  .right b {{ color:var(--text); }}
  .tag {{ display:inline-block; font-size:9px; letter-spacing:.06em; text-transform:uppercase; border:1px solid var(--line); padding:1px 5px; border-radius:3px; color:var(--muted); margin-right:6px; }}
  .pill {{ display:inline-block; font-size:11px; font-weight:650; padding:3px 8px; border-radius:999px; border:1px solid var(--line); }}
  .pill.good, .good {{ color:var(--good); }}
  .pill.ok, .ok {{ color:var(--ok); }}
  .pill.weak, .weak {{ color:var(--weak); }}
  .pill.bad, .bad {{ color:var(--bad); }}
  table {{ width:100%; border-collapse:collapse; font-size:12.5px; }}
  th, td {{ border-bottom:1px solid var(--line); padding:6px 5px; text-align:left; vertical-align:top; }}
  th {{ color:var(--muted); font-size:10px; text-transform:uppercase; letter-spacing:.04em; }}
  .num {{ text-align:right; font-variant-numeric:tabular-nums; white-space:nowrap; }}
  .muted {{ color:var(--muted); }}
  .tiny {{ font-size:11px; }}
  .grid4 {{ display:grid; grid-template-columns:repeat(2,1fr); gap:8px; margin-bottom:8px; }}
  .grid4 div {{ background:#0e131a; border:1px solid var(--line); border-radius:8px; padding:8px 9px; }}
  .grid4 small {{ display:block; color:var(--muted); font-size:10px; text-transform:uppercase; letter-spacing:.04em; margin-bottom:2px; }}
  .grid4 b {{ font-size:13px; }}
  ul.lines {{ margin:6px 0 0; padding-left:18px; color:var(--muted); font-size:12.5px; }}
  ul.lines b {{ color:var(--text); }}
  .scroll {{ overflow-x:auto; }}
  footer {{ margin-top:28px; color:var(--muted); font-size:12px; }}
  @media (min-width:720px) {{
    .callouts {{ grid-template-columns:1fr 1fr; }}
    .grid4 {{ grid-template-columns:repeat(4,1fr); }}
    .card header {{ align-items:center; }}
  }}
</style>
</head>
<body>
<div class="wrap">
  <div class="hero">
    <h1>GBO · скрины Digitronic + поле</h1>
    <p class="sub">PL → Казань · EUR <b>{r(data["eur"],4)}</b> · {data["date"]} · товар из аванса, <b>без двойной заморозки</b></p>
    <div class="callouts">
      <div class="callout"><b>Касса = landed один раз.</b> {data["note_capital"]}</div>
      <div class="callout"><b>Поле 25.09:</b> {data["field"]["a25"]}</div>
      <div class="callout"><b>Поле 27.09:</b> {data["field"]["a27"]}</div>
      <div class="callout"><b>Vs полка:</b> {best["name"]} {best["base"]["m_cash_pct"]:+.0f}%. <b>Vs рынок −25%:</b> {best_mkt["name"]} {best_mkt["base"].get("m_mkt_pct",0):+.0f}%. Слабые vs полка: {weak_names}.</div>
    </div>
  </div>

  <h2>1. Каталог со скринов Digitronic</h2>
  <div class="card">
    <p class="lead" style="margin-bottom:10px">
      Все позиции с присланных скринов + 2 фильтра из инвойса (Y, FLY), которых на скринах не было.
      Закуп: <b>инвойс AutoChill</b> где есть; иначе <b>PL-прокси</b> (нетто zł / {data["pln_eur"]} × 0,94).
      Рынок установщиков = полка −25% (аудио).
    </p>
    <div class="scroll">
      <table>
        <thead>
          <tr>
            <th>SKU</th><th>полка ₽</th><th>наличие</th><th>закуп €</th><th>рынок −25%</th><th>заметка</th>
          </tr>
        </thead>
        <tbody>{cat_rows}</tbody>
      </table>
    </div>
  </div>

  <h2>2. Нет в наличии на Digitronic (со скринов)</h2>
  <div class="card">
    <p class="lead" style="margin-bottom:8px">Установщик говорил: оригинал редко есть. Эти позиции уже OOS на полке — спрос/дыра.</p>
    <ul class="lines">{oos_html}</ul>
  </div>

  <h2>3. Маржа: земля vs полка vs рынок −25%</h2>
  <div class="card">
    <p class="lead" style="margin-bottom:10px">Только позиции с ценой закупки. «Vs полка» — если продавать по Digitronic; «vs рынок» — если как установщики (−25%).</p>
    <div class="scroll">
      <table>
        <thead>
          <tr>
            <th>SKU</th><th>полка</th><th>рынок</th><th>земля</th>
            <th>vs полка</th><th>vs рынок</th><th>₽ полка</th><th>₽ рынок</th><th></th>
          </tr>
        </thead>
        <tbody>{sku_rows}</tbody>
      </table>
    </div>
  </div>

  <h2>4. Компоновки рейса</h2>
  {combo_html}

  <h2>5. Каждый SKU отдельно</h2>
  {solo_html}

  <h2>6. Объёмы</h2>
  {vol_sections}

  <h2>7. Как читать</h2>
  <div class="card">
    <table>
      <tbody>
        <tr><td>Инвойс AutoChill</td><td class="muted">точные €: редукторы + BLASTER/FLS/Y/FLY</td></tr>
        <tr><td>PL-прокси</td><td class="muted">польский опт нетто → EUR×0,94 (калибровка Nordic). Уточнить у AutoChill перед заказом</td></tr>
        <tr><td>Рынок −25%</td><td class="muted">аудио 27.09: берут на 20–30% дешевле полки Digitronic</td></tr>
        <tr><td>Касса</td><td class="muted">landed один раз: товар + выкуп + фрахт + пошлина + НДС 22% + фиксы</td></tr>
      </tbody>
    </table>
  </div>

  <footer>
    Пересчёт `{DATE}` · `python3 build.py` · data.json · index.html · аудио 25.09 + 27.09
  </footer>
</div>
</body>
</html>
"""


def write_variants_md(data: dict) -> str:
    calcable = [s for s in data["skus"] if s.get("calcable") and s.get("base")]
    skus = sorted(calcable, key=lambda s: s["base"]["m_cash_pct"], reverse=True)
    combos = [t for t in data["trips"] if t["kind"] == "combo"]
    lines = [
        "# GBO — скрины Digitronic + поле",
        "",
        f"Дата **{data['date']}**, EUR **{data['eur']:.4f}**.",
        "",
        "## Поле (WhatsApp)",
        "",
        f"- {data['field']['a25']}",
        f"- {data['field']['a27']}",
        "",
        "## Каталог со скринов",
        "",
        "| SKU | арт | полка ₽ | наличие | € | источник | рынок −25% |",
        "|---|---|---:|---|---:|---|---:|",
    ]
    for c in data["catalog"]:
        eur = f"{c['eur']:.2f}" if c["eur"] is not None else "—"
        lines.append(
            f"| {c['name']} | {c['art']} | {c['dealer']} | {c['stock']} | {eur} | {c['eur_src']} | {c['sell_market']} |"
        )
    lines += [
        "",
        "## Маржа BASE (с €)",
        "",
        "| SKU | € | полка | земля | vs полка | vs рынок | вердикт |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for s in skus:
        b = s["base"]
        lines.append(
            f"| {s['name']} | {s['eur']:.2f} | {s['dealer']} | {b['ep']} | {b['m_cash_pct']:+.0f}% | {b.get('m_mkt_pct',0):+.0f}% | **{b['verdict']}** |"
        )
    lines += ["", "## Компоновки", ""]
    for t in combos:
        lines += [
            f"### {t['title']}",
            "",
            f"- {t['blurb']}",
            f"- Закуп **{t['goods_eur']:,.0f} €** · касса **{t['capital']/1000:.0f}k ₽**".replace(",", " "),
            f"- Vs полка **{t['m_cash']/1000:+.0f}k ({t['m_cash_pct']:+.0f}%)** · vs рынок **{t['m_mkt']/1000:+.0f}k ({t['m_mkt_pct']:+.0f}%)** · **{t['verdict']}**",
            "",
        ]
    lines += [
        "## Рекомендация",
        "",
        "1. **Ходовой микс со скринов** или **электроника+редукторы** — под спрос установщиков.",
        "2. Точные € только у инвойса (редукторы/фильтры) — их возить смело.",
        "3. MP32/MP48/OBD — PL-прокси; перед заказом запросить € у AutoChill.",
        "4. iQ / Maxi-2 — OOS на полке; без цены закупки не закладывать в рейс.",
        "5. Продавать ориентир рынок −20…30% от Digitronic, не полка.",
        "",
    ]
    return "\n".join(lines)


def main():
    data = build_data()
    (ROOT / "data.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    (ROOT / "index.html").write_text(render(data), encoding="utf-8")
    (ROOT / "VARIANTS.md").write_text(write_variants_md(data), encoding="utf-8")
    # transcripts
    audio_dir = Path("/tmp/gbo-audio")
    if audio_dir.exists():
        notes = ROOT / "FIELD_NOTES.md"
        a25 = (audio_dir / "a25.txt").read_text(encoding="utf-8") if (audio_dir / "a25.txt").exists() else ""
        a27 = (audio_dir / "a27.txt").read_text(encoding="utf-8") if (audio_dir / "a27.txt").exists() else ""
        notes.write_text(
            "# Полевые заметки · WhatsApp аудио\n\n"
            "## 25.09.2026\n\n" + a25.strip() + "\n\n"
            "## 27.09.2026\n\n" + a27.strip() + "\n",
            encoding="utf-8",
        )
    print("CATALOG")
    for c in data["catalog"]:
        eur = f"{c['eur']:.2f}€" if c["eur"] is not None else "—"
        print(f"  {c['stock']:<6} {c['name']:<34} {c['dealer']:>6}₽  {eur:>8}  {c['eur_src']}")
    print("\nMARGIN BASE (calcable)")
    for s in sorted([x for x in data["skus"] if x.get("base")], key=lambda x: -x["base"]["m_cash_pct"]):
        b = s["base"]
        print(
            f"  {s['name']:<34} ep={b['ep']:>5}  полка {b['m_cash_pct']:+6.1f}%  "
            f"рынок {b.get('m_mkt_pct',0):+6.1f}%  {b['verdict']}"
        )
    print("\nCOMBOS")
    for t in data["trips"]:
        if t["kind"] != "combo":
            continue
        print(
            f"  {t['id']:<18} полка {t['m_cash']/1000:+7.0f}k ({t['m_cash_pct']:+5.1f}%)  "
            f"рынок {t['m_mkt']/1000:+7.0f}k ({t['m_mkt_pct']:+5.1f}%)  cash={t['capital']/1000:6.0f}k"
        )


if __name__ == "__main__":
    main()
