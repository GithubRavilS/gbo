#!/usr/bin/env python3
"""GBO поставка PL→RU — landed / маржа / компоновки. Без двойной заморозки."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EUR = 94.8810  # ЦБ РФ ~01.10.2026
DATE = "01.10.2026"
BUYOUT_EUR = 750
BROKER = 25000
KAZAN = 12000
DUTY = 0.05
VAT_IMPORT = 0.22  # ввозная 22% по 8708; полка Digitronic — с НДС 5%


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
    # Партнёру: только выкуп + логистика (товар уже из аванса, не второй раз)
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


# SKU: eur = цена инвойса AutoChill; dealer = полка Digitronic (скрин/сайт)
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
        in_invoice=True,
        on_shelf=True,
        url="https://www.digitronicgas.ru/catalog/d/filtr_razbornyy_tsentrobezhnyy_blaster_y_12_x_2_12/",
        note="Расходник. В инвойсе и на полке Digitronic.",
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
        in_invoice=True,
        on_shelf=True,
        url="https://www.digitronicgas.ru/catalog/d/filtr_razbornyy_tsentrobezhnyy_blaster_12_x12/",
        note="Расходник. В инвойсе и на полке.",
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
        in_invoice=True,
        on_shelf=True,
        url="https://www.digitronicgas.ru/catalog/d/filtr_nizkogo_davleniya_nerazbornyy_fly_12_2x12/",
        note="Неразборный. На dedicated-рейсе маржа тонкая.",
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
        in_invoice=True,
        on_shelf=True,
        url="https://www.digitronicgas.ru/catalog/d/filtr_nizkogo_davleniya_nerazbornyy_fls_12x12_mm/",
        note="Ходовой дешёвый расходник. Фиксы бьют по штуке на малых qty.",
    ),
    dict(
        id="nordic",
        group="Редуктор",
        name="AT09 Nordic",
        art="RGDG3890",
        eur=26.0,
        kg=1.30,
        dealer=7000,
        base_qty=200,
        in_invoice=True,
        on_shelf=True,
        url="https://www.digitronicgas.ru/catalog/d/reduktor_tomasetto_at09_nordic/",
        note="До ~170 л.с. Полка Digitronic 7 000 ₽ (скрин 01.10).",
    ),
    dict(
        id="nordic_xp",
        group="Редуктор",
        name="AT09 Nordic XP",
        art="RGDG3895",
        eur=34.0,
        kg=1.40,
        dealer=9200,
        base_qty=180,
        in_invoice=True,
        on_shelf=True,
        url="https://www.digitronicgas.ru/catalog/d/reduktor_tomasetto_at09_nordic_xp_do_250_l_s/",
        note="До 250 л.с. Полка 9 200 ₽.",
    ),
    dict(
        id="at13",
        group="Редуктор",
        name="AT13 XP",
        art="RGDG3990",
        eur=46.0,
        kg=1.60,
        dealer=12800,
        base_qty=150,
        in_invoice=True,
        on_shelf=True,
        url="https://www.digitronicgas.ru/catalog/d/reduktor_tomasetto_at13_xp/",
        note="Мощные авто. Лучшая маржа среди редукторов. Полка 12 800 ₽.",
    ),
]

VOLUME_FACTORS = [
    ("−50%", 0.50),
    ("−30%", 0.70),
    ("BASE", 1.00),
    ("+30%", 1.30),
    ("+50%", 1.50),
]


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


def enrich(r: dict, dealer: int) -> dict:
    m_cash = (dealer - r["ep"]) * r["qty"]
    m_cash_pct = (dealer - r["ep"]) / r["ep"] * 100
    m_osno = (dealer - r["ep_ex_vat"]) * r["qty"]
    m_osno_pct = (dealer - r["ep_ex_vat"]) / r["ep_ex_vat"] * 100
    return {
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


def trip_from_lines(by_id: dict, lines: list[tuple[str, int]], meta: dict) -> dict:
    """lines: [(sku_id, qty), ...] — один рейс, фиксы делятся на всю партию."""
    items = []
    for sid, qty in lines:
        s = by_id[sid]
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
    lines_out = []
    profit_cash = 0.0
    profit_osno = 0.0
    for s, q in items:
        share = (s["eur"] * q) / goods_eur
        part_landed = landed * share
        part_vat = vat * share
        ep = part_landed / q
        ep_ex = (part_landed - part_vat) / q
        mc = (s["dealer"] - ep) * q
        mo = (s["dealer"] - ep_ex) * q
        profit_cash += mc
        profit_osno += mo
        lines_out.append(
            dict(
                id=s["id"],
                name=s["name"],
                group=s["group"],
                qty=q,
                eur=s["eur"],
                dealer=s["dealer"],
                ep=round(ep),
                ep_ex_vat=round(ep_ex),
                m_cash=round(mc),
                m_osno=round(mo),
                m_cash_pct=round((s["dealer"] - ep) / ep * 100, 1),
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
        capital=round(landed, 2),  # = касса один раз, без двойной оплаты товара
        shelf=shelf,
        m_cash=round(profit_cash),
        m_osno=round(profit_osno),
        m_cash_pct=round(profit_cash / landed * 100, 1),
        m_osno_pct=round(profit_osno / (landed - vat) * 100, 1),
        verdict=verdict_of(profit_cash / landed * 100),
        lines=lines_out,
    )


def build_data():
    by_id = {s["id"]: s for s in SKUS}
    skus_out = []
    for s in SKUS:
        volumes = []
        for label, factor in VOLUME_FACTORS:
            qty = max(1, int(round(s["base_qty"] * factor)))
            volumes.append({"label": label, "factor": factor, **enrich(calc(s["eur"], qty, s["kg"]), s["dealer"])})
        base = next(v for v in volumes if v["label"] == "BASE")
        skus_out.append({**s, "volumes": volumes, "base": base})

    # --- Рейсы ---
    trips = []

    # 1) Каждый SKU отдельно (BASE qty)
    for s in SKUS:
        trips.append(
            trip_from_lines(
                by_id,
                [(s["id"], s["base_qty"])],
                dict(
                    id=f"solo_{s['id']}",
                    kind="solo",
                    title=f"Отдельно · {s['name']}",
                    blurb=f"Только этот SKU, qty BASE {s['base_qty']}.",
                ),
            )
        )

    # 2) Всё вместе BASE
    trips.append(
        trip_from_lines(
            by_id,
            [(s["id"], s["base_qty"]) for s in SKUS],
            dict(
                id="all_base",
                kind="combo",
                title="Всё вместе · BASE qty каждого",
                blurb="Один рейс: все 7 позиций из инвойса на базовых количествах. Фиксы делятся.",
            ),
        )
    )

    # 3) Всё вместе −30%
    trips.append(
        trip_from_lines(
            by_id,
            [(s["id"], max(1, int(round(s["base_qty"] * 0.7)))) for s in SKUS],
            dict(
                id="all_m30",
                kind="combo",
                title="Всё вместе · −30% qty",
                blurb="Тот же микс, объём меньше — EP хуже из‑за фиксов.",
            ),
        )
    )

    # 4) Топ-3 выгодно по чуть-чуть (бывшие сильные: Y, AT13, Nordic XP)
    trips.append(
        trip_from_lines(
            by_id,
            [("blaster_y", 400), ("nordic_xp", 40), ("at13", 40)],
            dict(
                id="top3_light",
                kind="combo",
                title="Топ-3 лёгкий · Y 400 + Nordic XP 40 + AT13 40",
                blurb="Три самых маржинальных — по чуть-чуть в одном кубе.",
            ),
        )
    )

    # 5) Топ-3 нормальный
    trips.append(
        trip_from_lines(
            by_id,
            [("blaster_y", 800), ("nordic_xp", 60), ("at13", 80)],
            dict(
                id="top3_full",
                kind="combo",
                title="Топ-3 полный · Y 800 + Nordic XP 60 + AT13 80",
                blurb="Рекомендуемый комплект: расходник + два сильных редуктора.",
            ),
        )
    )

    # 6) Фильтры-расходники без FLY
    trips.append(
        trip_from_lines(
            by_id,
            [("blaster_y", 700), ("blaster", 500), ("fls", 1200)],
            dict(
                id="filters_no_fly",
                kind="combo",
                title="Фильтры без FLY · Y+BLASTER+FLS",
                blurb="Только ходовые фильтры. FLY убран — тянет маржу вниз.",
            ),
        )
    )

    # 7) Редукторы микс
    trips.append(
        trip_from_lines(
            by_id,
            [("nordic", 80), ("nordic_xp", 60), ("at13", 50)],
            dict(
                id="reducers_mix",
                kind="combo",
                title="Редукторы микс · Nordic + XP + AT13",
                blurb="Только редукторы. Высокий чек, оборот медленнее фильтров.",
            ),
        )
    )

    # 8) Без слабых (без FLY)
    trips.append(
        trip_from_lines(
            by_id,
            [
                ("blaster_y", 600),
                ("blaster", 400),
                ("fls", 800),
                ("nordic", 60),
                ("nordic_xp", 50),
                ("at13", 50),
            ],
            dict(
                id="all_no_fly",
                kind="combo",
                title="Широкий микс без FLY",
                blurb="Почти всё из инвойса, но FLY выкинут как слабое звено.",
            ),
        )
    )

    return {
        "eur": EUR,
        "date": DATE,
        "note_capital": "Аванс → оплата товара с аванса. Касса = landed один раз. Двойной оплаты товара нет.",
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


def render(data: dict) -> str:
    skus = sorted(data["skus"], key=lambda s: s["base"]["m_cash_pct"], reverse=True)
    solos = [t for t in data["trips"] if t["kind"] == "solo"]
    combos = [t for t in data["trips"] if t["kind"] == "combo"]

    sku_rows = ""
    for s in skus:
        b = s["base"]
        sku_rows += f"""<tr>
          <td><a href="{s["url"]}" target="_blank" rel="noopener">{s["name"]}</a><div class="muted tiny">{s["group"]} · {s["eur"]:.2f} €</div></td>
          <td class="num">{r(s["dealer"])}</td>
          <td class="num">{r(b["ep"])}</td>
          <td class="num">{r(b["ep_ex_vat"])}</td>
          <td class="num {vclass(b["verdict"])}">{b["m_cash_pct"]:+.0f}%</td>
          <td class="num">{k(b["m_cash"])}</td>
          <td class="num">{k(b["m_osno"])}</td>
          <td class="num">{r(b["landed"]/1000,0)}k</td>
          <td><span class="pill {vclass(b["verdict"])}">{b["verdict"]}</span></td>
        </tr>"""

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
              <td class="num">{k(v["m_cash"])}</td>
              <td class="num">{k(v["m_osno"])}</td>
              <td class="num">{r(v["landed"]/1000,0)}k</td>
            </tr>"""
        flags = []
        if s["in_invoice"]:
            flags.append("в инвойсе")
        if s["on_shelf"]:
            flags.append("на полке Digitronic")
        vol_sections += f"""
        <article class="card" id="{s["id"]}">
          <header>
            <div>
              <span class="tag">{s["group"]}</span>
              <h3>{s["name"]}</h3>
              <p class="lead">{s["note"]} · {", ".join(flags)}</p>
            </div>
            <div class="right">
              <div>инвойс <b>{s["eur"]:.2f} €</b> · полка <b>{r(s["dealer"])} ₽</b></div>
              <span class="pill {vclass(s["base"]["verdict"])}">{s["base"]["verdict"]} BASE</span>
            </div>
          </header>
          <table>
            <thead><tr><th>Объём</th><th>шт</th><th>инвойс</th><th>земля ₽</th><th>маржа кэш</th><th>₽ кэш</th><th>₽ ОСНО</th><th>касса</th></tr></thead>
            <tbody>{rows}</tbody>
          </table>
        </article>"""

    def trip_card(t):
        lines = "".join(
            f"<li><b>{x['name']}</b> ×{r(x['qty'])} · земля {r(x['ep'])} ₽ · "
            f"<span class='{vclass(x['verdict'])}'>{x['m_cash_pct']:+.0f}%</span> · {k(x['m_cash'])}</li>"
            for x in t["lines"]
        )
        return f"""
        <article class="card trip">
          <header>
            <div>
              <h3>{t["title"]}</h3>
              <p class="lead">{t["blurb"]}</p>
            </div>
            <span class="pill {vclass(t["verdict"])}">{t["verdict"]}</span>
          </header>
          <div class="grid4">
            <div><small>Инвойс</small><b>{r(t["goods_eur"],0)} € · {r(t["goods_rub"]/1000,0)}k</b></div>
            <div><small>Логистика</small><b>{r(t["log_eur"],0)} € · {r(t["weight"],0)} кг</b></div>
            <div><small>Касса (капитал)</small><b>{r(t["capital"]/1000,0)}k ₽</b></div>
            <div><small>НДС 22%</small><b>{r(t["vat"]/1000,0)}k ₽</b></div>
            <div><small>Полка Digitronic</small><b>{r(t["shelf"]/1000,0)}k ₽</b></div>
            <div><small>Прибыль кэш</small><b class="good">{k(t["m_cash"])} · {t["m_cash_pct"]:+.0f}%</b></div>
            <div><small>Прибыль ОСНО</small><b class="good">{k(t["m_osno"])} · {t["m_osno_pct"]:+.0f}%</b></div>
            <div><small>Партнёр (выкуп+фрахт)</small><b>{r(t["partner"]/1000,0)}k ₽</b></div>
          </div>
          <ul class="lines">{lines}</ul>
        </article>"""

    solo_html = "".join(trip_card(t) for t in sorted(solos, key=lambda x: -x["m_cash_pct"]))
    combo_html = "".join(trip_card(t) for t in combos)

    # ranking for verdict block
    best = skus[0]
    weak = [s for s in skus if s["base"]["verdict"] in ("слабо", "в минус")]
    weak_names = ", ".join(s["name"] for s in weak) or "—"

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>GBO поставка · полный расклад</title>
<style>
  :root {{
    --bg:#0c1016; --card:#141a22; --line:#273041; --text:#e8eef7; --muted:#8b97a8;
    --good:#34d399; --ok:#fbbf24; --weak:#fb923c; --bad:#f87171; --link:#93c5fd;
  }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; font:15px/1.45 "IBM Plex Sans", ui-sans-serif, system-ui, sans-serif; background:var(--bg); color:var(--text); }}
  .wrap {{ max-width:1040px; margin:0 auto; padding:22px 14px 72px; }}
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
    <h1>GBO поставка · полный расклад</h1>
    <p class="sub">PL → Казань · EUR ЦБ <b>{r(data["eur"],4)}</b> на {data["date"]} · товар из аванса, <b>без двойной заморозки</b></p>
    <div class="callouts">
      <div class="callout"><b>Касса = landed один раз.</b> {data["note_capital"]}</div>
      <div class="callout"><b>Лучший соло:</b> {best["name"]} · {best["base"]["m_cash_pct"]:+.0f}% кэш · {k(best["base"]["m_cash"])}. <b>Слабые:</b> {weak_names}.</div>
      <div class="callout"><b>Рекомендую комплект:</b> Топ-3 полный (BLASTER Y 800 + Nordic XP 60 + AT13 80) — см. блок компоновок.</div>
      <div class="callout"><b>НДС:</b> ввоз 22% всегда в кассе. Полка Digitronic — с НДС 5% (другая ставка). ОСНО = если ввозной НДС к вычету.</div>
    </div>
  </div>

  <h2>1. Что в инвойсе и на полке</h2>
  <div class="card">
    <p class="lead" style="margin-bottom:10px">Все 7 позиций есть и в прайсе AutoChill (инвойс EUR), и на digitronicgas.ru (полка ₽, скрины/сайт на {data["date"]}). Сравнение — земля vs полка.</p>
    <div class="scroll">
      <table>
        <thead>
          <tr>
            <th>SKU</th><th>полка ₽</th><th>земля кэш</th><th>земля без НДС</th>
            <th>маржа</th><th>₽ кэш BASE</th><th>₽ ОСНО</th><th>касса</th><th></th>
          </tr>
        </thead>
        <tbody>{sku_rows}</tbody>
      </table>
    </div>
  </div>

  <h2>2. Компоновки рейса (несколько SKU вместе)</h2>
  {combo_html}

  <h2>3. Если везти каждый SKU отдельно</h2>
  {solo_html}

  <h2>4. Доходность при разных объёмах (один SKU на рейсе)</h2>
  {vol_sections}

  <h2>5. Как читать цифры</h2>
  <div class="card">
    <table>
      <tbody>
        <tr><td>Товар</td><td class="muted">оплата из аванса, один раз</td></tr>
        <tr><td>Партнёр</td><td class="muted">выкуп 750 € (или 5% если инвойс ≥15k €) + фрахт 162,5+4,75×кг €</td></tr>
        <tr><td>Таможня</td><td class="muted">пошлина 5% от (товар+фрахт) + НДС 22% + брокер 25k + ФТС + Казань 12k</td></tr>
        <tr><td>Касса / капитал</td><td class="muted">сумма всего выше = landed. Лишних 100% товара на счету нет</td></tr>
        <tr><td>Кэш vs ОСНО</td><td class="muted">кэш сравнивает полку с землёй включая ввозной НДС; ОСНО — если НДС к вычету</td></tr>
      </tbody>
    </table>
  </div>

  <footer>
    Пересчёт `{DATE}` · `python3 build.py` · данные в data.json · этот файл index.html
  </footer>
</div>
</body>
</html>
"""


def write_variants_md(data: dict) -> str:
    skus = sorted(data["skus"], key=lambda s: s["base"]["m_cash_pct"], reverse=True)
    combos = [t for t in data["trips"] if t["kind"] == "combo"]
    lines = [
        "# GBO поставка — полный расклад",
        "",
        f"Дата **{data['date']}**, EUR **{data['eur']:.4f}**.",
        "",
        "## Важно про деньги",
        "",
        data["note_capital"],
        "Старая «заморозка = товар дважды» **убрана**.",
        "",
        "## SKU: инвойс ↔ полка ↔ выгодно?",
        "",
        "| SKU | инвойс € | полка ₽ | земля кэш | маржа | ₽ BASE | вердикт |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for s in skus:
        b = s["base"]
        lines.append(
            f"| {s['name']} | {s['eur']:.2f} | {s['dealer']} | {b['ep']} | {b['m_cash_pct']:+.0f}% | {b['m_cash']/1000:+.0f}k | **{b['verdict']}** |"
        )
    lines += ["", "## Компоновки", ""]
    for t in combos:
        lines += [
            f"### {t['title']}",
            "",
            f"- {t['blurb']}",
            f"- Инвойс **{t['goods_eur']:,.0f} €** · касса **{t['capital']/1000:.0f}k ₽** · НДС **{t['vat']/1000:.0f}k**".replace(",", " "),
            f"- Кэш **{t['m_cash']/1000:+.0f}k ({t['m_cash_pct']:+.0f}%)** · ОСНО **{t['m_osno']/1000:+.0f}k** · **{t['verdict']}**",
            "",
        ]
        for x in t["lines"]:
            lines.append(
                f"  - {x['name']} ×{x['qty']}: земля {x['ep']} ₽ · {x['m_cash_pct']:+.0f}% · {x['m_cash']/1000:+.0f}k · {x['verdict']}"
            )
        lines.append("")
    lines += [
        "## Рекомендация",
        "",
        "1. **Топ-3 полный** — основной сценарий.",
        "2. Не возить FLY dedicated; в широком миксе — без FLY.",
        "3. Соло имеет смысл для AT13 / BLASTER Y / Nordic XP.",
        "",
    ]
    return "\n".join(lines)


def main():
    data = build_data()
    (ROOT / "data.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    (ROOT / "index.html").write_text(render(data), encoding="utf-8")
    (ROOT / "VARIANTS.md").write_text(write_variants_md(data), encoding="utf-8")
    print("SKU ranking (BASE, no double freeze)")
    for s in sorted(data["skus"], key=lambda x: -x["base"]["m_cash_pct"]):
        b = s["base"]
        print(f"  {s['name']:<22} ep={b['ep']:>5}  {b['m_cash_pct']:+6.1f}%  {b['m_cash']/1000:+7.0f}k  cash={b['landed']/1000:6.0f}k  {b['verdict']}")
    print("\nCOMBOS")
    for t in data["trips"]:
        if t["kind"] != "combo":
            continue
        print(f"  {t['id']:<16} {t['m_cash']/1000:+7.0f}k ({t['m_cash_pct']:+5.1f}%)  cash={t['capital']/1000:6.0f}k  {t['verdict']}")


if __name__ == "__main__":
    main()
