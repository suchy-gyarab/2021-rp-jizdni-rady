from dataclasses import dataclass, field
from pprint import pprint
import datetime
from collections import defaultdict


@dataclass
class Stanice:
    nazev: str
    pocet_linek: int
    vzdalenost: int
    max_linka: "Linka" = None
    linky: list["Linka"] = field(default_factory=list, repr=False)
    prijezdy: set[int] = field(default_factory=set)
    mozna: bool = True


@dataclass
class Linka:
    nazev: str
    hmin: int
    hmax: int
    f: int
    pocet_stanic: int
    stanice: list[Stanice] = field(repr=False)
    offset: int = 0
    odjezdy: set[int] = field(default_factory=set)


def vzdalenost(l: Linka, s: Stanice | str):
    if type(s) is str:
        s = next(filter(lambda x: x.nazev == s, l.stanice))
    if s not in l.stanice:
        return 0

    v = 0
    for i in l.stanice:
        if i is s:
            break
        v += i.vzdalenost

    return v


def vyber_stanici(stanice: list[Stanice]) -> Stanice:
    out = list(filter(lambda x: x.mozna, stanice))
    if len(out) == 1:
        return out[0]
    stanice = out
    m = 0
    out = []
    for s in stanice:
        if len(s.prijezdy) > m:
            out = []
            m = len(s.prijezdy)
        if len(s.prijezdy) >= m:
            out.append(s)
    if len(out) == 1:
        return out[0]
    stanice = out
    m = 0
    out = []
    for s in stanice:
        if s.pocet_linek > m:
            out = []
            m = s.pocet_linek
        if s.pocet_linek >= m:
            out.append(s)
    if len(out) == 1:
        return out[0]
    stanice = out
    m = 99999999999
    out = []
    for s in stanice:
        v = vzdalenost(s.max_linka, s)
        if v < m:
            out = []
            m = v
        if v <= m:
            out.append(s)
    return out[0]


def main(stanice_, linky_, cas):
    # inicializace
    pprint(stanice_)
    pprint(linky_)
    stanice = [
        Stanice(
            nazev=i[0],
            pocet_linek=sum([j.isalpha() for j in i[0]]),
            vzdalenost=int(i[1]),
        )
        for i in stanice_
    ]
    linky = []
    for linka in linky_:
        seznam_stanic = linka[13:]
        for i in range(len(seznam_stanic)):
            seznam_stanic[i] = next(j for j in stanice if j.nazev == seznam_stanic[i])
        l = Linka(
            nazev=linka[0],
            hmin=round(0.8 * int(linka[cas])),
            hmax=min(40, round(1.2 * int(linka[cas]))),
            f=round(60 / int(linka[cas])),
            pocet_stanic=len(seznam_stanic),
            stanice=seznam_stanic,
        )
        linky.append(l)

    stanice = list(filter(lambda x: x.pocet_linek > 1, stanice))

    for s in stanice:
        s.max_linka = max(linky, key=lambda x: vzdalenost(x, s))
        s.linky = list(filter(lambda x: s in x.stanice, linky))

    odjezdy = sum([l.f for l in linky])

    # velká smyčka - hlavní algoritmus
    while odjezdy > 0:
        s = vyber_stanici(stanice)
        print(f"Vybraná stanice {s.nazev}")
        if len(s.prijezdy) == 0:
            # proceduraN
            # nastav rozestupy
            max_min = max(s.linky, key=lambda x: x.hmin).hmin
            min_max = max(s.linky, key=lambda x: x.hmax).hmax
            rozestup = None
            if max_min < min_max:
                rozestup = max_min

            # nastav počáteční odjezd
            max_vzdalenost = vzdalenost(s.max_linka, s)
            for linka in s.linky:
                v = vzdalenost(linka, s)
                linka.offset = max_vzdalenost - v

            # zaplň příjezdy na stanice
            for i in range(0, 60 if rozestup else 1, rozestup if rozestup else 1):
                for linka in s.linky:
                    if len(linka.odjezdy) == linka.f or linka.offset + i > 60:
                        continue
                    odjezd = linka.offset + i
                    linka.odjezdy.add(odjezd)
                    odjezdy -= 1
                    for s_ in linka.stanice:
                        v = vzdalenost(linka, s_)
                        s_.prijezdy.add(odjezd + v)
        elif s.mozna:
            # proceduraS
            zmena = False
            for linka in s.linky:
                if linka.f > len(linka.odjezdy):
                    v = vzdalenost(linka, s)
                    try:
                        posledni_odjezd = max(linka.odjezdy)
                    except ValueError:
                        posledni_odjezd = 0
                    min_prijezd = posledni_odjezd + linka.hmin + v
                    max_prijezd = posledni_odjezd + linka.hmax + v
                    for prijezd in s.prijezdy:
                        if min_prijezd <= prijezd <= max_prijezd and linka.f > len(
                            linka.odjezdy
                        ):
                            linka.odjezdy.add(prijezd - v)
                            for s_ in linka.stanice:
                                v_ = vzdalenost(linka, s_)
                                s_.prijezdy.add(prijezd - v + v_)
                            odjezdy -= 1
                            zmena = True
            s.mozna = zmena

        if not any([s.mozna for s in stanice]):
            # proceduraL
            nema_odjezdy = [l for l in linky if len(l.odjezdy) < l.f]
            if not nema_odjezdy:
                break
            linka = max(nema_odjezdy, key=lambda x: len(x.stanice))
            posledni_odjezd = max(linka.odjezdy) if linka.odjezdy else 0
            linka.odjezdy.add(min(posledni_odjezd + linka.hmin, 60))
            odjezdy -= 1
            for s in linka.stanice:
                s.mozna = True

        # breakpoint()

    return linky


if __name__ == "__main__":

    # inicializace a načtení dat
    start = datetime.datetime.fromtimestamp(0) + datetime.timedelta(hours=5)
    stanice = []
    with open("stanice.tsv") as f:
        for line in f.readlines():
            stanice.append(line.strip().split("\t"))

    linky = []
    with open("linky.tsv") as f:
        for line in f.readlines():
            linky.append(line.strip().split("\t"))

    # spouštění algoritmu pro každý časový interval
    cas = 1
    vysledky = []
    for i in range(1, 13):
        vysledky.append(main(stanice, linky, i))

    # spojení výsledků do lepšího formátu -> časy relativní k začátku dne
    odjezdy_linek = {"A": [], "B": [], "C": [], "D": [], "E": []}
    for i, vysledek in enumerate(vysledky):
        for linka in vysledek:
            print(f"Linka {linka.nazev} {i=} {linka.f=}: {sorted(list(linka.odjezdy))}")
            print()
            odjezdy_linek[linka.nazev].extend(
                sorted([60 * i + o for o in linka.odjezdy])
            )

    pprint(odjezdy_linek)

    # zapsání stonkolistu jízdního řádu do souboru output.tsv
    linky = vysledky[0]
    stanice = ["AC0", "AB1", "AD2", "AE3", "BC4", "BD5", "CD6", "CE7"]
    f = open("output.tsv", "w+")
    for s in stanice:
        print(f"Stanice {s}", file=f)
        for linka in linky:
            hodiny = defaultdict(list)
            try:
                v = vzdalenost(linka, s)
            except StopIteration:
                continue
            print(f"Linka {linka.nazev}", file=f)
            for odjezd in odjezdy_linek[linka.nazev]:
                cas = start + datetime.timedelta(minutes=odjezd + v)
                hodiny[cas.hour].append(cas.minute)
            for hodina in sorted(hodiny.keys()):
                x = "\t".join([str(y) for y in sorted(hodiny[hodina])])
                print(f"{hodina}\t{x}", file=f)
        print(file=f)
    f.close()
