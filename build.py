#!/usr/bin/env python3
"""GBO поставка PL→RU — пересчёт landed / freeze / маржа + варианты рейса."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EUR = 94.8810  # ЦБ РФ ~01.10.2026 (cbr-xml-daily)
DATE = "01.10.2026"
BUYOUT_EUR = 750
BROKER = 25000
KAZAN = 12000
DUTY = 0.05
VAT_IMPORT = 0.22  # ввозная ставка по 8708, не 5% с ценника Digitronic


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


def calc(eur_unit: float, qty: int, kg_unit: float) -> dict:
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
    landed = goods_rub + buyout_rub + log_rub + duty + vat + fixed
    ekaterina = goods_rub + buyout_rub + log_rub
    customs = duty + vat + fixed
    freeze = goods_rub + ekaterina + customs
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
        duty=duty,
        vat=vat,
        fee=fee,
        fixed=fixed,
        ekaterina=ekaterina,
        customs=customs,
        landed=landed,
        freeze=freeze,
        ep=ep,
        ep_ex_vat=ep_ex_vat,
        buy_unit_rub=eur_unit * EUR,
    )


SKUS = [
    dict(
        id="blaster_y",
        group="Фильтр",
        name="BLASTER Y 12×2/12",
        art="BLASTER Y 12x2/12",
        eur=4.50,
        kg=0.18,
        dealer=1250,
        base_qty=1100,
        url="https://www.digitronicgas.ru/catalog/d/filtr_razbornyy_tsentrobezhnyy_blaster_y_12_x_2_12/",
        note="Главный по марже к полке среди фильтров. Разборный расходник, меняют каждые 10–15 тыс. км.",
    ),
    dict(
        id="blaster",
        group="Фильтр",
        name="BLASTER 12×12",
        art="BLASTER 12х12",
        eur=3.50,
        kg=0.15,
        dealer=880,
        base_qty=1400,
        url="https://www.digitronicgas.ru/catalog/d/filtr_razbornyy_tsentrobezhnyy_blaster_12_x12/",
        note="Разборный центробежный. Слабее BLASTER Y, но тоже расходник.",
    ),
    dict(
        id="fly",
        group="Фильтр",
        name="FLY 12 / 2×12",
        art="FL01Y 12/12",
        eur=2.00,
        kg=0.10,
        dealer=440,
        base_qty=2000,
        url="https://www.digitronicgas.ru/catalog/d/filtr_nizkogo_davleniya_nerazbornyy_fly_12_2x12/",
        note="Y-образный неразборный. На dedicated-кубе маржа к полке тонкая.",
    ),
    dict(
        id="fls",
        group="Фильтр",
        name="FLS 12×12",
        art="FL01S 12/12",
        eur=0.70,
        kg=0.08,
        dealer=250,
        base_qty=2500,
        url="https://www.digitronicgas.ru/catalog/d/filtr_nizkogo_davleniya_nerazbornyy_fls_12x12_mm/",
        note="Самый ходовой расходник. Фиксы сильно бьют по штуке на малой партии.",
    ),
    dict(
        id="nordic",
        group="Редуктор",
        name="AT09 Nordic",
        art="RGDG3890",
        eur=26.0,
        kg=1.30,
        dealer=7000,  # Digitronic 01.10.2026 (было 6150)
        base_qty=200,
        url="https://www.digitronicgas.ru/catalog/d/reduktor_tomasetto_at09_nordic/",
        note="Хит 4-го поколения до ~170 л.с. Не расходник. Полка выросла до 7 000 ₽.",
    ),
    dict(
        id="nordic_xp",
        group="Редуктор",
        name="AT09 Nordic XP",
        art="RGDG3895",
        eur=34.0,
        kg=1.40,
        dealer=9200,  # Digitronic 01.10.2026 (было 8250)
        base_qty=180,
        url="https://www.digitronicgas.ru/catalog/d/reduktor_tomasetto_at09_nordic_xp_do_250_l_s/",
        note="До 250 л.с. Живая цена Digitronic 9 200 ₽.",
    ),
    dict(
        id="at13",
        group="Редуктор",
        name="AT13 XP",
        art="RGDG3990",
        eur=46.0,
        kg=1.60,
        dealer=12800,  # Digitronic 01.10.2026 (было 11600)
        base_qty=150,
        url="https://www.digitronicgas.ru/catalog/d/reduktor_tomasetto_at13_xp/",
        note="Под мощные авто. Лучшая маржа среди редукторов. Полка 12 800 ₽.",
    ),
]

SCENARIOS = [("BASE", 1.00), ("−30%", 0.70), ("−50%", 0.50)]

# Конкретные варианты первого рейса (смешанные кубы)
TRIP_VARIANTS = [
    dict(
        id="A",
        title="A · только BLASTER Y",
        verdict="GO · лучший простой старт по фильтрам",
        lines=[("blaster_y", 1100)],
    ),
    dict(
        id="B",
        title="B · только AT13 XP",
        verdict="GO · максимум ₽/рейс и маржа, медленнее оборот",
        lines=[("at13", 150)],
    ),
    dict(
        id="C",
        title="C · MIX BLASTER Y 800 + AT13 80",
        verdict="РЕКОМЕНДУЮ · расходник + дорогой чек в одном рейсе",
        lines=[("blaster_y", 800), ("at13", 80)],
    ),
    dict(
        id="D",
        title="D · MIX BLASTER Y 700 + Nordic XP 60 + AT13 40",
        verdict="GO · шире ассортимент, чуть ниже маржа чем C",
        lines=[("blaster_y", 700), ("nordic_xp", 60), ("at13", 40)],
    ),
    dict(
        id="E",
        title="E · filters mix Y 900 + BLASTER 500 + FLS 1000",
        verdict="OK · объём расходников, без редукторов",
        lines=[("blaster_y", 900), ("blaster", 500), ("fls", 1000)],
    ),
    dict(
        id="A30",
        title="A−30% · BLASTER Y 770",
        verdict="GO soft · меньше заморозка, EP хуже",
        lines=[("blaster_y", 770)],
    ),
]


def rnd(v):
    return round(v, 2) if isinstance(v, float) else v


def build_data():
    by_id = {s["id"]: s for s in SKUS}
    out = []
    for s in SKUS:
        scenarios = []
        for label, factor in SCENARIOS:
            qty = max(1, int(round(s["base_qty"] * factor)))
            r = calc(s["eur"], qty, s["kg"])
            dealer = s["dealer"]
            m = (dealer - r["ep"]) * qty
            mp = (dealer - r["ep"]) / r["ep"] * 100
            m_osno = (dealer - r["ep_ex_vat"]) * qty
            mp_osno = (dealer - r["ep_ex_vat"]) / r["ep_ex_vat"] * 100
            scenarios.append(
                {
                    "label": label,
                    "factor": factor,
                    **{k: rnd(v) for k, v in r.items()},
                    "ep": round(r["ep"]),
                    "ep_ex_vat": round(r["ep_ex_vat"]),
                    "buy_unit_rub": round(r["buy_unit_rub"]),
                    "m_shelf": round(m),
                    "m_shelf_pct": round(mp, 1),
                    "m_osno": round(m_osno),
                    "m_osno_pct": round(mp_osno, 1),
                }
            )
        base_ep = next(x["ep"] for x in scenarios if x["label"] == "BASE")
        m50_ep = next(x["ep"] for x in scenarios if x["label"] == "−50%")
        assert m50_ep > base_ep, (s["name"], base_ep, m50_ep)
        out.append({**s, "scenarios": scenarios})

    trips = []
    for tv in TRIP_VARIANTS:
        items = []
        for sid, qty in tv["lines"]:
            s = by_id[sid]
            items.append((s["name"], s["eur"], s["kg"], s["dealer"], qty, sid))
        goods_eur = sum(e * q for _, e, _, _, q, _ in items)
        goods_rub = goods_eur * EUR
        weight = sum(kg * q for _, _, kg, _, q, _ in items)
        log_eur = logistics_eur(weight)
        log_rub = log_eur * EUR
        buyout_eur = BUYOUT_EUR if goods_eur < 15000 else goods_eur * 0.05
        buyout_rub = buyout_eur * EUR
        ts = goods_rub + log_rub
        duty = ts * DUTY
        vat = (ts + duty) * VAT_IMPORT
        fee = fts_fee(ts)
        fixed = BROKER + fee + KAZAN
        landed = goods_rub + buyout_rub + log_rub + duty + vat + fixed
        ekaterina = goods_rub + buyout_rub + log_rub
        customs = duty + vat + fixed
        freeze = goods_rub + ekaterina + customs
        shelf = sum(d * q for *_, d, q, _ in items)
        lines_out = []
        profit_cash = 0.0
        profit_osno = 0.0
        for name, e, _kg, d, q, sid in items:
            share = (e * q) / goods_eur
            part_landed = landed * share
            part_vat = vat * share
            ep = part_landed / q
            ep_ex = (part_landed - part_vat) / q
            mc = (d - ep) * q
            mo = (d - ep_ex) * q
            profit_cash += mc
            profit_osno += mo
            lines_out.append(
                dict(
                    id=sid,
                    name=name,
                    qty=q,
                    ep=round(ep),
                    ep_ex_vat=round(ep_ex),
                    dealer=d,
                    m_cash=round(mc),
                    m_osno=round(mo),
                )
            )
        trips.append(
            dict(
                id=tv["id"],
                title=tv["title"],
                verdict=tv["verdict"],
                goods_eur=round(goods_eur, 2),
                goods_rub=round(goods_rub, 2),
                weight=round(weight, 2),
                log_eur=round(log_eur, 2),
                log_rub=round(log_rub, 2),
                buyout_rub=round(buyout_rub, 2),
                duty=round(duty, 2),
                vat=round(vat, 2),
                fee=fee,
                fixed=fixed,
                ekaterina=round(ekaterina, 2),
                customs=round(customs, 2),
                landed=round(landed, 2),
                freeze=round(freeze, 2),
                shelf=shelf,
                m_cash=round(profit_cash),
                m_osno=round(profit_osno),
                m_cash_pct=round(profit_cash / landed * 100, 1),
                m_osno_pct=round(profit_osno / (landed - vat) * 100, 1),
                lines=lines_out,
            )
        )

    return {"eur": EUR, "date": DATE, "skus": out, "trips": trips}


def r(n, d=0):
    n = float(n)
    return f"{n:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", " ")


def k(n):
    sign = "+" if n >= 0 else ""
    return sign + r(n / 1000, 0) + "k"


def scenario(s, label):
    return next(x for x in s["scenarios"] if x["label"] == label)


def unit_chart(skus):
    labels = ["BASE", "−30%", "−50%"]
    W, H, pad_l, pad_r, pad_t, pad_b = 720, 280, 52, 16, 16, 36
    inner_w, inner_h = W - pad_l - pad_r, H - pad_t - pad_b
    all_ep = [sc["ep"] for s in skus for sc in s["scenarios"]]
    ymin, ymax = min(all_ep) * 0.9, max(all_ep) * 1.08
    colors = [
        "#3b82f6",
        "#22c55e",
        "#eab308",
        "#f97316",
        "#a78bfa",
        "#06b6d4",
        "#ef4444",
    ]
    n = max(len(labels) - 1, 1)

    def x(i):
        return pad_l + (inner_w * i / n)

    def y(v):
        return pad_t + inner_h * (1 - (v - ymin) / (ymax - ymin))

    parts = [
        f'<svg viewBox="0 0 {W} {H}" class="chart" role="img" '
        f'aria-label="Себестоимость за штуку растёт при снижении объёма">'
    ]
    for t in range(5):
        val = ymin + (ymax - ymin) * t / 4
        yy = y(val)
        parts.append(
            f'<line x1="{pad_l}" y1="{yy:.1f}" x2="{W - pad_r}" y2="{yy:.1f}" stroke="#1f2937"/>'
        )
        parts.append(
            f'<text x="{pad_l - 8}" y="{yy + 4:.1f}" text-anchor="end" fill="#6b7280" font-size="11">{r(val, 0)}</text>'
        )
    for i, lab in enumerate(labels):
        parts.append(
            f'<text x="{x(i):.1f}" y="{H - 10}" text-anchor="middle" fill="#9ca3af" font-size="12">{lab}</text>'
        )
    for si, s in enumerate(skus):
        pts = []
        for i, lab in enumerate(labels):
            sc = scenario(s, lab)
            pts.append(f"{x(i):.1f},{y(sc['ep']):.1f}")
        c = colors[si % len(colors)]
        parts.append(
            f'<polyline fill="none" stroke="{c}" stroke-width="2.2" points="{" ".join(pts)}"/>'
        )
        for i, lab in enumerate(labels):
            sc = scenario(s, lab)
            parts.append(
                f'<circle cx="{x(i):.1f}" cy="{y(sc["ep"]):.1f}" r="3.2" fill="{c}"/>'
            )
    legend = '<div class="legend">'
    for si, s in enumerate(skus):
        c = colors[si % len(colors)]
        legend += f'<span><i style="background:{c}"></i>{s["name"]}</span>'
    legend += "</div>"
    return "".join(parts) + "</svg>" + legend


def mp_class(pct):
    return "bad" if pct < 0 else ("good" if pct >= 20 else "")


def mln(n):
    return f"{n / 1e6:.2f}".replace(".", ",") + " млн"


def master_cards(skus):
    cards = []
    for s in skus:
        b = scenario(s, "BASE")
        m30 = scenario(s, "−30%")
        m50 = scenario(s, "−50%")
        cls = "weak" if b["m_shelf_pct"] < 15 else ""
        cards.append(
            f"""
      <article class="scard {cls}" id="sum-{s["id"]}">
        <header class="scard-h">
          <div>
            <span class="tag">{s["group"]}</span>
            <a class="scard-name" href="#{s["id"]}">{s["name"]}</a>
          </div>
          <div class="scard-meta">
            <span>{s["eur"]:.2f} € · {r(b["buy_unit_rub"])} ₽</span>
            <a href="{s["url"]}" target="_blank" rel="noopener">полка {r(s["dealer"])} ₽</a>
          </div>
        </header>
        <div class="sgrid">
          <div class="shead"></div>
          <div class="shead">BASE</div>
          <div class="shead">−30%</div>
          <div class="shead">−50%</div>

          <div class="slabel">Земля</div>
          <div class="sval accent">{r(b["ep"])}</div>
          <div class="sval">{r(m30["ep"])}</div>
          <div class="sval">{r(m50["ep"])}</div>

          <div class="slabel">Маржа</div>
          <div class="sval {mp_class(b["m_shelf_pct"])}">{b["m_shelf_pct"]:+.0f}%</div>
          <div class="sval {mp_class(m30["m_shelf_pct"])}">{m30["m_shelf_pct"]:+.0f}%</div>
          <div class="sval {mp_class(m50["m_shelf_pct"])}">{m50["m_shelf_pct"]:+.0f}%</div>

          <div class="slabel">₽ рейса</div>
          <div class="sval">{k(b["m_shelf"])}</div>
          <div class="sval">{k(m30["m_shelf"])}</div>
          <div class="sval">{k(m50["m_shelf"])}</div>

          <div class="slabel">Заморозка</div>
          <div class="sval freeze">{mln(b["freeze"])}</div>
          <div class="sval freeze">{mln(m30["freeze"])}</div>
          <div class="sval freeze">{mln(m50["freeze"])}</div>
        </div>
      </article>"""
        )
    return "".join(cards)


def trip_cards(trips):
    cards = []
    for t in trips:
        lines = "".join(
            f"<div class='tline'><b>{x['name']}</b> ×{r(x['qty'])} · земля {r(x['ep'])} ₽ · "
            f"кэш {k(x['m_cash'])} · ОСНО {k(x['m_osno'])}</div>"
            for x in t["lines"]
        )
        cards.append(
            f"""
      <article class="tcard" id="trip-{t["id"]}">
        <header>
          <h2>{t["title"]}</h2>
          <p class="verdict">{t["verdict"]}</p>
        </header>
        <div class="tkpis">
          <div><small>Инвойс</small><b>{r(t["goods_eur"], 0)} € · {r(t["goods_rub"] / 1000, 0)}k ₽</b></div>
          <div><small>Логистика</small><b>{r(t["log_eur"], 0)} € · {r(t["weight"], 0)} кг</b></div>
          <div><small>Касса партии</small><b>{r(t["landed"] / 1000, 0)}k ₽</b></div>
          <div><small>НДС ввоз 22%</small><b>{r(t["vat"] / 1000, 0)}k ₽</b></div>
          <div><small>Заморозка</small><b class="freeze">{mln(t["freeze"])}</b></div>
          <div><small>Прибыль к полке</small><b class="good">{k(t["m_cash"])} · {t["m_cash_pct"]:+.0f}%</b></div>
          <div><small>Если НДС к вычету (ОСНО)</small><b class="good">{k(t["m_osno"])} · {t["m_osno_pct"]:+.0f}%</b></div>
          <div><small>Полка Digitronic</small><b>{r(t["shelf"] / 1000, 0)}k ₽</b></div>
        </div>
        <div class="tlines">{lines}</div>
      </article>"""
        )
    return "".join(cards)


def sku_section(s, eur):
    b = scenario(s, "BASE")
    rows_sc = ""
    for lab in ["BASE", "−30%", "−50%"]:
        sc = scenario(s, lab)
        mpcls = "bad" if sc["m_shelf_pct"] < 0 else "good"
        rows_sc += f"""<tr>
          <td>{lab}</td>
          <td class="num">{r(sc["qty"])}</td>
          <td class="num">{r(sc["weight"], 0)}</td>
          <td class="num">{r(sc["goods_eur"], 0)} €</td>
          <td class="num">{r(sc["ep"])} ₽</td>
          <td class="num freeze">{r(sc["freeze"])} ₽</td>
          <td class="num">{r(sc["landed"])} ₽</td>
          <td class="num {mpcls}">{sc["m_shelf_pct"]:+.1f}%</td>
          <td class="num">{k(sc["m_shelf"])}</td>
        </tr>"""
    stages = [
        (
            "1. Закупка по инвойсу AutoChill (netto)",
            b["buy_unit_rub"],
            f"{s['eur']:.2f} € × {r(eur, 4)} ₽",
        ),
        ("2. + доля выкупа 750 €", round(b["buyout_rub"] / b["qty"]), "фикс на партию"),
        (
            "3. + доля логистики PL→МСК",
            round(b["log_rub"] / b["qty"]),
            f"{r(b['log_eur'], 0)} € на {r(b['weight'], 0)} кг",
        ),
        ("4. + пошлина 5%", round(b["duty"] / b["qty"]), "от (товар + фрахт)"),
        (
            "5. + НДС ввоз 22%",
            round(b["vat"] / b["qty"]),
            "таможня, не 5% с ценника Digitronic",
        ),
        (
            "6. + брокер / сбор ФТС / МСК→Казань",
            round(b["fixed"] / b["qty"]),
            "фиксы партии",
        ),
    ]
    stage_rows = ""
    cum = 0
    for name, val, note in stages:
        cum += val
        stage_rows += f"""<tr>
          <td>{name}</td>
          <td class="num">{r(val)} ₽</td>
          <td class="num muted">{r(cum)} ₽</td>
          <td class="muted">{note}</td>
        </tr>"""
    return f"""
    <section class="sku" id="{s["id"]}">
      <header>
        <div>
          <span class="tag">{s["group"]}</span>
          <h2>{s["name"]}</h2>
          <p class="lead">{s["note"]}</p>
        </div>
        <a class="dealer" href="{s["url"]}" target="_blank" rel="noopener">Полка Digitronic · {r(s["dealer"])} ₽ →</a>
      </header>
      <div class="kpis">
        <div><small>Закупка инвойс</small><b>{s["eur"]:.2f} € · {r(b["buy_unit_rub"])} ₽</b></div>
        <div><small>Земля BASE / шт</small><b>{r(b["ep"])} ₽</b></div>
        <div><small>Полка дилера (с НДС 5%)</small><b><a href="{s["url"]}" target="_blank" rel="noopener">{r(s["dealer"])} ₽</a></b></div>
        <div><small>Маржа к полке BASE</small><b class="{"bad" if b["m_shelf_pct"] < 0 else "good"}">{b["m_shelf_pct"]:+.1f}% · {k(b["m_shelf"])}</b></div>
        <div><small>Заморозка BASE</small><b>{r(b["freeze"])} ₽</b></div>
      </div>
      <h3>Стадии до земли — BASE, 1 шт</h3>
      <table>
        <thead><tr><th>Стадия</th><th>На штуку</th><th>Накопительно</th><th></th></tr></thead>
        <tbody>{stage_rows}
        <tr class="total"><td>Себестоимость в Казани (кэш, НДС 22% внутри)</td><td class="num">{r(b["ep"])} ₽</td><td></td><td>касса {r(b["landed"])} ₽ / {r(b["qty"])} шт</td></tr>
        </tbody>
      </table>
      <p class="tiny">Если юрлицо на ОСНО / УСН со ставкой 22% — ввозной НДС к вычету. Тогда экономическая земля BASE {r(b["ep_ex_vat"])} ₽/шт, маржа к полке {b["m_osno_pct"]:+.1f}%. Заморозка всё равно включает НДС до вычета.</p>
      <h3>Заморозка капитала — BASE</h3>
      <table>
        <thead><tr><th>Куда деньги</th><th>Сумма</th><th></th></tr></thead>
        <tbody>
          <tr><td>Польша: товар AutoChill</td><td class="num">{r(b["goods_rub"])} ₽</td><td class="muted">{r(b["goods_eur"], 0)} €</td></tr>
          <tr><td>РФ-партнёру: товар + 750 € + логистика</td><td class="num">{r(b["ekaterina"])} ₽</td><td class="muted">двойная оплата товара</td></tr>
          <tr><td>Таможня: пошлина + НДС 22% + брокер + Казань</td><td class="num">{r(b["customs"])} ₽</td><td></td></tr>
          <tr class="total"><td>Итого заморозка</td><td class="num">{r(b["freeze"])} ₽</td><td class="muted">товар считается дважды</td></tr>
        </tbody>
      </table>
      <h3>Объём: земля и заморозка</h3>
      <table>
        <thead><tr><th>Сценарий</th><th>Шт</th><th>Кг</th><th>Инвойс</th><th>EP / шт</th><th>Заморозка</th><th>Касса партии</th><th>Маржа к полке</th><th>₽ с рейса</th></tr></thead>
        <tbody>{rows_sc}</tbody>
      </table>
    </section>
    """


def render(data):
    skus = sorted(
        data["skus"],
        key=lambda s: scenario(s, "BASE")["m_shelf_pct"],
        reverse=True,
    )
    toc = "".join(f'<a href="#{s["id"]}">{s["name"]}</a>' for s in skus)
    sections = "\n".join(sku_section(s, data["eur"]) for s in skus)
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>GBO поставка · Польша → Казань</title>
<style>
  :root {{
    --bg:#0b0d10; --card:#12161c; --line:#222831; --text:#e8edf4; --muted:#8b95a5;
    --accent:#6ee7b7; --bad:#f87171; --link:#93c5fd; --freeze:#c4b5fd;
  }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; font:15px/1.4 "IBM Plex Sans", ui-sans-serif, system-ui, sans-serif; background:var(--bg); color:var(--text); }}
  .wrap {{ max-width:980px; margin:0 auto; padding:24px 14px 64px; }}
  h1 {{ font-size:clamp(22px,5vw,28px); letter-spacing:-.03em; margin:0 0 6px; font-weight:650; line-height:1.15; }}
  h2 {{ font-size:20px; margin:0 0 4px; font-weight:650; }}
  h3 {{ font-size:12px; text-transform:uppercase; letter-spacing:.08em; color:var(--muted); margin:22px 0 10px; font-weight:600; }}
  p, .lead {{ color:var(--muted); }}
  .sub {{ margin:0 0 16px; font-size:14px; }}
  a {{ color:var(--link); text-decoration:none; }}
  a:hover {{ text-decoration:underline; }}
  .note {{ border:1px solid var(--line); background:var(--card); padding:12px 14px; border-radius:10px; margin:12px 0 18px; font-size:13.5px; line-height:1.45; }}
  .note strong {{ color:var(--text); }}
  .tiny {{ font-size:12px; margin:8px 0 0; }}
  table {{ width:100%; border-collapse:collapse; font-size:12.5px; }}
  th, td {{ border-bottom:1px solid var(--line); padding:6px 5px; text-align:left; vertical-align:top; }}
  th {{ color:var(--muted); font-weight:600; font-size:10px; text-transform:uppercase; letter-spacing:.04em; }}
  .num {{ text-align:right; font-variant-numeric:tabular-nums; white-space:nowrap; }}
  .muted {{ color:var(--muted); }}
  .accent {{ font-weight:650; }}
  .good {{ color:var(--accent); }}
  .bad {{ color:var(--bad); }}
  .freeze {{ color:var(--freeze); font-weight:600; }}
  tr.total td {{ font-weight:650; border-bottom:none; padding-top:10px; }}
  .tag {{ display:inline-block; font-size:9px; letter-spacing:.06em; text-transform:uppercase; border:1px solid var(--line); padding:1px 5px; border-radius:3px; color:var(--muted); margin-right:6px; vertical-align:middle; }}
  .kpis {{ display:grid; grid-template-columns:repeat(2,1fr); gap:8px; margin:12px 0 8px; }}
  .kpis div {{ background:var(--card); border:1px solid var(--line); padding:10px 11px; border-radius:8px; }}
  .kpis small {{ display:block; color:var(--muted); font-size:10px; text-transform:uppercase; letter-spacing:.05em; margin-bottom:3px; }}
  .kpis b {{ font-size:14px; font-weight:650; }}
  .sku {{ margin:36px 0; padding-top:6px; border-top:1px solid var(--line); }}
  .sku header {{ display:flex; justify-content:space-between; gap:12px; align-items:flex-start; }}
  .dealer {{ border:1px solid var(--line); padding:7px 10px; border-radius:8px; white-space:nowrap; font-size:13px; }}
  .legend {{ display:flex; flex-wrap:wrap; gap:8px 14px; margin-top:8px; color:var(--muted); font-size:11px; }}
  .legend i {{ display:inline-block; width:8px; height:8px; border-radius:50%; margin-right:5px; vertical-align:middle; }}
  .chart {{ width:100%; height:auto; background:var(--card); border:1px solid var(--line); border-radius:10px; }}
  nav.toc {{ display:flex; flex-wrap:wrap; gap:6px; margin:16px 0 20px; }}
  nav.toc a {{ border:1px solid var(--line); padding:5px 9px; border-radius:999px; font-size:12px; color:var(--text); }}
  .ass {{ display:grid; grid-template-columns:1fr; gap:10px; }}
  footer {{ margin-top:28px; color:var(--muted); font-size:12px; }}
  .scards, .tcards {{ display:grid; gap:10px; }}
  .scard, .tcard {{ background:var(--card); border:1px solid var(--line); border-radius:12px; padding:10px 11px 8px; }}
  .scard.weak {{ border-color:#3a2a2a; }}
  .scard-h {{ display:flex; flex-direction:column; gap:4px; margin-bottom:8px; padding-bottom:8px; border-bottom:1px solid var(--line); }}
  .scard-name {{ color:var(--text); font-weight:650; font-size:15px; }}
  .scard-meta {{ display:flex; flex-wrap:wrap; gap:6px 12px; font-size:12px; color:var(--muted); }}
  .sgrid {{ display:grid; grid-template-columns:72px repeat(3,minmax(0,1fr)); gap:2px 4px; align-items:center; font-variant-numeric:tabular-nums; }}
  .shead {{ font-size:10px; color:var(--muted); text-align:right; text-transform:uppercase; letter-spacing:.04em; font-weight:600; padding:0 2px 4px; }}
  .shead:first-child {{ text-align:left; }}
  .slabel {{ font-size:11px; color:var(--muted); padding:3px 0; }}
  .sval {{ text-align:right; font-size:12.5px; padding:3px 2px; white-space:nowrap; }}
  .cap {{ font-size:12px; color:var(--muted); margin:8px 0 0; }}
  .verdict {{ color:var(--accent); margin:4px 0 10px; font-size:13.5px; }}
  .tkpis {{ display:grid; grid-template-columns:repeat(2,1fr); gap:8px; margin-bottom:10px; }}
  .tkpis div {{ background:#0e1218; border:1px solid var(--line); padding:8px 10px; border-radius:8px; }}
  .tkpis small {{ display:block; color:var(--muted); font-size:10px; text-transform:uppercase; letter-spacing:.05em; margin-bottom:2px; }}
  .tkpis b {{ font-size:13px; }}
  .tline {{ font-size:12.5px; color:var(--muted); padding:3px 0; border-top:1px dashed var(--line); }}
  .tline b {{ color:var(--text); }}
  @media (min-width:640px) {{
    .wrap {{ padding:32px 20px 72px; }}
    .kpis, .tkpis {{ grid-template-columns:repeat(3,1fr); }}
    .scards, .tcards {{ grid-template-columns:1fr 1fr; gap:12px; }}
  }}
  @media (min-width:900px) {{
    .kpis {{ grid-template-columns:repeat(5,1fr); }}
    .tkpis {{ grid-template-columns:repeat(4,1fr); }}
    .ass {{ grid-template-columns:1fr 1fr; }}
  }}
  @media (max-width:800px) {{
    .sku header {{ flex-direction:column; }}
    .dealer {{ white-space:normal; }}
  }}
</style>
</head>
<body>
<div class="wrap">
  <h1>GBO поставка · Польша → Казань</h1>
  <p class="sub">Фильтры и редукторы AutoChill / Tomasetto. Пересчёт {data["date"]}, EUR {r(data["eur"], 4)}. Полный ответ с вариантами рейса — в <code>VARIANTS.md</code>.</p>

  <h3>Варианты первого рейса</h3>
  <div class="tcards">
      {trip_cards(data["trips"])}
  </div>

  <h3>Сводка по SKU: земля, маржа к полке, заморозка</h3>
  <div class="scards">
      {master_cards(skus)}
  </div>
  <p class="cap">Полка — digitronicgas.ru на {data["date"]}. Заморозка = товар в PL + платёж РФ-партнёру (товар ещё раз + 750 € + логистика) + таможня. Курс ЦБ {r(data["eur"], 4)} ₽/€.</p>

  <h3>Себестоимость за штуку vs объём</h3>
  {unit_chart(skus)}
  <p>Ось Y — земля ₽/шт. Направо партия меньше — EP растёт из‑за фиксов.</p>

  <nav class="toc">{toc}</nav>
  {sections}

  <h3>Вводные</h3>
  <div class="ass">
    <div class="note">
      <strong>Деньги</strong><br/>
      EUR ЦБ {r(data["eur"], 4)} на {data["date"]}. Выкуп 750 € фикс до инвойса 15 000 €.
      Брокер 25 000 ₽. Сбор ФТС — шкала от ТС. МСК→Казань 12 000 ₽.
    </div>
    <div class="note">
      <strong>Таможня и фрахт</strong><br/>
      ТН ВЭД 8708 99 97. Пошлина 5% от (товар+фрахт). НДС ввоз 22%.
      Логистика: 162,5 + 4,75 × кг €. BASE qty — реалистичная набивка ~1 м³.
      Полка Digitronic — с НДС 5%; ввозной НДС 22% — другая ставка.
    </div>
  </div>
  <footer>
    Репозиторий GithubRavilS/gbo · проект вынесен из Private Assistant (15_gas-equipment-ru / старый gbo-investor).
    FLY на dedicated-кубе слабее остальных. Главные: BLASTER Y и AT13 XP.
  </footer>
</div>
</body>
</html>
"""


def write_variants_md(data: dict) -> str:
    lines = [
        "# GBO поставка — конкретные варианты",
        "",
        f"Пересчёт **{data['date']}**, EUR ЦБ **{data['eur']:.4f}**.",
        "Полки Digitronic сверены 01.10.2026. Логика: AutoChill PL → выкуп/фрахт → таможня (пошлина 5% + НДС 22%) → Казань.",
        "",
        "## Короткий вердикт",
        "",
        "1. **Брать вариант C** (BLASTER Y 800 + AT13 80): ~**+849k ₽** к полке кэшем, заморозка **~1,87 млн**, инвойс **7 280 €**.",
        "2. Если нужен один SKU без микса — **B (AT13)** по деньгам или **A (BLASTER Y)** по обороту расходника.",
        "3. **НДС:** в кассе всегда платим ввозные **22%**. Если юрлицо вычитает НДС (ОСНО) — экономическая маржа выше (~+20–30 п.п.). Без вычета смотри колонку «кэш».",
        "4. FLY dedicated не тащить. Nordic/Nordic XP — только в миксе после C.",
        "",
        "## Что изменилось vs сентябрь",
        "",
        f"| | Было (04.09) | Сейчас ({data['date']}) |",
        "|---|---:|---:|",
        "| EUR | 100,598 | 94,881 |",
        "| Nordic полка | 6 150 | 7 000 |",
        "| Nordic XP полка | 8 250 | 9 200 |",
        "| AT13 полка | 11 600 | 12 800 |",
        "| BLASTER Y земля BASE | 816 ₽ | ~772 ₽ |",
        "",
        "Курс вниз + полки редукторов вверх → маржа стала лучше, не хуже.",
        "",
        "## Варианты рейса",
        "",
    ]
    for t in data["trips"]:
        lines += [
            f"### {t['title']}",
            "",
            f"**{t['verdict']}**",
            "",
            f"- Инвойс: **{t['goods_eur']:,.0f} €** ({t['goods_rub']/1000:,.0f}k ₽)".replace(",", " "),
            f"- Вес / логистика: **{t['weight']:.0f} кг** · **{t['log_eur']:.0f} €** ({t['log_rub']/1000:.0f}k ₽)",
            f"- Выкуп 750 €: **{t['buyout_rub']/1000:.0f}k ₽**",
            f"- Пошлина 5%: **{t['duty']/1000:.0f}k ₽**",
            f"- НДС ввоз 22%: **{t['vat']/1000:.0f}k ₽**",
            f"- Брокер+ФТС+Казань: **{t['fixed']/1000:.0f}k ₽**",
            f"- Касса партии (landed): **{t['landed']/1000:.0f}k ₽**",
            f"- Заморозка капитала: **{t['freeze']/1e6:.2f} млн ₽**",
            f"- Продажа по полке Digitronic: **{t['shelf']/1000:.0f}k ₽**",
            f"- Прибыль к полке **кэш (НДС внутри)**: **{t['m_cash']/1000:+.0f}k ₽** ({t['m_cash_pct']:+.0f}% к landed)",
            f"- Прибыль если **НДС к вычету (ОСНО)**: **{t['m_osno']/1000:+.0f}k ₽** ({t['m_osno_pct']:+.0f}% к земле без НДС)",
            "",
            "| SKU | шт | земля ₽ | без НДС ₽ | полка | кэш ₽ | ОСНО ₽ |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
        for x in t["lines"]:
            lines.append(
                f"| {x['name']} | {x['qty']} | {x['ep']} | {x['ep_ex_vat']} | {x['dealer']} | {x['m_cash']/1000:+.0f}k | {x['m_osno']/1000:+.0f}k |"
            )
        lines.append("")

    lines += [
        "## НДС vs не НДС — как читать",
        "",
        "| Режим | Что в кассе на таможне | Какую землю сравнивать с полкой |",
        "|---|---|---|",
        "| **Кэш / без вычета** | Платим НДС 22% | `ep` (НДС внутри) |",
        "| **ОСНО, НДС к вычету** | Платим сейчас, потом к вычету | `ep_ex_vat` |",
        "",
        "Полка Digitronic уже с **НДС 5%** (льгота на ГБО в ритейле) — это **не** ставка ввоза.",
        "Путать 5% полки и 22% таможни нельзя: ввоз всегда 22% по 8708.",
        "",
        "## Логистика (формула)",
        "",
        "`фрахт € = 162,5 + 4,75 × кг`",
        "",
        "Плюс фикс выкупа **750 €** (пока инвойс < 15 000 €), брокер **25 000 ₽**, Казань **12 000 ₽**, сбор ФТС по шкале ТС.",
        "",
        "## Next",
        "",
        "1. Согласовать с менеджером вариант **C** (или A/B).",
        "2. Запросить инвойс AutoChill под выбранный qty.",
        "3. Закрыть слот логистики / выкупа (Екатерина) и таможню.",
        "",
        "_Источник модели: `build.py` → `data.json` / `index.html` / этот файл._",
        "",
    ]
    return "\n".join(lines)


def main():
    data = build_data()
    (ROOT / "data.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (ROOT / "index.html").write_text(render(data), encoding="utf-8")
    (ROOT / "VARIANTS.md").write_text(write_variants_md(data), encoding="utf-8")
    print("SKU                    EP BASE  EP-50%  полка  маржа%   freeze BASE")
    for s in sorted(
        data["skus"], key=lambda x: scenario(x, "BASE")["m_shelf_pct"], reverse=True
    ):
        b = scenario(s, "BASE")
        m = scenario(s, "−50%")
        print(
            f"{s['name']:<22} {b['ep']:>7} {m['ep']:>7} {s['dealer']:>6} {b['m_shelf_pct']:>+6.1f}%  {b['freeze'] / 1e6:5.2f} млн"
        )
    print("\nTRIPS")
    for t in data["trips"]:
        print(
            f"{t['id']:<4} cash {t['m_cash']/1000:+7.0f}k  freeze {t['freeze']/1e6:4.2f}M  {t['title']}"
        )


if __name__ == "__main__":
    main()
