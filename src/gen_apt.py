"""Aptitude question families. Every answer is computed, never typed; options are checked for uniqueness.
Each family f(r, L) -> dict(stmt, ans, cands, expl, hint, tags[, fmt]) for difficulty level L in 1..5."""
import math
import random
from fractions import Fraction
from itertools import combinations, permutations

from builder import MCQ


def nf(x):
    if isinstance(x, Fraction):
        x = float(x)
    if isinstance(x, str):
        return x
    return str(int(round(x))) if abs(x - round(x)) < 1e-9 else f"{x:.2f}".rstrip("0").rstrip(".")


def pc(x):
    return nf(x) + "%"


def options(ans, cands, fmt=nf):
    a = fmt(ans)
    w = []
    prob = isinstance(ans, Fraction) and 0 < ans <= 1
    if prob:
        cands = [c for c in cands if 0 < c <= 1]
    for c in cands:
        s = fmt(c)
        if s != a and s not in w:
            w.append(s)
    if prob:
        for c in (ans / 2, (1 + ans) / 2, ans * Fraction(2, 3), ans * Fraction(3, 4), ans / 3):
            s = fmt(c)
            if s != a and s not in w and len(w) < 3:
                w.append(s)
    if not isinstance(ans, (str, Fraction)) and abs(ans - round(ans)) < 1e-9:       # integer answer -> integer distractors
        base = int(round(ans))
        for c in (base + 1, base - 1, base + 2, base - 2, base * 2, base + 10, base // 2 + 1, base + 5, base + 7):
            s = fmt(c)
            if c > 0 and s != a and s not in w and len(w) < 3:
                w.append(s)
    k = 1
    while len(w) < 3 and not isinstance(ans, str):
        for c in (ans + k, ans * (1 + 0.1 * k), ans * 2 + k, abs(ans - k) + 0.5):
            s = fmt(c)
            if s != a and s not in w and len(w) < 3:
                w.append(s)
        k += 1
    assert len(w) >= 3, (ans, cands)
    return a, w[:3]


# ---------------------------------------------------------------- families
def percent(r, L):
    if L == 1:
        p, n = r.choice([10, 20, 25, 50, 5]), r.choice([40, 80, 120, 200, 360, 500])
        return dict(stmt=f"What is {p}% of {n}?", ans=p * n / 100, cands=[n / p, p + n / 100, n - p * n / 100],
                    expl=f"{p}% of {n} = {p}/100 × {n} = {nf(p*n/100)}.", hint="x% of N = x/100 × N.", tags=["percentages"])
    if L == 2:
        p, q, a, b = r.choice([10, 20, 25]), r.choice([5, 10, 40]), r.choice([200, 400, 600]), r.choice([100, 300, 500])
        v = p * a / 100 + q * b / 100
        return dict(stmt=f"What is {p}% of {a} plus {q}% of {b}?", ans=v, cands=[(p + q) * (a + b) / 100, p * a / 100, v + q],
                    expl=f"{p}% of {a} = {nf(p*a/100)} and {q}% of {b} = {nf(q*b/100)}; the sum is {nf(v)}.", hint="Compute each percentage separately, then add.", tags=["percentages"])
    if L == 3:
        p, q = r.choice([10, 20, 25, 30]), r.choice([10, 20, 40])
        net = (100 + p) * (100 - q) / 100 - 100
        return dict(stmt=f"A share price rises by {p}% on Monday and then falls by {q}% on Tuesday. What is the net percentage change over the two days?",
                    ans=net, cands=[p - q, -(q - p), net + 2], fmt=lambda x: nf(x) + "%",
                    expl=f"Multiplier = (1 + {p}/100)(1 − {q}/100) = {nf((100+p)*(100-q)/10000)}. Net change = {nf(net)}%.", hint="Successive changes multiply: new = old × (1 + p/100) × (1 − q/100). Don't just add the percentages.", tags=["percentages", "successive change"])
    if L == 4:
        M, p, q = r.choice([2000, 4000, 5000]), r.choice([10, 20, 25]), r.choice([10, 20, 30])
        sp = M * (100 - p) * (100 - q) / 10000
        return dict(stmt=f"A laptop has a marked price of {M}. It is sold after successive discounts of {p}% and {q}%. What is the selling price?", ans=sp,
                    cands=[M * (100 - p - q) / 100, M * (100 - p) / 100, M * (100 - q) / 100 - 50],
                    expl=f"{M} × {100-p}/100 × {100-q}/100 = {nf(sp)}. Adding the discounts ({p+q}%) would be wrong because the second discount applies to the reduced price.", hint="Apply the second discount to the already discounted price: M × (1 − p/100) × (1 − q/100).", tags=["percentages", "discount"])
    orig = r.choice([200, 250, 400, 500, 800, 1000]); p, q = r.choice([20, 25, 50]), r.choice([20, 40, 50])
    R = orig * (100 + p) * (100 - q) / 10000
    return dict(stmt=f"A number is increased by {p}% and the result is then decreased by {q}%, giving {nf(R)}. What was the original number?", ans=orig,
                cands=[R * (100 - p + q) / 100, R / (1 + (p - q) / 100), R * 100 / (100 - q) - p], fmt=nf,
                expl=f"Net multiplier = {100+p}/100 × {100-q}/100 = {nf((100+p)*(100-q)/10000)}. Original = {nf(R)} ÷ {nf((100+p)*(100-q)/10000)} = {nf(orig)}.", hint="Work backwards: original = final ÷ (product of the multipliers).", tags=["percentages", "reverse percentage"])


def profit(r, L):
    if L == 1:
        cp, g = r.choice([200, 250, 400, 500]), r.choice([20, 30, 40, 50])
        sp = cp + g
        return dict(stmt=f"An item bought for {cp} is sold for {sp}. What is the profit percentage?", ans=g * 100 / cp, cands=[g, g * 100 / sp, sp * 100 / cp], fmt=pc,
                    expl=f"Profit = {sp} − {cp} = {g}. Profit % = {g}/{cp} × 100 = {nf(g*100/cp)}%.", hint="Profit % = (SP − CP)/CP × 100. The base is the cost price.", tags=["profit and loss"])
    if L == 2:
        cp, p = r.choice([400, 600, 800, 1200]), r.choice([10, 15, 20, 25])
        return dict(stmt=f"A trader buys goods for {cp} and wants a profit of {p}%. At what price must he sell?", ans=cp * (100 + p) / 100, cands=[cp + p, cp * (100 - p) / 100, cp * p / 100],
                    expl=f"SP = CP × (100 + {p})/100 = {nf(cp*(100+p)/100)}.", hint="SP = CP × (1 + profit%).", tags=["profit and loss"])
    if L == 3:
        mp, d, p = r.choice([1000, 1500, 2000]), r.choice([10, 20, 25]), None
        sp = mp * (100 - d) / 100
        cp = r.choice([x for x in range(int(sp * 0.6), int(sp * 0.95)) if x % 10 == 0])
        pr = (sp - cp) * 100 / cp
        return dict(stmt=f"A shopkeeper marks an article at {mp} and gives a discount of {d}%. If the cost price is {cp}, what is his profit percentage?", ans=pr,
                    cands=[(sp - cp) * 100 / sp, (mp - cp) * 100 / cp, d], fmt=pc,
                    expl=f"SP = {mp} × {100-d}% = {nf(sp)}. Profit = {nf(sp)} − {cp} = {nf(sp-cp)}. Profit % = {nf(sp-cp)}/{cp} × 100 = {nf(pr)}%.", hint="First find the selling price after the discount, then profit % = (SP − CP)/CP × 100.", tags=["profit and loss", "discount"])
    if L == 4:
        s, g = r.choice([1200, 1800, 2400]), r.choice([10, 20, 25])
        cp1, cp2 = s * 100 / (100 + g), s * 100 / (100 - g)
        loss = (cp1 + cp2) - 2 * s
        return dict(stmt=f"Two articles are each sold for {s}. One is sold at a gain of {g}% and the other at a loss of {g}%. What is the overall result?",
                    ans=-loss, cands=[0, loss, g * s / 100], fmt=lambda x: ("Loss of " + nf(-x)) if x < 0 else ("Gain of " + nf(x) if x > 0 else "No profit, no loss"),
                    expl=f"CP₁ = {s}×100/{100+g} = {nf(cp1)}, CP₂ = {s}×100/{100-g} = {nf(cp2)}. Total CP = {nf(cp1+cp2)}, total SP = {2*s}. Net = {nf(2*s-cp1-cp2)}.", hint="Find each cost price from SP = CP × (1 ± g/100); compare total CP with total SP. Equal gain% and loss% on the same SP always gives a loss.", tags=["profit and loss"])
    c, tgt, d = r.choice([600, 800, 1000]), r.choice([20, 25, 40]), r.choice([10, 20, 25])
    mp = c * (100 + tgt) / (100 - d)
    return dict(stmt=f"By what price should an article costing {c} be marked so that after allowing a discount of {d}% the shopkeeper still makes a profit of {tgt}%?", ans=mp,
                cands=[c * (100 + tgt + d) / 100, c * (100 + tgt) / 100, c * (100 + tgt) * (100 + d) / 10000],
                expl=f"Required SP = {c} × {100+tgt}% = {nf(c*(100+tgt)/100)}. This is {100-d}% of the marked price, so MP = {nf(c*(100+tgt)/100)} ÷ {nf((100-d)/100)} = {nf(mp)}.", hint="SP = CP × (1 + profit%) and SP = MP × (1 − discount%). Equate them.", tags=["profit and loss", "discount"])


def interest(r, L):
    P, rt, t = r.choice([2000, 5000, 8000, 10000]), r.choice([5, 8, 10, 12]), r.choice([2, 3, 4])
    if L == 1:
        return dict(stmt=f"Find the simple interest on {P} at {rt}% per annum for {t} years.", ans=P * rt * t / 100, cands=[P * rt / 100, P * (1 + rt / 100) ** t - P, P * rt * t / 10],
                    expl=f"SI = P×R×T/100 = {P}×{rt}×{t}/100 = {nf(P*rt*t/100)}.", hint="SI = P × R × T / 100.", tags=["interest"])
    if L == 2:
        si = P * rt * t / 100
        return dict(stmt=f"A sum of {P} earns simple interest of {nf(si)} in {t} years. What is the annual rate?", ans=rt, cands=[si / P, rt * t, rt / t], fmt=pc,
                    expl=f"R = SI×100/(P×T) = {nf(si)}×100/({P}×{t}) = {rt}%.", hint="R = SI × 100 / (P × T).", tags=["interest"])
    if L == 3:
        P, rt = r.choice([5000, 10000, 20000]), r.choice([10, 20])
        ci = P * (1 + rt / 100) ** 2 - P
        return dict(stmt=f"Find the compound interest on {P} at {rt}% per annum for 2 years, compounded annually.", ans=ci, cands=[P * rt * 2 / 100, P * (1 + rt / 100) ** 2, ci + P * 0.01],
                    expl=f"Amount = {P}×(1+{rt}/100)² = {nf(P*(1+rt/100)**2)}. CI = amount − principal = {nf(ci)}.", hint="A = P(1 + r/100)^n and CI = A − P.", tags=["interest", "compound interest"])
    if L == 4:
        P, rt = r.choice([5000, 8000, 10000, 20000]), r.choice([5, 10, 20])
        ci = P * (1 + rt / 100) ** 2 - P; si = P * rt * 2 / 100
        return dict(stmt=f"What is the difference between the compound interest and the simple interest on {P} at {rt}% per annum for 2 years?", ans=ci - si, cands=[ci, si, P * rt / 100],
                    expl=f"CI = {nf(ci)}, SI = {nf(si)}; difference = {nf(ci-si)}. (Shortcut: P(r/100)² = {nf(P*(rt/100)**2)}.)", hint="For 2 years, CI − SI = P × (r/100)².", tags=["interest", "compound interest"])
    P, rt = r.choice([8000, 16000, 20000]), r.choice([10, 20])
    A = P * (1 + rt / 200) ** 2
    return dict(stmt=f"What is the amount on {P} for 1 year at {rt}% per annum compounded half-yearly?", ans=A, cands=[P * (1 + rt / 100), P * (1 + rt / 200), P * (1 + rt / 100) ** 2],
                expl=f"Half-yearly: rate per period = {nf(rt/2)}%, 2 periods. A = {P}×(1+{nf(rt/200)})² = {nf(A)}.", hint="With half-yearly compounding use rate r/2 and 2n periods.", tags=["interest", "compound interest"])


def ratio(r, L):
    if L == 1:
        a, b, k = r.choice([(2, 3), (3, 5), (1, 4), (2, 5)]), None, r.choice([20, 30, 40, 50])
        a, b = a; tot = k * (a + b)
        return dict(stmt=f"Divide {tot} in the ratio {a}:{b}. What is the larger share?", ans=k * max(a, b), cands=[k * min(a, b), tot * max(a, b) / 100, tot / max(a, b)],
                    expl=f"Total parts = {a+b}; one part = {tot}/{a+b} = {k}. Larger share = {max(a,b)} × {k} = {k*max(a,b)}.", hint="Share = (part / sum of parts) × total.", tags=["ratio"])
    if L == 2:
        a, b = r.choice([(3, 4), (2, 5), (5, 7)]); k = r.choice([4, 6, 8])
        return dict(stmt=f"The ratio of boys to girls in a class is {a}:{b}. If there are {a*k} boys, how many students are in the class?", ans=(a + b) * k, cands=[b * k, (a + b) * k - k, a * b * k],
                    expl=f"One part = {a*k}/{a} = {k}. Total = ({a}+{b}) × {k} = {(a+b)*k}.", hint="Find the value of one ratio part first.", tags=["ratio"])
    if L == 3:
        a, b = r.choice([(2, 3), (3, 5), (4, 5)]); k = r.choice([5, 10, 12]); add = r.choice([4, 6, 8, 10])
        return dict(stmt=f"Two numbers are in the ratio {a}:{b} and their sum is {(a+b)*k}. If {add} is added to each, what is the new ratio (in simplest form)?",
                    ans=Fraction(a * k + add, b * k + add), cands=[Fraction(a, b), Fraction(a * k, b * k + add), Fraction(a * k + add, b * k)], fmt=lambda f: f"{Fraction(f).numerator}:{Fraction(f).denominator}",
                    expl=f"Numbers are {a*k} and {b*k}. After adding {add}: {a*k+add}:{b*k+add} = {Fraction(a*k+add,b*k+add).numerator}:{Fraction(a*k+add,b*k+add).denominator}.", hint="Find the actual numbers first, then add and simplify the ratio.", tags=["ratio"])
    if L == 4:
        a, b, c, d = r.choice([(2, 3, 4, 5), (3, 4, 2, 3), (1, 2, 3, 4)])
        # A:B = a:b , B:C = c:d  => A:B:C = a*c : b*c : b*d
        x, y, z = a * c, b * c, b * d; g = math.gcd(math.gcd(x, y), z); x, y, z = x // g, y // g, z // g
        return dict(stmt=f"If A:B = {a}:{b} and B:C = {c}:{d}, what is A:B:C?", ans=f"{x}:{y}:{z}", cands=[f"{a}:{b}:{d}", f"{a*c}:{b*d}:{d}", f"{a}:{c}:{d}"], fmt=str,
                    expl=f"Make B equal: A:B = {a*c}:{b*c}, B:C = {b*c}:{b*d}. So A:B:C = {a*c}:{b*c}:{b*d} = {x}:{y}:{z}.", hint="Scale both ratios so the common term (B) has the same value, then chain them.", tags=["ratio"])
    p1, m1, p2, m2 = r.choice([(4000, 12, 6000, 8), (5000, 6, 3000, 10), (2000, 12, 8000, 3)]); prof = r.choice([6200, 9000, 11700])
    s1, s2 = p1 * m1, p2 * m2; sh1 = Fraction(prof * s1, s1 + s2)
    if sh1.denominator != 1:
        prof = (s1 + s2) * 3; sh1 = Fraction(prof * s1, s1 + s2)
    return dict(stmt=f"A invests {p1} for {m1} months and B invests {p2} for {m2} months. They earn a profit of {prof}. What is A's share?", ans=sh1,
                cands=[Fraction(prof * p1, p1 + p2), prof / 2, Fraction(prof * s2, s1 + s2)], expl=f"Profit ratio = investment × time = {s1}:{s2}. A's share = {prof} × {s1}/{s1+s2} = {nf(sh1)}.", hint="Partners share profit in the ratio of (capital × time).", tags=["ratio", "partnership"])


def average(r, L):
    n = r.choice([4, 5, 6]); xs = [r.randrange(10, 60) for _ in range(n)]
    if L == 1:
        xs = xs[:5]; s = sum(xs) + (5 - sum(xs) % 5) % 5; xs[-1] += s - sum(xs)
        return dict(stmt=f"Find the average of {', '.join(map(str, xs))}.", ans=sum(xs) / 5, cands=[sum(xs), sum(xs) / 4, max(xs)], expl=f"Sum = {sum(xs)}; average = {sum(xs)}/5 = {nf(sum(xs)/5)}.", hint="Average = sum of values / number of values.", tags=["averages"])
    if L == 2:
        avg = r.choice([20, 25, 30, 40]); n = r.choice([4, 5]); known = [avg + r.choice([-6, -3, 2, 5]) for _ in range(n - 1)]; miss = avg * n - sum(known)
        return dict(stmt=f"The average of {n} numbers is {avg}. Four... ".replace("Four... ", "") + f"{n-1} of them are {', '.join(map(str, known))}. What is the remaining number?", ans=miss, cands=[avg, sum(known) / (n - 1), miss + avg],
                    expl=f"Total = {avg} × {n} = {avg*n}. Missing = {avg*n} − {sum(known)} = {miss}.", hint="Total = average × count. Missing number = total − sum of the known numbers.", tags=["averages"])
    if L == 3:
        n = r.choice([5, 6, 8]); avg = r.choice([30, 40, 50]); out, inn = r.choice([20, 24, 30]), r.choice([40, 48, 52])
        new = (avg * n - out + inn) / n
        return dict(stmt=f"The average weight of {n} players is {avg} kg. A player weighing {out} kg leaves and another weighing {inn} kg joins. What is the new average?", ans=new, cands=[avg + (inn - out), avg, (avg * n + inn) / (n + 1)], fmt=lambda x: nf(x) + " kg",
                    expl=f"New total = {avg*n} − {out} + {inn} = {avg*n-out+inn}; divide by {n}: {nf(new)} kg.", hint="Replace the individual in the total, not in the average, then divide by the (unchanged) count.", tags=["averages"])
    if L == 4:
        n1, a1, n2, a2 = r.choice([(30, 60, 20, 40), (12, 45, 8, 70), (15, 52, 25, 36), (10, 80, 40, 50)])
        v = (n1 * a1 + n2 * a2) / (n1 + n2)
        return dict(stmt=f"Class A has {n1} students with an average score of {a1}; class B has {n2} students with an average score of {a2}. What is the combined average?", ans=v, cands=[(a1 + a2) / 2, (n1 * a1 + n2 * a2) / n1, v + 2],
                    expl=f"Total marks = {n1}×{a1} + {n2}×{a2} = {n1*a1+n2*a2}; students = {n1+n2}; average = {nf(v)}. The simple mean of the two averages ({nf((a1+a2)/2)}) ignores class sizes.", hint="Weighted average = (n₁a₁ + n₂a₂)/(n₁ + n₂).", tags=["averages", "weighted average"])
    n, avg = r.choice([6, 8, 10]), r.choice([30, 36, 40]); age_left = r.choice([20, 24, 12]); newavg = (avg * n - age_left) / (n - 1)
    return dict(stmt=f"The average age of a team of {n} is {avg} years. One member aged {age_left} leaves the team. What is the average age of the remaining members?", ans=newavg, cands=[avg, avg + age_left / n, (avg * n + age_left) / (n - 1)], fmt=lambda x: nf(x),
                expl=f"Remaining total = {avg*n} − {age_left} = {avg*n-age_left}; remaining members = {n-1}; average = {nf(newavg)}.", hint="Subtract the leaver from the total and divide by the new count.", tags=["averages"])


def speed(r, L):
    if L == 1:
        s, t = r.choice([40, 60, 72, 80]), r.choice([2, 3, 4, 5])
        return dict(stmt=f"A car travels at {s} km/h for {t} hours. How far does it go?", ans=s * t, cands=[s / t, s + t, s * t * 2], fmt=lambda x: nf(x) + " km", expl=f"Distance = {s} × {t} = {s*t} km.", hint="Distance = speed × time.", tags=["speed and distance"])
    if L == 2:
        s = r.choice([18, 36, 54, 72, 90])
        return dict(stmt=f"Convert {s} km/h to m/s.", ans=s * 5 / 18, cands=[s * 18 / 5, s / 36, s * 5 / 36], fmt=lambda x: nf(x) + " m/s", expl=f"{s} × 5/18 = {nf(s*5/18)} m/s.", hint="km/h → m/s: multiply by 5/18.", tags=["speed and distance"])
    if L == 3:
        d, s1, s2 = r.choice([(120, 40, 60), (180, 30, 45), (240, 60, 40), (300, 50, 75)])
        avg = 2 * s1 * s2 / (s1 + s2)
        return dict(stmt=f"A person travels {d} km at {s1} km/h and returns along the same route at {s2} km/h. What is the average speed for the whole journey?", ans=avg, cands=[(s1 + s2) / 2, s1 * s2 / (s1 + s2), avg + 4], fmt=lambda x: nf(x) + " km/h",
                    expl=f"Total distance = {2*d}; total time = {d}/{s1} + {d}/{s2} = {nf(d/s1+d/s2)} h; average = {nf(avg)} km/h. Not the arithmetic mean.", hint="Average speed = total distance / total time. For equal distances use 2ab/(a + b).", tags=["speed and distance", "average speed"])
    if L == 4:
        v, t, pl = r.choice([(54, 20, 150), (72, 25, 300), (36, 30, 200)])
        ln = v * 5 / 18 * t - pl
        return dict(stmt=f"A train running at {v} km/h crosses a platform {pl} m long in {t} seconds. What is the length of the train?", ans=ln, cands=[v * 5 / 18 * t, pl, v * t - pl], fmt=lambda x: nf(x) + " m",
                    expl=f"Speed = {v}×5/18 = {nf(v*5/18)} m/s. Distance covered = {nf(v*5/18*t)} m = train + platform. Train = {nf(ln)} m.", hint="Crossing a platform: distance = train length + platform length. Convert km/h to m/s first (× 5/18).", tags=["speed and distance", "trains"])
    l1, l2, v1, v2 = r.choice([(150, 200, 60, 40), (120, 180, 72, 36), (200, 250, 54, 36)])
    t = (l1 + l2) / ((v1 + v2) * 5 / 18)
    return dict(stmt=f"Two trains of lengths {l1} m and {l2} m run on parallel tracks in opposite directions at {v1} km/h and {v2} km/h. How long (in seconds) do they take to cross each other completely?", ans=t,
                cands=[(l1 + l2) / ((v1 - v2) * 5 / 18), (l1 + l2) / (v1 + v2), t * 2], fmt=lambda x: nf(x) + " s",
                expl=f"Relative speed = ({v1}+{v2}) × 5/18 = {nf((v1+v2)*5/18)} m/s. Distance = {l1+l2} m. Time = {nf(t)} s.", hint="Opposite directions: add the speeds; distance = sum of the lengths.", tags=["speed and distance", "relative speed"])


def work(r, L):
    a, b = r.choice([(10, 15), (12, 6), (20, 30), (8, 24), (6, 3), (15, 10)])
    if L == 1:
        d = r.choice([2, 3, 4]); return dict(stmt=f"A can finish a job in {a*d} days. How much of the job does A finish in {d} days?", ans=Fraction(1, a), cands=[Fraction(1, a * d), Fraction(d, 1), Fraction(a, 1)], fmt=lambda f: str(Fraction(f)),
                                             expl=f"A does 1/{a*d} per day; in {d} days: {d}/{a*d} = 1/{a}.", hint="Work per day = 1 / (days to finish alone).", tags=["time and work"])
    if L == 2:
        t = Fraction(a * b, a + b)
        return dict(stmt=f"A can do a piece of work in {a} days and B in {b} days. Working together, in how many days will they finish it?", ans=t, cands=[Fraction(a + b, 2), a + b, Fraction(a * b, abs(a - b) or 1)], fmt=lambda f: nf(float(f)) + " days",
                    expl=f"Combined rate = 1/{a} + 1/{b} = {a+b}/{a*b}. Time = {a*b}/{a+b} = {nf(float(t))} days.", hint="Add the rates: 1/a + 1/b; time = 1 / combined rate.", tags=["time and work"])
    if L == 3:
        a, b, c = r.choice([(10, 15, 30), (12, 24, 8), (20, 30, 60), (6, 12, 4)]); t = 1 / (Fraction(1, a) + Fraction(1, b) + Fraction(1, c))
        return dict(stmt=f"A, B and C can complete a task alone in {a}, {b} and {c} days respectively. Working together how many days do they need?", ans=t, cands=[Fraction(a + b + c, 3), t + 1, Fraction(a * b * c, a + b + c)], fmt=lambda f: nf(float(f)) + " days",
                    expl=f"Rate = 1/{a} + 1/{b} + 1/{c} = {nf(float(1/t))}; time = {nf(float(t))} days.", hint="Add the three daily rates, then take the reciprocal.", tags=["time and work"])
    if L == 4:
        fill, leak = r.choice([(6, 12), (10, 15), (4, 12), (5, 20)]); t = 1 / (Fraction(1, fill) - Fraction(1, leak))
        return dict(stmt=f"A tap fills a tank in {fill} hours. A leak at the bottom empties the full tank in {leak} hours. If both are open, how long does it take to fill the empty tank?", ans=t, cands=[Fraction(fill * leak, fill + leak), Fraction(leak - fill), t + 2], fmt=lambda f: nf(float(f)) + " hours",
                    expl=f"Net rate = 1/{fill} − 1/{leak} = {nf(float(1/t))} per hour. Time = {nf(float(t))} hours.", hint="A leak is a negative rate: net rate = 1/fill − 1/leak.", tags=["time and work", "pipes"])
    a, b = r.choice([(12, 18), (10, 40), (20, 30), (15, 60)]); d = r.choice([2, 3, 4]); left = 1 - Fraction(d, a); t = left * b
    return dict(stmt=f"A can finish a job in {a} days and B in {b} days. A works alone for {d} days and leaves. How many more days does B need to finish the remaining work?", ans=t, cands=[Fraction(b - d), Fraction(a * b, a + b), t + 1], fmt=lambda f: nf(float(f)) + " days",
                expl=f"A completes {d}/{a} of the work, leaving {nf(float(left))}. B's rate is 1/{b}, so B needs {nf(float(left))} × {b} = {nf(float(t))} days.", hint="Subtract the work already done from 1, then divide by B's rate.", tags=["time and work"])


def series(r, L):
    if L == 1:
        a, d = r.randrange(2, 20), r.randrange(2, 9); s = [a + i * d for i in range(5)]
        return dict(stmt=f"Find the next number: {', '.join(map(str,s))}, ?", ans=a + 5 * d, cands=[a + 4 * d + 1, a + 6 * d, s[-1] * 2 - s[-2] + d], expl=f"Common difference {d}; next = {s[-1]} + {d} = {a+5*d}.", hint="Look at the difference between consecutive terms.", tags=["number series"])
    if L == 2:
        a, q = r.choice([2, 3, 5]), r.choice([2, 3]); s = [a * q ** i for i in range(5)]
        return dict(stmt=f"Find the next number: {', '.join(map(str,s))}, ?", ans=a * q ** 5, cands=[s[-1] + s[-2], s[-1] + q, s[-1] * (q + 1)], expl=f"Each term is {q} times the previous one; next = {s[-1]}×{q} = {a*q**5}.", hint="Check ratios of consecutive terms.", tags=["number series"])
    if L == 3:
        a, d, e = r.randrange(1, 10), r.randrange(1, 5), r.randrange(1, 4); s = [a]; step = d
        for _ in range(5): s.append(s[-1] + step); step += e
        return dict(stmt=f"Find the next number: {', '.join(map(str,s[:-1]))}, ?", ans=s[-1], cands=[s[-2] + (s[-2] - s[-3]), s[-2] + step - 2 * e, s[-2] * 2 - s[-3] + 1], expl=f"Differences: {', '.join(str(s[i+1]-s[i]) for i in range(len(s)-2))} — they grow by {e} each time, so the next difference is {s[-1]-s[-2]} and the answer is {s[-1]}.", hint="Take first differences; if they are not constant take second differences.", tags=["number series"])
    if L == 4:
        a, d, b, q = r.randrange(2, 9), r.randrange(2, 6), r.randrange(1, 4), r.choice([2, 3])
        arith = [a + i * d for i in range(5)]; geo = [b * q ** i for i in range(5)]
        shown = [v for i in range(4) for v in (arith[i], geo[i])][:7]
        ans = geo[3]
        return dict(stmt=f"The series interleaves two patterns. Find the next term: {', '.join(map(str, shown))}, ?", ans=ans, cands=[arith[4], ans + d, shown[-1] + shown[-2]],
                    expl=f"Odd positions: {', '.join(map(str, arith[:4]))} (add {d}); even positions: {', '.join(map(str, geo[:3]))} (multiply by {q}). The 8th term is the 4th even-position term = {geo[2]} × {q} = {ans}.",
                    hint="Split the series into odd-position and even-position terms and find each rule separately.", tags=["number series"])
    a = r.randrange(1, 6); s = [i * i + a for i in range(1, 7)]
    return dict(stmt=f"Find the next number: {', '.join(map(str,s))}, ?", ans=49 + a, cands=[49 + a + 2, 2 * s[-1] - s[-2] + 2, 50 + a], expl=f"The terms are n² + {a}: 1+{a}, 4+{a}, …; the 7th term is 49 + {a} = {49+a}.", hint="Compare the terms with perfect squares; subtract a constant.", tags=["number series"])


def counting(r, L):
    if L == 1:
        n = r.choice([3, 4, 5]); return dict(stmt=f"In how many different ways can {n} different books be arranged on a shelf?", ans=math.factorial(n), cands=[n * n, math.factorial(n - 1), n * 2], expl=f"{n}! = {math.factorial(n)}.", hint="n distinct objects can be arranged in n! ways.", tags=["permutations"])
    if L == 2:
        n, k = r.choice([(6, 3), (7, 2), (8, 3), (5, 3)]); return dict(stmt=f"In how many ways can a president, a secretary and a treasurer be chosen from {n} people if no person holds two posts? (Use {k} posts)".replace("a president, a secretary and a treasurer", f"{k} different posts"), ans=math.perm(n, k), cands=[math.comb(n, k), n ** k, math.factorial(n)], expl=f"Ordered selection: {n}P{k} = {math.perm(n,k)}.", hint="Different posts means order matters: nPr = n!/(n − r)!.", tags=["permutations"])
    if L == 3:
        n, k = r.choice([(8, 3), (10, 4), (7, 3), (9, 2)]); return dict(stmt=f"A committee of {k} is to be chosen from {n} people. In how many ways can this be done?", ans=math.comb(n, k), cands=[math.perm(n, k), n * k, math.comb(n, k) * 2], expl=f"Order does not matter: {n}C{k} = {math.comb(n,k)}.", hint="Selection without order: nCr = n! / (r!(n − r)!).", tags=["combinations"])
    if L == 4:
        w = r.choice(["LEVEL", "BANANA", "SUCCESS", "STATISTICS"][:3]); from collections import Counter
        c = Counter(w); v = math.factorial(len(w)); [v := v // math.factorial(x) for x in c.values()]
        return dict(stmt=f"How many distinct arrangements can be made from all the letters of the word {w}?", ans=v, cands=[math.factorial(len(w)), v * 2, math.factorial(len(w)) // 2], expl=f"{len(w)}! divided by the factorial of each repeat count ({', '.join(f'{k}:{x}' for k,x in c.items() if x>1)}) = {v}.", hint="Divide n! by the factorial of the count of each repeated letter.", tags=["permutations"])
    n = r.choice([5, 6, 7]); v = math.factorial(n - 1) * 2
    return dict(stmt=f"In how many ways can {n} people sit in a row if two particular people must sit together?", ans=math.factorial(n - 1) * 2, cands=[math.factorial(n), math.factorial(n - 1), math.factorial(n - 2) * 2], expl=f"Treat the pair as one unit: {n-1}! arrangements × 2 internal orders = {v}.", hint="Glue the pair into a single block, arrange blocks, then multiply by the pair's internal orderings.", tags=["permutations"])


def probability(r, L):
    if L == 1:
        k = r.choice([1, 2, 3]); return dict(stmt=f"A fair die is rolled once. What is the probability of getting a number greater than {6-k}?", ans=Fraction(k, 6), cands=[Fraction(1, 6), Fraction(6 - k, 6), Fraction(k, 3)], fmt=lambda f: str(Fraction(f)), expl=f"Favourable outcomes: {k} of 6 → {Fraction(k,6)}.", hint="Probability = favourable / total outcomes.", tags=["probability"])
    if L == 2:
        n = r.choice([2, 3]); return dict(stmt=f"A fair coin is tossed {n} times. What is the probability of getting all heads?", ans=Fraction(1, 2 ** n), cands=[Fraction(1, 2 * n), Fraction(1, 2), Fraction(n, 2 ** n)], fmt=lambda f: str(Fraction(f)), expl=f"Independent tosses: (1/2)^{n} = 1/{2**n}.", hint="Independent events multiply.", tags=["probability"])
    if L == 3:
        red, blue = r.choice([(4, 6), (5, 5), (3, 7), (6, 4)]); n = red + blue; p = Fraction(red, n) * Fraction(red - 1, n - 1)
        return dict(stmt=f"A bag has {red} red and {blue} blue balls. Two balls are drawn one after another without replacement. What is the probability that both are red?", ans=p, cands=[Fraction(red, n) ** 2, Fraction(red, n), Fraction(red * blue, n * (n - 1))], fmt=lambda f: str(Fraction(f)),
                    expl=f"{red}/{n} × {red-1}/{n-1} = {p}.", hint="Without replacement the second draw has one fewer ball of that colour and one fewer ball overall.", tags=["probability"])
    if L == 4:
        red, blue = r.choice([(5, 4), (6, 3), (4, 5)]); n = red + blue
        # P(second red | first blue)
        p = Fraction(red, n - 1)
        return dict(stmt=f"A bag contains {red} red and {blue} blue balls. One ball is drawn and is blue (not replaced). What is the probability the next ball is red?", ans=p, cands=[Fraction(red, n), Fraction(red, n - 2), Fraction(blue, n - 1)], fmt=lambda f: str(Fraction(f)),
                    expl=f"After removing a blue ball there are {n-1} balls, {red} of them red: {p}.", hint="Condition on what has been removed: recount the remaining balls.", tags=["probability", "conditional"])
    p1, p2, p3 = r.choice([(Fraction(1, 2), Fraction(1, 3), Fraction(1, 4)), (Fraction(1, 5), Fraction(1, 2), Fraction(1, 4)), (Fraction(1, 3), Fraction(1, 3), Fraction(1, 3))])
    v = 1 - (1 - p1) * (1 - p2) * (1 - p3)
    return dict(stmt=f"Three independent systems fail with probabilities {p1}, {p2} and {p3}. What is the probability that at least one fails?", ans=v, cands=[p1 + p2 + p3, p1 * p2 * p3, 1 - p1 * p2 * p3], fmt=lambda f: str(Fraction(f)),
                expl=f"P(none fail) = (1−{p1})(1−{p2})(1−{p3}) = {(1-p1)*(1-p2)*(1-p3)}; so P(at least one) = {v}.", hint="Use the complement: P(at least one) = 1 − P(none).", tags=["probability"])


def ages(r, L):
    a, b = r.randrange(20, 40), r.randrange(5, 15)
    if L == 1:
        return dict(stmt=f"Ravi is {a} years old and his son is {b} years old. What will be the sum of their ages after 5 years?", ans=a + b + 10, cands=[a + b + 5, a + b, a + b + 20], expl=f"Each ages 5 years: {a}+{b}+10 = {a+b+10}.", hint="Every person's age increases by the same number of years.", tags=["ages"])
    if L == 2:
        return dict(stmt=f"The sum of the ages of a father and son is {a+b} years and the father is {a-b} years older. How old is the son?", ans=b, cands=[a, (a + b) / 2, a - b], expl=f"Son = ((a+b) − (a−b))/2 = {b}.", hint="Smaller = (sum − difference)/2.", tags=["ages"])
    if L == 3:
        y = r.choice([4, 5, 6]); x = r.choice([2, 3]); s = r.randrange(5, 12); f = x * (s) 
        # father is x times the son's age now; y years ago father was ... keep simple: father = x*son
        fa = x * s
        return dict(stmt=f"A father is {x} times as old as his son. {y} years from now the sum of their ages will be {fa+s+2*y}. How old is the son now?", ans=s, cands=[fa, s + y, s - y], expl=f"Let son = s, father = {x}s. After {y} years the sum is {x+1}s + {2*y} = {fa+s+2*y}, so s = {s}.", hint="Let the son's age be s; write the father's age in terms of s and form one equation.", tags=["ages", "algebra"])
    if L == 4:
        s = r.choice([6, 8, 10]); k = r.choice([3, 4]); y = r.choice([4, 6]); f = k * s  # now f = k*s ; after y years ratio?
        fy, sy = f + y, s + y
        fr = Fraction(fy, sy)
        return dict(stmt=f"The present age of a mother is {k} times that of her daughter. After {y} years the ratio of mother's to daughter's age will be {fr.numerator}:{fr.denominator}. What is the daughter's present age?", ans=s, cands=[f, s + y, f - y], expl=f"Let daughter = d: ({k}d + {y})/(d + {y}) = {fr.numerator}/{fr.denominator}. Solving gives d = {s}.", hint="Write both ages in terms of d, form the ratio equation and cross-multiply.", tags=["ages", "algebra"])
    a_, b_, c_ = r.choice([(24, 30, 36), (20, 28, 40), (18, 27, 45)]); d = r.choice([4, 6])
    return dict(stmt=f"The total of the ages of A, B and C is {a_+b_+c_} years. {d} years ago A was {a_-d} years old and B was {b_-d} years old. How old is C now?", ans=c_, cands=[c_ - d, c_ + d, a_ + b_],
                expl=f"A is now {a_} and B is now {b_}, so C = {a_+b_+c_} − {a_+b_} = {c_}.", hint="Convert 'x years ago' statements into present ages, then use the total.", tags=["ages"])


def alligation(r, L):
    if L <= 2:
        a, b, ka, kb = r.choice([(40, 60, 1, 1), (30, 50, 2, 3), (20, 35, 3, 2)]); ka, kb = ka * r.choice([1, 2]), kb * r.choice([1, 2])
        v = Fraction(a * ka + b * kb, ka + kb)
        return dict(stmt=f"{ka} kg of rice at {a} per kg is mixed with {kb} kg of rice at {b} per kg. What is the price per kg of the mixture?", ans=v, cands=[Fraction(a + b, 2), Fraction(a * kb + b * ka, ka + kb), v + 3], fmt=lambda f: nf(float(f)), expl=f"Total cost = {a*ka + b*kb}; total weight = {ka+kb}; mean price = {nf(float(v))}.", hint="Mixture price = total cost / total quantity.", tags=["mixtures"])
    if L == 3:
        a, b, m = r.choice([(40, 60, 54), (20, 50, 35), (30, 70, 58)])
        q = Fraction(m - a, b - m)
        return dict(stmt=f"In what ratio must tea costing {a} per kg be mixed with tea costing {b} per kg to get a blend worth {m} per kg?", ans=Fraction(b - m, m - a), cands=[Fraction(m - a, b - m), Fraction(b, a), Fraction(m, b)], fmt=lambda f: f"{Fraction(f).numerator}:{Fraction(f).denominator}",
                    expl=f"By alligation: cheaper : dearer = ({b} − {m}) : ({m} − {a}) = {b-m}:{m-a} = {Fraction(b-m,m-a).numerator}:{Fraction(b-m,m-a).denominator}.", hint="Alligation: cheaper : dearer = (dearer − mean) : (mean − cheaper).", tags=["mixtures", "alligation"])
    if L == 4:
        tot, p, rem = r.choice([(40, 25, 10), (60, 50, 12), (80, 25, 20)])
        milk_after = tot * (1 - Fraction(rem, tot)) ** 2
        return dict(stmt=f"A vessel contains {tot} litres of pure milk. {rem} litres are removed and replaced by water; then {rem} litres of the mixture are removed and replaced by water again. How much milk is left?", ans=milk_after, cands=[tot - 2 * rem, Fraction(tot * (tot - rem), tot), milk_after + 2], fmt=lambda f: nf(float(f)) + " litres",
                    expl=f"Milk left = {tot} × (1 − {rem}/{tot})² = {nf(float(milk_after))} litres.", hint="After n replacements: remaining = initial × (1 − removed/total)ⁿ.", tags=["mixtures", "replacement"])
    a, b, m = r.choice([(50, 80, 62), (30, 90, 50), (24, 60, 36)]); total = r.choice([30, 45, 60, 90])
    x = Fraction(total * (b - m), b - a)
    return dict(stmt=f"A trader wants {total} kg of a mixture priced at {m} per kg using two grades priced {a} and {b} per kg. How many kg of the {a}-grade are needed?", ans=x, cands=[Fraction(total * (m - a), b - a), total / 2, Fraction(total * a, a + b)], fmt=lambda f: nf(float(f)) + " kg",
                expl=f"Ratio cheap:dear = ({b}−{m}):({m}−{a}) = {b-m}:{m-a}. Cheap grade = {total} × {b-m}/{b-a} = {nf(float(x))} kg.", hint="Find the ratio by alligation, then split the total by that ratio.", tags=["mixtures", "alligation"])


def sets(r, L):
    A, B = r.choice([(30, 25), (40, 35), (50, 30)]); both = r.choice([5, 8, 10]); n = A + B - both + r.choice([0, 6, 10])
    if L == 1:
        return dict(stmt=f"In a group, {A} people like tea, {B} like coffee and {both} like both. How many like at least one of them?", ans=A + B - both, cands=[A + B, A + B + both, A - both], expl=f"|A ∪ B| = {A} + {B} − {both} = {A+B-both}.", hint="|A ∪ B| = |A| + |B| − |A ∩ B|.", tags=["sets"])
    if L == 2:
        return dict(stmt=f"{A} students study maths, {B} study physics and {both} study both. How many study only maths?", ans=A - both, cands=[A, A + B - both, A - B], expl=f"Only maths = {A} − {both} = {A-both}.", hint="Only A = |A| − |A ∩ B|.", tags=["sets"])
    if L == 3:
        return dict(stmt=f"Out of {n} employees, {A} use Python, {B} use R and {both} use both. How many use neither?", ans=n - (A + B - both), cands=[n - A - B, n - both, A + B - both], expl=f"At least one = {A+B-both}; neither = {n} − {A+B-both} = {n-(A+B-both)}.", hint="Neither = total − |A ∪ B|.", tags=["sets"])
    ab, bc, ac, abc = 6, 5, 4, 2
    A, B, C = r.choice([(20, 18, 15), (25, 22, 20)])
    if L == 4:
        u = A + B + C - ab - bc - ac + abc
        return dict(stmt=f"In a survey, {A} like A, {B} like B and {C} like C. {ab} like A and B, {bc} like B and C, {ac} like A and C, and {abc} like all three. How many like at least one?", ans=u, cands=[A + B + C - ab - bc - ac, A + B + C, u + abc], expl=f"|A∪B∪C| = {A}+{B}+{C} − {ab} − {bc} − {ac} + {abc} = {u}.", hint="Inclusion–exclusion: add singles, subtract pairs, add the triple intersection.", tags=["sets"])
    u = A + B + C - ab - bc - ac + abc; only_a = A - ab - ac + abc
    return dict(stmt=f"In a survey, {A} like A, {B} like B and {C} like C. {ab} like A and B, {bc} like B and C, {ac} like A and C, and {abc} like all three. How many like only A?", ans=only_a, cands=[A - ab - ac, A - abc, A - ab], expl=f"Only A = {A} − {ab} − {ac} + {abc} = {only_a} (the triple overlap was subtracted twice).", hint="Only A = |A| − |A∩B| − |A∩C| + |A∩B∩C|.", tags=["sets"])


def algebra(r, L):
    x = r.randrange(2, 12)
    if L == 1:
        a, b = r.randrange(2, 6), r.randrange(1, 10); return dict(stmt=f"If {a}x + {b} = {a*x+b}, find x.", ans=x, cands=[x + 1, (a * x + b) / a, x - 1 if x > 1 else x + 2], expl=f"{a}x = {a*x}, so x = {x}.", hint="Isolate x: subtract the constant, then divide.", tags=["algebra"])
    if L == 2:
        a, b = x + r.randrange(2, 9), x; return dict(stmt=f"The sum of two numbers is {a+b} and their difference is {a-b}. Find the larger number.", ans=a, cands=[b, a + b, a - b], expl=f"Larger = (sum + difference)/2 = {a}.", hint="Larger = (sum + difference)/2.", tags=["algebra"])
    if L == 3:
        p, q = r.randrange(2, 9), r.randrange(1, 9); return dict(stmt=f"Two pens and three notebooks cost {2*p+3*q}. One pen and one notebook cost {p+q}. What is the cost of one pen?", ans=p, cands=[q, p + q, 2 * p], expl=f"Subtract 2×(second equation): 3q − 2q = q = {q}; then pen = {p+q} − {q} = {p}.", hint="Eliminate one variable by multiplying the second equation by 2 and subtracting.", tags=["algebra", "simultaneous equations"])
    if L == 4:
        n = r.randrange(5, 30); return dict(stmt=f"The sum of three consecutive integers is {3*n}. What is the product of the smallest and largest?", ans=(n - 1) * (n + 1), cands=[n * n, n * (n + 1), (n - 2) * n], expl=f"The integers are {n-1}, {n}, {n+1}; product of the extremes = {(n-1)*(n+1)}.", hint="Call the middle integer m; the others are m − 1 and m + 1.", tags=["algebra"])
    a, b = r.randrange(2, 9), r.randrange(2, 9); return dict(stmt=f"If the roots of x² − Sx + P = 0 are {a} and {b}, what is S² − 2P?", ans=a * a + b * b, cands=[(a + b) ** 2, a * b, a + b], expl=f"S = {a+b}, P = {a*b}; S² − 2P = {(a+b)**2} − {2*a*b} = {a*a+b*b} (= a² + b²).", hint="For roots a and b: sum = S, product = P; a² + b² = S² − 2P.", tags=["algebra", "quadratics"])


def clocks(r, L):
    h, m = r.choice([(3, 0), (6, 0), (9, 0), (4, 0)]) if L <= 3 else r.choice([(3, 20), (4, 40), (7, 30), (2, 10)])
    ang = abs(30 * h - 5.5 * m); ang = min(ang, 360 - ang)
    return dict(stmt=f"What is the smaller angle between the hour and minute hands of a clock at {h}:{m:02d}?", ans=ang, cands=[360 - ang if 360 - ang != ang else ang + 15, abs(30 * h - 6 * m), 30 * h % 180], fmt=lambda x: nf(x) + "°",
                expl=f"Angle = |30h − 5.5m| = |{30*h} − {nf(5.5*m)}| = {nf(abs(30*h-5.5*m))}°; the smaller angle is {nf(ang)}°.", hint="Angle = |30h − 5.5m| degrees (take 360 minus it if it exceeds 180).", tags=["clocks"], _min=3)


def geometry(r, L):
    l, b = r.randrange(5, 20), r.randrange(3, 12)
    if L == 1:
        return dict(stmt=f"A rectangle is {l} m long and {b} m wide. What is its area?", ans=l * b, cands=[2 * (l + b), l + b, l * l], fmt=lambda x: nf(x) + " m²", expl=f"{l} × {b} = {l*b} m².", hint="Area of a rectangle = length × width.", tags=["geometry"])
    if L == 2:
        rr = r.choice([7, 14, 21]); return dict(stmt=f"What is the circumference of a circle of radius {rr} cm? (Use π = 22/7)", ans=2 * 22 * rr / 7, cands=[22 * rr * rr / 7, 22 * rr / 7, 4 * 22 * rr / 7], fmt=lambda x: nf(x) + " cm", expl=f"2πr = 2 × 22/7 × {rr} = {nf(2*22*rr/7)} cm.", hint="Circumference = 2πr.", tags=["geometry"])
    if L == 3:
        p, q = r.choice([(20, 10), (10, 10), (20, 20), (30, 10)]); new = (100 + p) * (100 - q) / 100 - 100
        return dict(stmt=f"The length of a rectangle is increased by {p}% and its breadth is decreased by {q}%. What is the percentage change in its area?", ans=new, cands=[p - q, p + q, new + 3], fmt=pc, expl=f"Area multiplier = {1+p/100} × {1-q/100} = {nf((1+p/100)*(1-q/100))}. Change = {nf(new)}%.", hint="Area scales by (1 + p/100)(1 − q/100).", tags=["geometry", "percentages"])
    if L == 4:
        s = r.choice([6, 8, 10, 12]); return dict(stmt=f"The diagonal of a square is {s}√2 cm. What is the area of the square?", ans=s * s, cands=[2 * s * s, s * 2, s * s * 2 // 4], fmt=lambda x: nf(x) + " cm²", expl=f"Side = diagonal/√2 = {s} cm; area = {s*s} cm².", hint="Diagonal = side × √2.", tags=["geometry"])
    a, b = r.choice([(3, 4), (5, 12), (8, 15), (7, 24)]); k = r.choice([2, 3])
    return dict(stmt=f"A right-angled triangle has legs {a*k} cm and {b*k} cm. What is the length of the altitude drawn to the hypotenuse?", ans=Fraction(a * b * k, math.isqrt(a * a + b * b)), cands=[Fraction(a * k * b * k, (a + b) * k), Fraction(a * b * k, 1), Fraction(a * k + b * k, 2)], fmt=lambda f: nf(float(f)) + " cm",
                expl=f"Hypotenuse = {math.isqrt(a*a+b*b)*k} cm. Area = ½ × {a*k} × {b*k}. Altitude = 2·Area/hypotenuse = {nf(a*k*b*k/(math.isqrt(a*a+b*b)*k))} cm.", hint="Area = ½·legs product = ½·hypotenuse·altitude.", tags=["geometry"])


def remainder(r, L):
    if L <= 2:
        a, b = r.randrange(50, 300), r.choice([7, 9, 11, 13]); return dict(stmt=f"What is the remainder when {a} is divided by {b}?", ans=a % b, cands=[a // b, (a % b + 1) % b, b - a % b], expl=f"{a} = {b} × {a//b} + {a%b}.", hint="Remainder = a − b × floor(a/b).", tags=["number system"])
    if L == 3:
        base, k = r.choice([(7, 2023), (3, 1998), (9, 2011), (2, 2025)]); ans = pow(base, k, 10)
        return dict(stmt=f"What is the last digit of {base}^{k}?", ans=ans, cands=[base, (ans + 2) % 10, (ans + 4) % 10], expl=f"Last digits of powers of {base} repeat with period 4: {', '.join(str(pow(base, i, 10)) for i in range(1, 5))}. {k} mod 4 = {k%4}, giving {ans}.", hint="Last digits of powers repeat in a cycle (length at most 4); reduce the exponent mod the cycle length.", tags=["number system"])
    if L == 4:
        lo, hi, d = r.choice([(100, 500, 7), (200, 900, 13), (50, 400, 9)]); v = hi // d - (lo - 1) // d
        return dict(stmt=f"How many integers from {lo} to {hi} (inclusive) are divisible by {d}?", ans=v, cands=[v + 1, v - 1, (hi - lo) // d + 2], expl=f"⌊{hi}/{d}⌋ − ⌊{lo-1}/{d}⌋ = {hi//d} − {(lo-1)//d} = {v}.", hint="Count multiples ≤ n as ⌊n/d⌋ and subtract the count below the range.", tags=["number system"])
    a, b = r.choice([(12, 18), (24, 36), (30, 45), (16, 40)]); g = math.gcd(a, b); l = a * b // g; k = r.choice([3, 5])
    return dict(stmt=f"Two lights blink every {a} and {b} minutes respectively. They blink together now. After how many minutes will they next blink together?", ans=l, cands=[g, a * b, l * 2], expl=f"LCM({a}, {b}) = {l}.", hint="They coincide again after the LCM of the two periods.", tags=["number system", "LCM"])


def logic(r, L):
    n = {1: 3, 2: 4, 3: 5, 4: 5, 5: 6}[L]
    names = r.sample(["Asha", "Bela", "Chen", "Dev", "Esha", "Farid", "Gita"], n)
    order = names[:]                      # tallest -> shortest
    r.shuffle(order)
    forms = ["{hi} is taller than {lo}"] if L <= 2 else ["{hi} is taller than {lo}", "{lo} is shorter than {hi}", "{lo} is not taller than {hi}"]
    clues = [r.choice(forms).format(hi=order[i], lo=order[i + 1]) for i in range(n - 1)]
    r.shuffle(clues)
    pos = r.randrange(0, n)
    ask = ["tallest", "shortest"] if L == 1 else [f"{pos+1}{['st','nd','rd'][pos] if pos < 3 else 'th'} tallest"]
    which = ask[r.randrange(len(ask))]
    ans = order[0] if which == "tallest" else order[-1] if which == "shortest" else order[pos]
    note = " All heights are different." if L > 2 else ""
    return dict(stmt=f"{'; '.join(clues)}.{note} Who is the {which}?", ans=ans, cands=[x for x in names if x != ans] + ["Cannot be determined"], fmt=str,
                expl=f"Chain the statements: {' > '.join(order)} (tallest to shortest). The {which} is {ans}.", hint="Arrange the people in a chain from the comparisons, then read off the requested position.", tags=["logical reasoning"])


FAMILIES = {
    "percent": (percent, 1), "profit": (profit, 1), "interest": (interest, 1), "ratio": (ratio, 1), "average": (average, 1), "speed": (speed, 1), "work": (work, 1),
    "series": (series, 1), "counting": (counting, 1), "probability": (probability, 1), "ages": (ages, 1), "alligation": (alligation, 1), "sets": (sets, 1),
    "algebra": (algebra, 1), "clocks": (clocks, 3), "geometry": (geometry, 1), "remainder": (remainder, 1), "logic": (logic, 1),
}
LEVEL_PLAN = {1: [1] * 11 + [2] * 4, 2: [1] * 3 + [2] * 5 + [3] * 7, 3: [2] * 2 + [3] * 11 + [4] * 2, 4: [3] * 5 + [4] * 7 + [5] * 3, 5: [4] * 5 + [5] * 10}
DIFF = {1: "easy", 2: "easy", 3: "medium", 4: "hard", 5: "hard"}


_SEEN = set()      # statements already used by any OA (aptitude questions never repeat across assessments)


def build_aptitude(oa: int):
    """15 aptitude MCQs for OA `oa` (1..5): distinct families, levels follow LEVEL_PLAN, answers computed."""
    r = random.Random(7000 + oa)
    levels = LEVEL_PLAN[oa][:]
    names = list(FAMILIES)
    out, used = [], set()
    for L in levels:
        for _ in range(2000):
            fam = r.choice(names)
            fn, minL = FAMILIES[fam]
            if fam in used or L < minL:
                continue
            d = fn(r, L)
            if d["stmt"] in _SEEN:
                continue
            used.add(fam); _SEEN.add(d["stmt"])
            break
        else:
            raise RuntimeError("no family")
        ans, w = options(d["ans"], d["cands"], d.get("fmt", nf))
        out.append(MCQ("APT", d["tags"] + ["aptitude"], DIFF[L], d["stmt"], ans, w, d["expl"]))
        out[-1].hint = d["hint"]
    return out


if __name__ == "__main__":
    for oa in range(1, 6):
        qs = build_aptitude(oa)
        print(oa, len(qs), [q.diff for q in qs].count("easy"), [q.diff for q in qs].count("hard"))
    for q in build_aptitude(3)[:6]:
        print(q.stmt, "->", q.correct, q.wrongs, "|", q.hint)
