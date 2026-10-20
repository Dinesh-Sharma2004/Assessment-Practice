"""Data-analysis (chart) question generator. Each case builds a seeded dataset + chart spec(s) and then asks
questions whose answers are computed from the plotted numbers. Chart specs are rendered by the frontend as SVG."""
import json
import random

from builder import MCQ
from gen_apt import nf, options, pc

CATS_Q = ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6"]
CATS_M = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
CATS_Y = ["2019", "2020", "2021", "2022", "2023", "2024"]
THEMES = [
    dict(metric="revenue", unit="$M", title="Quarterly revenue", cats=CATS_Q, catname="quarter", lo=40, hi=140),
    dict(metric="monthly active users", unit="thousand", title="Monthly active users", cats=CATS_M, catname="month", lo=120, hi=480),
    dict(metric="model error rate", unit="%", title="Fraud-model error rate", cats=CATS_M, catname="month", lo=4, hi=18),
    dict(metric="cloud spend", unit="$K", title="Cloud spend", cats=CATS_Y, catname="year", lo=80, hi=360),
    dict(metric="support tickets", unit="", title="Support tickets raised", cats=CATS_Q, catname="quarter", lo=200, hi=900),
    dict(metric="API latency", unit="ms", title="Average API latency", cats=CATS_M, catname="month", lo=60, hi=240),
]
PIE_THEMES = [
    ("Cloud cost split", "$K", ["Compute", "Storage", "Network", "Support", "Licences"], "cloud bill"),
    ("Trade volume by asset class", "million shares", ["Equities", "Options", "Futures", "ETFs", "Bonds"], "trading volume"),
    ("Alert causes", "alerts", ["Velocity", "Geo", "Amount", "Device", "Manual"], "alerts raised"),
]


def line_or_bar(r, kind):
    return kind


def series_vals(r, th, n=6, step=None):
    lo, hi = th["lo"], th["hi"]
    v = [r.randrange(lo, hi)]
    for _ in range(n - 1):
        v.append(max(lo // 2, v[-1] + r.randrange(-(hi - lo) // 4, (hi - lo) // 3)))
    v = [int(x) for x in v]
    return v


def spec(kind, th, vals, name=None, cats=None, title=None):
    return {"type": kind, "title": title or th["title"], "xLabel": th["catname"].capitalize(), "yLabel": f"{th['metric'].capitalize()}" + (f" ({th['unit']})" if th["unit"] else ""),
            "categories": cats or th["cats"], "series": [{"name": name or th["metric"].capitalize(), "values": vals}], "unit": th["unit"]}


class Seen:
    """Returns 0 the first time a level is requested within a case, 1 the second time, ... so repeated levels get different asks."""
    def __init__(self): self.n = {}
    def __call__(self, L):
        self.n[L] = self.n.get(L, -1) + 1
        return self.n[L]


def interval(c, i):
    return f"{c[i]} to {c[i+1]}"


# --------------------------------------------------------------- family A: single series (bar / line)
def fam_single(r, levels, kind):
    th = r.choice(THEMES)
    while True:
        v = series_vals(r, th)
        inc_abs = [v[i + 1] - v[i] for i in range(5)]; inc_pct = [(v[i + 1] - v[i]) / v[i] for i in range(5)]
        if max(range(5), key=lambda i: inc_abs[i]) != max(range(5), key=lambda i: inc_pct[i]) and len(set(v)) == 6 and all(x > 0 for x in v):
            break
    c, u = th["cats"], th["unit"]
    chart = spec(kind, th, v)
    fm = (lambda x: nf(x) + (" " + u if u and u != "%" else ("%" if u == "%" else ""))).__call__ if False else None
    def f(x):
        return nf(x) + ("%" if u == "%" else (" " + u if u else ""))
    qs = []
    seen = Seen()
    for L in levels:
        ask = seen(L) % 2
        if L == 1:
            if ask == 0:
                i = max(range(6), key=lambda k: v[k]); d = dict(stmt=f"In which {th['catname']} was {th['metric']} the highest?", ans=c[i], cands=[x for j, x in enumerate(c) if j != i], fmt=str,
                                                              expl=f"Reading the chart, the highest value is {f(v[i])} in {c[i]}.", hint="Find the tallest bar / highest point.")
            else:
                i = r.randrange(6); d = dict(stmt=f"What was the {th['metric']} in {c[i]}?", ans=v[i], cands=[v[(i + 1) % 6], v[(i + 2) % 6], v[i] + 10], fmt=f, expl=f"The plotted value for {c[i]} is {f(v[i])}.", hint="Read the value for that category off the vertical axis.")
        elif L == 2:
            i, j = r.sample(range(6), 2)
            if ask == 0:
                d = dict(stmt=f"What is the difference between the {th['metric']} in {c[i]} and in {c[j]}?", ans=abs(v[i] - v[j]), cands=[v[i] + v[j], abs(v[i] - v[j]) + 10, abs(v[i] - v[j]) // 2 + 1], fmt=f,
                         expl=f"|{v[i]} − {v[j]}| = {abs(v[i]-v[j])}.", hint="Subtract the smaller value from the larger.")
            else:
                d = dict(stmt=f"What is the total {th['metric']} across {c[i]} and {c[j]} combined?", ans=v[i] + v[j], cands=[abs(v[i] - v[j]), (v[i] + v[j]) / 2, v[i] + v[j] + 10], fmt=f, expl=f"{v[i]} + {v[j]} = {v[i]+v[j]}.", hint="Read both values and add them.")
        elif L == 3:
            if ask == 0:
                i = r.randrange(5); a, b = v[i], v[i + 1]; pcv = (b - a) * 100 / a
                d = dict(stmt=f"By what percentage did {th['metric']} {'rise' if b>a else 'fall'} from {c[i]} to {c[i+1]}?", ans=abs(pcv), cands=[abs(b - a), abs(b - a) * 100 / b, abs(pcv) + 5], fmt=pc,
                         expl=f"|{b} − {a}| / {a} × 100 = {nf(abs(pcv))}%.", hint="Percentage change = (new − old) / old × 100 — divide by the earlier value.")
            else:
                avg = sum(v) / 6; d = dict(stmt=f"What is the average {th['metric']} over the six {th['catname']}s shown?", ans=avg, cands=[max(v) / 2 + min(v) / 2 if False else (max(v) + min(v)) / 2, sum(v), avg + 7], fmt=f,
                                           expl=f"Sum = {sum(v)}; average = {sum(v)}/6 = {nf(avg)}.", hint="Average = sum of the six values / 6.")
        elif L == 4:
            if ask == 0:
                k = max(range(5), key=lambda i: inc_abs[i]); d = dict(stmt=f"Between which two consecutive {th['catname']}s was the absolute increase in {th['metric']} the largest?", ans=interval(c, k), cands=[interval(c, i) for i in range(5) if i != k], fmt=str,
                                                                    expl=f"Changes: {', '.join(f'{interval(c,i)}: {inc_abs[i]:+d}' for i in range(5))}. The largest is {interval(c,k)} ({inc_abs[k]:+d}).", hint="Compute each consecutive difference and compare.")
            else:
                top3 = sorted(v)[-3:]; d = dict(stmt=f"What is the average of the three highest {th['metric']} values shown?", ans=sum(top3) / 3, cands=[sum(v) / 6, sum(sorted(v)[:3]) / 3, max(v)], fmt=f,
                                                expl=f"Three highest: {', '.join(map(str, sorted(top3, reverse=True)))}; average = {nf(sum(top3)/3)}.", hint="Pick the three tallest bars, add and divide by 3.")
        else:
            if ask == 0:
                k = max(range(5), key=lambda i: inc_pct[i]); d = dict(stmt=f"Which interval shows the largest *percentage* increase in {th['metric']}?", ans=interval(c, k), cands=[interval(c, i) for i in range(5) if i != k], fmt=str,
                                                                    expl=f"Percentage changes: {', '.join(f'{interval(c,i)}: {inc_pct[i]*100:+.1f}%' for i in range(5))}. The largest is {interval(c,k)}. (The biggest absolute rise is in {interval(c, max(range(5), key=lambda i: inc_abs[i]))}, which is not the biggest percentage rise.)",
                                                                    hint="Percentage change depends on the starting level — divide each increase by its own starting value.")
            else:
                imax, imin = max(range(6), key=lambda k: v[k]), min(range(6), key=lambda k: v[k])
                true = [f"The highest value occurs in {c[imax]}.", f"The lowest value occurs in {c[imin]}.", f"The value in {c[imax]} is {nf(v[imax]*100/v[imin])}% of the value in {c[imin]}."]
                false = f"The value in {c[imin]} is more than half of the value in {c[imax]}." if v[imin] * 2 <= v[imax] else f"The value in {c[imin]} is less than half of the value in {c[imax]}."
                if v[imin] * 2 <= v[imax]:
                    false = f"The value in {c[imin]} is more than half of the value in {c[imax]}."
                else:
                    false = f"The value in {c[imax]} is more than double the value in {c[imin]}."
                    if v[imax] > 2 * v[imin]: false = f"The value in {c[imax]} is less than the value in {c[imin]}."
                d = dict(stmt="Which statement is NOT supported by the chart?", ans=false, cands=true, fmt=str,
                         expl=f"Highest = {v[imax]} ({c[imax]}), lowest = {v[imin]} ({c[imin]}). The other three statements are consistent with these values; the selected statement contradicts them.", hint="Check each statement against the numbers; exactly one is false.")
        d["tags"] = ["chart reading", kind + " chart"]; d["charts"] = [chart]; d["L"] = L; qs.append(d)
    return qs


# --------------------------------------------------------------- family B: two series (grouped bar / line)
def fam_two(r, levels, kind):
    th = r.choice(THEMES[:4]); c = th["cats"]; n = 6
    a = series_vals(r, th); b = [max(5, int(x * r.uniform(0.55, 1.2))) for x in a]
    while len(set(x - y for x, y in zip(a, b))) < 5 or max(a) == min(a):
        a = series_vals(r, th); b = [max(5, int(x * r.uniform(0.55, 1.2))) for x in a]
    n1, n2 = r.choice([("Region A", "Region B"), ("Product X", "Product Y"), ("Model v1", "Model v2")])
    chart = {"type": kind, "title": f"{th['title']}: {n1} vs {n2}", "xLabel": th["catname"].capitalize(), "yLabel": f"{th['metric'].capitalize()}" + (f" ({th['unit']})" if th["unit"] else ""),
             "categories": c, "series": [{"name": n1, "values": a}, {"name": n2, "values": b}], "unit": th["unit"]}
    u = th["unit"]; f = lambda x: nf(x) + ("%" if u == "%" else (" " + u if u else ""))
    qs = []
    seen = Seen()
    for L in levels:
        v_ = seen(L) % 2
        i = r.randrange(6)
        gaps = [x - y for x, y in zip(a, b)]
        if L == 1 and v_:
            d = dict(stmt=f"In {c[i]}, which series had the higher {th['metric']}: {n1} or {n2}?", ans=(n1 if a[i] > b[i] else n2 if b[i] > a[i] else "They were equal"), cands=[x for x in (n1, n2, "They were equal", "Cannot be determined") if x != (n1 if a[i] > b[i] else n2 if b[i] > a[i] else "They were equal")], fmt=str,
                     expl=f"In {c[i]}: {n1} = {a[i]}, {n2} = {b[i]}, so " + ("the higher one is " + (n1 if a[i] > b[i] else n2) if a[i] != b[i] else "they were equal") + ".", hint="Compare the two bars (or points) of the same category.")
        elif L == 1:
            d = dict(stmt=f"What was the {th['metric']} of {n1} in {c[i]}?", ans=a[i], cands=[b[i], a[(i + 1) % 6], a[i] + 10], fmt=f, expl=f"The {n1} series reads {a[i]} in {c[i]}.", hint="Pick the right series by its legend colour, then read the category.")
        elif L == 2 and v_:
            d = dict(stmt=f"What was the combined {th['metric']} of {n1} and {n2} in {c[i]}?", ans=a[i] + b[i], cands=[abs(gaps[i]), a[i], (a[i] + b[i]) / 2], fmt=f, expl=f"{a[i]} + {b[i]} = {a[i]+b[i]}.", hint="Add the two series' values for that category.")
        elif L == 2:
            d = dict(stmt=f"In {c[i]}, by how much did {n1} differ from {n2}?", ans=abs(gaps[i]), cands=[a[i] + b[i], abs(gaps[i]) + 10, a[i]], fmt=f, expl=f"|{a[i]} − {b[i]}| = {abs(gaps[i])}.", hint="Subtract the two series' values for the same category.")
        elif L == 3 and v_:
            k = min(range(6), key=lambda j: abs(gaps[j])); d = dict(stmt=f"In which {th['catname']} were {n1} and {n2} closest to each other?", ans=c[k], cands=[x for j, x in enumerate(c) if j != k], fmt=str,
                                                                    expl=f"Gaps: {', '.join(f'{c[j]}: {abs(gaps[j])}' for j in range(6))}. Smallest in {c[k]}.", hint="Compute |series 1 − series 2| for each category and take the smallest.")
        elif L == 3:
            k = max(range(6), key=lambda j: abs(gaps[j])); d = dict(stmt=f"In which {th['catname']} was the gap between {n1} and {n2} the largest?", ans=c[k], cands=[x for j, x in enumerate(c) if j != k], fmt=str,
                                                                    expl=f"Gaps: {', '.join(f'{c[j]}: {abs(gaps[j])}' for j in range(6))}. Largest in {c[k]}.", hint="Compute |series 1 − series 2| for each category.")
        elif L == 4 and v_:
            ta, tb = sum(a), sum(b); d = dict(stmt=f"Over all six {th['catname']}s, what percentage of the combined total did {n1} account for?", ans=ta * 100 / (ta + tb), cands=[tb * 100 / (ta + tb), ta * 100 / tb, ta / 6], fmt=pc,
                                              expl=f"{n1} total = {ta}, {n2} total = {tb}; share = {ta}/{ta+tb} = {nf(ta*100/(ta+tb))}%.", hint="Sum each series first; share = series total ÷ combined total.")
        elif L == 4:
            ga = (a[-1] - a[0]) * 100 / a[0]; gb = (b[-1] - b[0]) * 100 / b[0]
            d = dict(stmt=f"From {c[0]} to {c[-1]}, which series grew by the larger percentage, and by how much (approx.)?", ans=f"{n1}, {nf(round(ga,1))}%" if ga > gb else f"{n2}, {nf(round(gb,1))}%",
                     cands=[f"{n2}, {nf(round(gb,1))}%" if ga > gb else f"{n1}, {nf(round(ga,1))}%", f"{n1}, {nf(round(a[-1]-a[0],1))}", f"{n2}, {nf(round(b[-1]-b[0],1))}"], fmt=str,
                     expl=f"{n1}: ({a[-1]}−{a[0]})/{a[0]} = {ga:.1f}%; {n2}: ({b[-1]}−{b[0]})/{b[0]} = {gb:.1f}%.", hint="Percentage growth = (last − first)/first × 100, computed for each series.")
        elif v_:
            ra = [x / y for x, y in zip(a, b)]; k2 = min(range(6), key=lambda j: ra[j]); k = max(range(6), key=lambda j: ra[j])
            d = dict(stmt=f"The ratio {n1} : {n2} was lowest in which {th['catname']}, and what was that ratio (to 2 decimals)?", ans=f"{c[k2]}, {ra[k2]:.2f}", cands=[f"{c[k]}, {ra[k]:.2f}", f"{c[min(range(6), key=lambda j: gaps[j])]}, {ra[min(range(6), key=lambda j: gaps[j])]:.2f}", f"{c[k2]}, {ra[k2]+0.1:.2f}"], fmt=str,
                     expl=f"Ratios: {', '.join(f'{c[j]}: {ra[j]:.2f}' for j in range(6))}. Lowest in {c[k2]}.", hint="Divide the first series by the second for every category and compare.")
        else:
            ra = [x / y for x, y in zip(a, b)]; k = max(range(6), key=lambda j: ra[j]); k2 = min(range(6), key=lambda j: ra[j])
            d = dict(stmt=f"The ratio {n1} : {n2} was highest in which {th['catname']}, and what was that ratio (to 2 decimals)?", ans=f"{c[k]}, {ra[k]:.2f}", cands=[f"{c[k2]}, {ra[k2]:.2f}", f"{c[max(range(6), key=lambda j: gaps[j])]}, {ra[max(range(6), key=lambda j: gaps[j])]:.2f}", f"{c[k]}, {ra[k]+0.1:.2f}"], fmt=str,
                     expl=f"Ratios: {', '.join(f'{c[j]}: {ra[j]:.2f}' for j in range(6))}. Highest in {c[k]}.", hint="Divide the first series by the second for every category; the largest gap is not necessarily the largest ratio.")
        d["tags"] = ["chart reading", "comparison", kind + " chart"]; d["charts"] = [chart]; d["L"] = L; qs.append(d)
    return qs


# --------------------------------------------------------------- family C: pie
def fam_pie(r, levels):
    title, unit, labels, nm = r.choice(PIE_THEMES)
    while True:
        sh = [r.randrange(5, 40) for _ in labels]; s = sum(sh); sh = [round(x * 100 / s) for x in sh]; sh[0] += 100 - sum(sh)
        if len(set(sh)) == len(sh) and min(sh) > 3: break
    T = r.choice([200, 240, 400, 500, 800])
    chart = {"type": "pie", "title": f"{title} (percent of total)", "slices": [{"label": l, "value": v} for l, v in zip(labels, sh)], "unit": "%"}
    f = lambda x: nf(x) + (" " + unit if unit else "")
    qs = []
    seen = Seen()
    for L in levels:
        i, j = r.sample(range(len(labels)), 2)
        rep_ = seen(L)
        if L == 1 and rep_:
            k = min(range(len(sh)), key=lambda x: sh[x]); d = dict(stmt=f"Which category has the smallest share of the {nm}?", ans=labels[k], cands=[l for x, l in enumerate(labels) if x != k], fmt=str, expl=f"{labels[k]} has {sh[k]}%, the smallest slice.", hint="The smallest slice has the smallest percentage.")
        elif L == 1:
            k = max(range(len(sh)), key=lambda x: sh[x]); d = dict(stmt=f"Which category has the largest share of the {nm}?", ans=labels[k], cands=[l for x, l in enumerate(labels) if x != k], fmt=str, expl=f"{labels[k]} has {sh[k]}%, the largest slice.", hint="The largest slice has the largest percentage.")
        elif L == 2:
            d = dict(stmt=f"The total {nm} is {T} {unit}. How much is {labels[i]}?".replace("  ", " "), ans=sh[i] * T / 100, cands=[sh[i], sh[i] * T / 10, sh[j] * T / 100], fmt=f, expl=f"{sh[i]}% of {T} = {nf(sh[i]*T/100)}.", hint="Amount = share% × total.")
        elif L == 3 and rep_:
            hi_, lo_ = (i, j) if sh[i] >= sh[j] else (j, i)
            d = dict(stmt=f"How many times as large is the share of {labels[hi_]} compared with the share of {labels[lo_]}? (Answer to 2 decimals.)", ans=sh[hi_] / sh[lo_], cands=[sh[hi_] - sh[lo_], sh[lo_] / sh[hi_], sh[hi_] / sh[lo_] + 0.5], fmt=lambda x: nf(round(x, 2)) + "×",
                     expl=f"{sh[hi_]}% ÷ {sh[lo_]}% = {sh[hi_]/sh[lo_]:.2f}.", hint="Divide the larger share by the smaller one.")
        elif L == 3:
            d = dict(stmt=f"What percentage of the {nm} do {labels[i]} and {labels[j]} account for together?", ans=sh[i] + sh[j], cands=[abs(sh[i] - sh[j]), (sh[i] + sh[j]) / 2, sh[i] + sh[j] + 5], fmt=pc, expl=f"{sh[i]}% + {sh[j]}% = {sh[i]+sh[j]}%.", hint="Shares of the same whole can be added.")
        elif L == 4:
            d = dict(stmt=f"The total {nm} is {T} {unit}. By how much does {labels[i]} exceed {labels[j]} in absolute terms?", ans=abs(sh[i] - sh[j]) * T / 100, cands=[abs(sh[i] - sh[j]), (sh[i] + sh[j]) * T / 100, abs(sh[i] - sh[j]) * T / 10], fmt=f,
                     expl=f"|{sh[i]} − {sh[j]}| = {abs(sh[i]-sh[j])} percentage points of {T} = {nf(abs(sh[i]-sh[j])*T/100)}.", hint="Convert the percentage-point gap to an amount using the total.")
        else:
            cut = r.choice([20, 25, 50]); newT = T - sh[i] * T / 100 * cut / 100; newshare = (sh[i] * T / 100 * (1 - cut / 100)) * 100 / newT
            d = dict(stmt=f"The total {nm} is {T} {unit}. If {labels[i]} is cut by {cut}% and everything else stays the same, what is the new share of {labels[i]} in the (new) total?", ans=newshare, cands=[sh[i] * (1 - cut / 100), sh[i] - cut, newshare + 3], fmt=pc,
                     expl=f"{labels[i]} = {nf(sh[i]*T/100)}; after the cut {nf(sh[i]*T/100*(1-cut/100))}. New total = {nf(newT)}. Share = {nf(newshare)}%.", hint="The total changes too: recompute the total before computing the new share.")
        d["tags"] = ["chart reading", "pie chart", "shares"]; d["charts"] = [chart]; d["L"] = L; qs.append(d)
    return qs


# --------------------------------------------------------------- family D: stacked bar
def fam_stacked(r, levels):
    c = ["North", "South", "East", "West"]; comps = ["Product A", "Product B", "Product C"]
    vals = [[r.randrange(10, 60) for _ in c] for _ in comps]
    chart = {"type": "stacked", "title": "Units sold by region and product", "xLabel": "Region", "yLabel": "Units sold (thousand)", "categories": c,
             "series": [{"name": n, "values": v} for n, v in zip(comps, vals)], "unit": "thousand"}
    tot = [sum(vals[k][j] for k in range(3)) for j in range(4)]
    f = lambda x: nf(x) + " thousand"
    qs = []
    seen = Seen()
    for L in levels:
        v_ = seen(L) % 2
        j = r.randrange(4); k = r.randrange(3); j2 = (j + 1 + r.randrange(3)) % 4
        if L == 1:
            d = dict(stmt=f"How many units of {comps[k]} were sold in the {c[j]} region?", ans=vals[k][j], cands=[tot[j], vals[(k + 1) % 3][j], vals[k][j] + 10], fmt=f, expl=f"The {comps[k]} segment in {c[j]} is {vals[k][j]}.", hint="Read the height of that segment (top minus bottom of the coloured block).")
        elif L == 2 and v_:
            kbest = max(range(4), key=lambda x: tot[x]); d = dict(stmt="Which region sold the most units in total (all products)?", ans=c[kbest], cands=[x for q_, x in enumerate(c) if q_ != kbest], fmt=str,
                                                                  expl="Totals: " + ", ".join(f"{c[x]}: {tot[x]}" for x in range(4)) + f". Highest: {c[kbest]}.", hint="Add the segments of each bar and compare the totals.")
        elif L == 2:
            d = dict(stmt=f"What is the total number of units sold in the {c[j]} region?", ans=tot[j], cands=[vals[k][j], sum(vals[k]), tot[j] + 10], fmt=f, expl=f"{' + '.join(str(vals[x][j]) for x in range(3))} = {tot[j]}.", hint="The total is the height of the whole stacked bar.")
        elif L == 3 and v_:
            k2 = (k + 1) % 3
            d = dict(stmt=f"In the {c[j]} region, how many times as many units of {comps[k]} as of {comps[k2]} were sold? (2 decimals)", ans=vals[k][j] / vals[k2][j], cands=[vals[k2][j] / vals[k][j], vals[k][j] - vals[k2][j], vals[k][j] / vals[k2][j] + 0.5], fmt=lambda x: nf(round(x, 2)) + "×",
                     expl=f"{vals[k][j]} / {vals[k2][j]} = {vals[k][j]/vals[k2][j]:.2f}.", hint="Divide the first segment by the second segment of the same bar.")
        elif L == 3:
            d = dict(stmt=f"What percentage of {c[j]}'s sales were {comps[k]}?", ans=vals[k][j] * 100 / tot[j], cands=[vals[k][j], vals[k][j] * 100 / sum(tot), tot[j] / vals[k][j]], fmt=pc, expl=f"{vals[k][j]} / {tot[j]} × 100 = {nf(vals[k][j]*100/tot[j])}%.", hint="Share = segment / bar total × 100.")
        elif L == 4 and v_:
            best = min(range(4), key=lambda x: vals[k][x] / tot[x]); d = dict(stmt=f"In which region does {comps[k]} make up the smallest share of that region's sales?", ans=c[best], cands=[x for i, x in enumerate(c) if i != best], fmt=str,
                                                                              expl="Shares: " + ", ".join(f"{c[x]}: {vals[k][x]*100/tot[x]:.1f}%" for x in range(4)) + f". Smallest in {c[best]}.", hint="Compute segment ÷ total for every region and compare.")
        elif L == 4:
            best = max(range(4), key=lambda x: vals[k][x] / tot[x]); d = dict(stmt=f"In which region does {comps[k]} make up the largest share of that region's sales?", ans=c[best], cands=[x for i, x in enumerate(c) if i != best], fmt=str,
                                                                              expl="Shares: " + ", ".join(f"{c[x]}: {vals[k][x]*100/tot[x]:.1f}%" for x in range(4)) + f". Highest in {c[best]}.", hint="Compute segment ÷ total for every region; the tallest segment is not necessarily the largest share.")
        else:
            s1, s2 = vals[k][j] * 100 / tot[j], vals[k][j2] * 100 / tot[j2]
            d = dict(stmt=f"By how many percentage points does the share of {comps[k]} in {c[j]} differ from its share in {c[j2]}?", ans=abs(s1 - s2), cands=[abs(vals[k][j] - vals[k][j2]), abs(s1 - s2) / 2 + 1, (s1 + s2) / 2], fmt=lambda x: nf(round(x, 1)) + " pts",
                     expl=f"Share in {c[j]} = {s1:.1f}%, in {c[j2]} = {s2:.1f}%; difference = {abs(s1-s2):.1f} percentage points.", hint="Compute both shares first, then subtract them (percentage points, not percent).")
        d["tags"] = ["chart reading", "stacked bar", "shares"]; d["charts"] = [chart]; d["L"] = L; qs.append(d)
    return qs


# --------------------------------------------------------------- family E: scatter
def fam_scatter(r, levels):
    xs = sorted(r.sample(range(1, 11), 7)); slope, icpt = r.choice([(4, 20), (5, 10), (3, 30), (6, 5)]); pts = [(x, slope * x + icpt + r.choice([-3, -2, 2, 3])) for x in xs]
    o = r.randrange(2, 6); pts_o = pts[:]; pts_o[o] = (pts[o][0], pts[o][1] + r.choice([-35, 40]))
    pts = pts_o
    chart = {"type": "scatter", "title": "Study hours vs exam score", "xLabel": "Hours studied", "yLabel": "Exam score", "series": [{"name": "Students", "points": [{"x": x, "y": y} for x, y in pts]}], "unit": ""}
    qs = []
    seen = Seen()
    for L in levels:
        v_ = seen(L) % 2
        i = r.choice([0, 1, 5, 6])
        if L == 1 and v_:
            d = dict(stmt="Which description fits the pattern of the points best?", ans="Roughly linear and increasing, with one point far from the trend", cands=["Roughly linear and decreasing", "Curved with a clear peak in the middle", "Points scattered randomly with no trend"], fmt=str,
                     expl="Most points lie close to an upward-sloping line; one point lies far from it.", hint="Describe direction (up/down), shape (line/curve) and any unusual point.")
        elif L == 1:
            d = dict(stmt="What relationship does the scatter plot suggest between hours studied and exam score?", ans="Positive: more hours are generally associated with higher scores", cands=["Negative: more hours are associated with lower scores", "No relationship at all", "A perfect relationship with every point on one line"], fmt=str,
                     expl="Points rise from bottom-left to top-right, indicating a positive association (the outlier does not change the overall pattern).", hint="Does y generally rise or fall as x increases?")
        elif L == 2 and v_:
            hi_ = max(pts, key=lambda p: p[1])
            d = dict(stmt="How many hours did the student with the highest exam score study?", ans=hi_[0], cands=[hi_[1], min(pts, key=lambda p: p[1])[0], hi_[0] + 1], fmt=nf, expl=f"The highest point is ({hi_[0]}, {hi_[1]}), so the student studied {hi_[0]} hours.", hint="Find the highest point and read its horizontal position.")
        elif L == 2:
            d = dict(stmt=f"What is the exam score of the student who studied {pts[i][0]} hours?", ans=pts[i][1], cands=[pts[i][1] + 10, pts[(i + 1) % 7][1], pts[i][0]], fmt=nf, expl=f"The plotted point at x = {pts[i][0]} has y = {pts[i][1]}.", hint="Locate x on the horizontal axis and read the point's height.")
        elif L == 3:
            a, b = (pts[2], pts[3]) if v_ and o not in (2, 3) else (pts[0], pts[1]) if not v_ else (pts[5], pts[6]); m = (b[1] - a[1]) / (b[0] - a[0])
            d = dict(stmt=f"Using the points ({a[0]}, {a[1]}) and ({b[0]}, {b[1]}), what is the approximate gain in score per extra hour studied?", ans=m, cands=[b[1] - a[1], (b[0] - a[0]) / (b[1] - a[1]), a[1] / a[0]], fmt=lambda x: nf(round(x, 2)),
                     expl=f"Slope = (Δy)/(Δx) = ({b[1]}−{a[1]})/({b[0]}−{a[0]}) = {nf(round(m,2))}.", hint="Slope = change in y ÷ change in x between the two points.")
        elif L == 4 and v_:
            hi = [x for x, y in pts if y > 50]
            d = dict(stmt="How many students scored above 50?", ans=len(hi), cands=[len(hi) + 1, len(hi) - 1 if len(hi) > 1 else len(hi) + 2, len(pts)], fmt=nf, expl=f"Points with y > 50 have x = {', '.join(map(str, hi))}: {len(hi)} students.", hint="Count the points above the 50 mark on the vertical axis.")
        elif L == 4:
            d = dict(stmt="One student's score looks unusually far from the overall trend. How many hours did that student study?", ans=pts[o][0], cands=[x for x, _ in pts if x != pts[o][0]][:5], fmt=nf,
                     expl=f"The point at x = {pts[o][0]} (score {pts[o][1]}) is far from the line formed by the others (about {slope}x + {icpt}).", hint="Look for the point that sits far above or below the line formed by the rest.")
        elif v_:
            others = [p for k, p in enumerate(pts) if k != o]; a, b = others[0], others[-1]; m = (b[1] - a[1]) / (b[0] - a[0]); pred = a[1] + m * (pts[o][0] - a[0]); gap = pts[o][1] - pred
            d = dict(stmt=f"Draw a straight line through the first point ({a[0]}, {a[1]}) and the last point ({b[0]}, {b[1]}) of the students other than the outlier. By how many points does the outlier's actual score differ from this line's prediction at {pts[o][0]} hours? (Answer: actual − predicted.)", ans=gap, cands=[-gap, abs(gap) / 2, pts[o][1]], fmt=lambda x: nf(round(x, 1)),
                     expl=f"Slope = {m:.3f}; predicted score at {pts[o][0]} h = {pred:.1f}; the outlier scored {pts[o][1]}, so the difference is {gap:.1f}.", hint="Predict the outlier's score from the line, then subtract it from the actual score.")
        else:
            others = [p for k, p in enumerate(pts) if k != o]; a, b = others[0], others[-1]; m = (b[1] - a[1]) / (b[0] - a[0]); x0 = r.choice([x for x in range(1, 15) if x not in xs]); pred = a[1] + m * (x0 - a[0])
            d = dict(stmt=f"Ignoring the outlier, draw a straight line through the first point ({a[0]}, {a[1]}) and the last point ({b[0]}, {b[1]}) of the remaining students. What score does this line predict for {x0} hours?", ans=pred, cands=[b[1] + (x0 - b[0]) * 2, pred + 8, m * x0], fmt=lambda x: nf(round(x, 1)),
                     expl=f"Slope = {nf(round(m,3))}; prediction = {a[1]} + {nf(round(m,3))}×({x0} − {a[0]}) = {nf(round(pred,1))}.", hint="Find the slope, then use y = y₁ + m(x − x₁).")
        d["tags"] = ["chart reading", "scatter plot", "trend"]; d["charts"] = [chart]; d["L"] = L; qs.append(d)
    return qs


# --------------------------------------------------------------- family F: two charts combined
def fam_dual(r, levels):
    c = CATS_Q[:5]; rev = [r.randrange(60, 200) for _ in c]; head = [r.randrange(10, 40) for _ in c]
    ch1 = {"type": "bar", "title": "Revenue by quarter", "xLabel": "Quarter", "yLabel": "Revenue ($M)", "categories": c, "series": [{"name": "Revenue", "values": rev}], "unit": "$M"}
    ch2 = {"type": "line", "title": "Headcount by quarter", "xLabel": "Quarter", "yLabel": "Employees", "categories": c, "series": [{"name": "Headcount", "values": head}], "unit": ""}
    rp = [x / y for x, y in zip(rev, head)]
    qs = []
    seen = Seen()
    for L in levels:
        v_ = seen(L) % 2
        i = r.randrange(5); j = (i + 1 + r.randrange(4)) % 5
        if L <= 2:
            d = dict(stmt=f"In {c[i]}, what was the revenue and how many employees were there?", ans=f"${rev[i]}M and {head[i]} employees", cands=[f"${rev[j]}M and {head[i]} employees", f"${rev[i]}M and {head[j]} employees", f"${head[i]}M and {rev[i]} employees"], fmt=str,
                     expl=f"Left chart: {rev[i]}; right chart: {head[i]}.", hint="Read each chart separately for the same quarter.")
        elif L == 3 and v_:
            d = dict(stmt=f"By how much (in $M, 2 decimals) did revenue per employee change from {c[i]} to {c[j]}? (Answer: {c[j]} value − {c[i]} value.)", ans=rp[j] - rp[i], cands=[rev[j] - rev[i], head[j] - head[i], rp[i] - rp[j] if rp[i] != rp[j] else rp[j] + 0.3], fmt=lambda x: "$" + nf(round(x, 2)) + "M",
                     expl=f"{c[j]}: {rev[j]}/{head[j]} = {rp[j]:.2f}; {c[i]}: {rev[i]}/{head[i]} = {rp[i]:.2f}; change = {rp[j]-rp[i]:.2f}.", hint="Compute revenue ÷ headcount for both quarters, then subtract.")
        elif L == 3:
            d = dict(stmt=f"What was the revenue per employee (in $M, to 2 decimals) in {c[i]}?", ans=rp[i], cands=[rev[i] - head[i], head[i] / rev[i], rp[j]], fmt=lambda x: "$" + nf(round(x, 2)) + "M", expl=f"{rev[i]} / {head[i]} = {rp[i]:.2f}.", hint="Combine the charts: revenue ÷ headcount for the same quarter.")
        elif L == 4 and v_:
            k = min(range(5), key=lambda x: rp[x]); d = dict(stmt="In which quarter was revenue per employee the lowest?", ans=c[k], cands=[x for q, x in enumerate(c) if q != k], fmt=str,
                                                           expl="Revenue per employee: " + ", ".join(f"{c[x]}: {rp[x]:.2f}" for x in range(5)) + f". Lowest: {c[k]}.", hint="Compute revenue ÷ headcount for each quarter and compare.")
        elif L == 4:
            k = max(range(5), key=lambda x: rp[x]); d = dict(stmt="In which quarter was revenue per employee the highest?", ans=c[k], cands=[x for q, x in enumerate(c) if q != k], fmt=str,
                                                           expl="Revenue per employee: " + ", ".join(f"{c[x]}: {rp[x]:.2f}" for x in range(5)) + f". Highest: {c[k]}.", hint="Compute revenue ÷ headcount for each quarter; highest revenue is not necessarily the best productivity.")
        elif v_:
            tr, th_ = sum(rev), sum(head); d = dict(stmt="Using the totals over all five quarters, what was the average revenue per employee-quarter (total revenue ÷ total headcount, 2 decimals, in $M)?", ans=tr / th_, cands=[sum(rp) / 5, tr / 5, th_ / tr], fmt=lambda x: "$" + nf(round(x, 2)) + "M",
                                                    expl=f"Total revenue {tr}, total headcount {th_}; ratio = {tr/th_:.2f}. (The mean of the five quarterly ratios is {sum(rp)/5:.2f}, which is a different, unweighted number.)", hint="Divide the sum of revenues by the sum of headcounts — not the mean of the ratios.")
        else:
            gr = (rev[-1] - rev[0]) * 100 / rev[0]; gh = (head[-1] - head[0]) * 100 / head[0]; diff = gr - gh
            d = dict(stmt=f"From {c[0]} to {c[-1]}, by how many percentage points did revenue growth exceed (or fall short of) headcount growth? (Answer: revenue growth − headcount growth.)", ans=diff, cands=[gr, gh, -diff], fmt=lambda x: nf(round(x, 1)) + " pts",
                     expl=f"Revenue growth = {gr:.1f}%, headcount growth = {gh:.1f}%; difference = {diff:.1f} percentage points.", hint="Compute the percentage growth of each chart's series first, then subtract.")
        d["tags"] = ["chart reading", "multiple charts"]; d["charts"] = [ch1, ch2]; d["L"] = L; qs.append(d)
    return qs


# --------------------------------------------------------------- family G: table with chart (model comparison)
def fam_table(r, levels):
    models = ["Model A", "Model B", "Model C", "Model D"]; acc = [r.randrange(78, 96) for _ in models]; lat = [r.randrange(20, 120) for _ in models]; prec = [max(60, a - r.randrange(0, 8)) for a in acc]
    ch = {"type": "bar", "title": "Accuracy (%) by model", "xLabel": "Model", "yLabel": "Accuracy (%)", "categories": models, "series": [{"name": "Accuracy", "values": acc}], "unit": "%"}
    table = {"type": "table", "title": "Latency and precision", "columns": ["Model", "Latency (ms)", "Precision (%)"], "rows": [[m, l, p] for m, l, p in zip(models, lat, prec)]}
    qs = []
    seen = Seen()
    for L in levels:
        v_ = seen(L) % 2
        i = r.randrange(4); j = (i + 1 + r.randrange(3)) % 4
        if L == 1 and v_:
            k = max(range(4), key=lambda x: acc[x]); d = dict(stmt="Which model has the highest accuracy?", ans=models[k], cands=[m for x, m in enumerate(models) if x != k], fmt=str, expl=f"The tallest bar is {models[k]} at {acc[k]}%.", hint="Find the tallest bar in the chart.")
        elif L == 1:
            k = min(range(4), key=lambda x: lat[x]); d = dict(stmt="Which model has the lowest latency?", ans=models[k], cands=[m for x, m in enumerate(models) if x != k], fmt=str, expl=f"The table shows {lat[k]} ms for {models[k]}, the smallest.", hint="Look in the Latency column.")
        elif L == 2:
            d = dict(stmt=f"By how many percentage points is the accuracy of {models[i]} higher or lower than that of {models[j]}? (Give the absolute difference.)", ans=abs(acc[i] - acc[j]), cands=[acc[i] + acc[j], abs(lat[i] - lat[j]), abs(acc[i] - acc[j]) + 3], fmt=lambda x: nf(x) + " pts", expl=f"|{acc[i]} − {acc[j]}| = {abs(acc[i]-acc[j])}.", hint="Read both accuracies from the chart and subtract.")
        elif L == 3 and v_:
            d = dict(stmt="What is the average latency of the four models?", ans=sum(lat) / 4, cands=[max(lat), sum(lat) / 3, sum(acc) / 4], fmt=lambda x: nf(x) + " ms", expl=f"({' + '.join(map(str, lat))})/4 = {nf(sum(lat)/4)}.", hint="Average = sum / 4 using the Latency column.")
        elif L == 3:
            d = dict(stmt=f"What is the average accuracy of the four models?", ans=sum(acc) / 4, cands=[max(acc), sum(acc) / 3, sum(prec) / 4], fmt=pc, expl=f"({' + '.join(map(str, acc))})/4 = {nf(sum(acc)/4)}.", hint="Average = sum / 4.")
        elif L == 4 and v_:
            gap = [a - p for a, p in zip(acc, prec)]; k = max(range(4), key=lambda x: gap[x]); d = dict(stmt="Which model has the largest gap between its accuracy and its precision?", ans=models[k], cands=[m for x, m in enumerate(models) if x != k], fmt=str,
                                                                                                    expl="Accuracy − precision: " + ", ".join(f"{models[x]}: {gap[x]}" for x in range(4)) + f". Largest: {models[k]}.", hint="Combine the chart (accuracy) with the table (precision) and subtract per model.")
        elif L == 4:
            ratio = [a / l for a, l in zip(acc, lat)]; k = max(range(4), key=lambda x: ratio[x]); d = dict(stmt="Which model gives the most accuracy points per millisecond of latency (accuracy ÷ latency)?", ans=models[k], cands=[m for x, m in enumerate(models) if x != k], fmt=str,
                                                                                                          expl="Accuracy ÷ latency: " + ", ".join(f"{models[x]}: {ratio[x]:.3f}" for x in range(4)) + f". Best: {models[k]}.", hint="Combine the chart and the table: divide each model's accuracy by its latency.")
        elif v_:
            sc = [a * 0.5 + p * 0.3 - l * 0.2 for a, p, l in zip(acc, prec, lat)]; k = max(range(4), key=lambda x: sc[x]); d = dict(stmt="A composite score is 0.5 × accuracy + 0.3 × precision − 0.2 × latency (ms). Which model scores highest, and what is its score (1 decimal)?", ans=f"{models[k]}, {sc[k]:.1f}", cands=[f"{models[x]}, {sc[x]:.1f}" for x in range(4) if x != k], fmt=str,
                                                  expl="Scores: " + ", ".join(f"{models[x]}: {sc[x]:.1f}" for x in range(4)) + f". Highest: {models[k]}.", hint="Evaluate the weighted formula for every model using chart + table values.")
        else:
            f1 = [2 * a * p / (a + p) for a, p in zip(acc, prec)]; k = max(range(4), key=lambda x: f1[x])
            d = dict(stmt="Treat accuracy as recall and compute the harmonic mean (F1) of accuracy and precision for each model. Which model has the highest F1, and what is it (1 decimal)?", ans=f"{models[k]}, {f1[k]:.1f}", cands=[f"{models[x]}, {f1[x]:.1f}" for x in range(4) if x != k], fmt=str,
                     expl="F1 = 2ap/(a+p): " + ", ".join(f"{models[x]}: {f1[x]:.1f}" for x in range(4)) + f". Highest: {models[k]}.", hint="F1 = 2·a·p / (a + p) with a = accuracy and p = precision.")
        d["tags"] = ["chart reading", "table", "model evaluation"]; d["charts"] = [ch, table]; d["L"] = L; qs.append(d)
    return qs


CASES = [
    lambda r, L: fam_single(r, L, "bar"), lambda r, L: fam_single(r, L, "line"), lambda r, L: fam_two(r, L, "grouped"), lambda r, L: fam_two(r, L, "line"),
    fam_pie, fam_stacked, fam_scatter, fam_dual, fam_table,
]
PLAN = {1: [(1, 1, 2), (1, 1, 2), (1, 1, 2), (1, 2, 2)], 2: [(1, 2, 2), (2, 2, 3), (2, 3, 3), (1, 2, 3)], 3: [(2, 3, 3), (3, 3, 4), (3, 3, 2), (3, 4, 3)],
        4: [(3, 3, 4), (3, 4, 3), (4, 4, 5), (3, 4, 5)], 5: [(4, 4, 5), (4, 5, 5), (5, 5, 4), (4, 5, 5)]}
CASE_PICK = {1: [0, 4, 2, 6], 2: [1, 5, 3, 8], 3: [0, 7, 4, 3], 4: [2, 5, 7, 8], 5: [1, 6, 7, 8]}
DIFF = {1: "easy", 2: "easy", 3: "medium", 4: "hard", 5: "hard"}


_SEEN = set()


def build_da(oa: int):
    r = random.Random(9100 + oa)
    out, stmts = [], set()
    for ci, levels in zip(CASE_PICK[oa], PLAN[oa]):
        for _ in range(3000):
            qs = CASES[ci](r, list(levels))
            if len({d["stmt"] for d in qs}) < len(qs) or any(d["stmt"] in stmts or (d["stmt"] + json.dumps(d["charts"], sort_keys=True)) in _SEEN for d in qs):
                continue
            try:
                made = []
                for d in qs:
                    ans, w = options(d["ans"], d["cands"], d.get("fmt", nf))
                    m = MCQ("DA", d["tags"] + ["data analysis"], DIFF[d["L"]], d["stmt"], ans, w, d["expl"])
                    m.hint = d["hint"]; m.charts = d["charts"]; made.append(m)
            except AssertionError:
                continue
            stmts |= {d["stmt"] for d in qs}; _SEEN.update(d["stmt"] + json.dumps(d["charts"], sort_keys=True) for d in qs)
            break
        else:
            raise RuntimeError("could not build distinct DA case")
        out += made
    return out


if __name__ == "__main__":
    import json
    for oa in range(1, 6):
        qs = build_da(oa); print(oa, len(qs), [q.diff[0] for q in qs])
    for q in build_da(4)[:4]:
        print(q.stmt, "->", q.correct, q.wrongs, "|", q.expl[:90])
