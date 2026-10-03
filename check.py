"""Controlla le taglie di uno o più articoli Zalando e avvisa su Telegram
quando una taglia che ti interessa torna disponibile."""

import json
import os
import re
import sys

from curl_cffi import requests

CONFIG_FILE = "config.json"
STATE_FILE = "state.json"
MAX_ERRORI = 8  # dopo 8 controlli falliti di fila (~2 ore) ti avvisa

TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")


def invia(testo):
    if not TOKEN or not CHAT_ID:
        print("[telegram non configurato]", testo)
        return
    r = requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": testo, "parse_mode": "HTML"},
        timeout=20,
    )
    if r.status_code != 200:
        print("Errore Telegram:", r.status_code, r.text[:300])


def scarica(url):
    r = requests.get(
        url,
        impersonate="chrome",
        timeout=40,
        headers={"Accept-Language": "it-IT,it;q=0.9,en;q=0.8"},
    )
    return r.status_code, r.text


def leggi_taglie(pagina):
    """Restituisce {taglia: True/False} cercando i dati di stock nella pagina."""
    t = pagina.replace('\\"', '"').replace("\\u002F", "/")
    taglie = {}
    for m in re.finditer(r'"size"\s*:\s*"([^"]{1,15})"', t):
        taglia = m.group(1).strip()
        finestra = t[m.end(): m.end() + 1200]
        prossima = re.search(r'"size"\s*:', finestra)
        if prossima:
            finestra = finestra[: prossima.start()]

        disponibile = None
        q = re.search(r'"quantity"\s*:\s*"([A-Z_]+)"', finestra)
        if q:
            disponibile = q.group(1) != "OUT_OF_STOCK"
        else:
            a = re.search(r'"(?:isAvailable|available|inStock|isInStock)"\s*:\s*(true|false)', finestra)
            if a:
                disponibile = a.group(1) == "true"
            else:
                a = re.search(r"(InStock|OutOfStock|SoldOut)", finestra)
                if a:
                    disponibile = a.group(1) == "InStock"

        if disponibile is not None:
            taglie[taglia] = taglie.get(taglia, False) or disponibile
    return taglie


def salva_debug(nome, codice, pagina):
    """Salva cosa ha ricevuto da Zalando, per capire perché non legge le taglie."""
    titolo = re.search(r"<title[^>]*>(.*?)</title>", pagina, re.S)
    righe = [
        f"articolo: {nome}",
        f"HTTP: {codice}",
        f"lunghezza pagina: {len(pagina)}",
        f"titolo: {titolo.group(1).strip()[:200] if titolo else '-'}",
    ]
    for k in ['"size"', '"simples"', "OUT_OF_STOCK", '"quantity"', "captcha", "akamai", "sec-cpt", "Access Denied"]:
        righe.append(f"{k}: {pagina.count(k)}")
    righe += ["", "---- inizio pagina ----", pagina[:6000]]
    with open("debug.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(righe))


def norm(s):
    return str(s).strip().lower().replace(",", ".")


def main():
    test = "--test" in sys.argv
    config = json.load(open(CONFIG_FILE, encoding="utf-8"))
    try:
        stato = json.load(open(STATE_FILE, encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        stato = {}

    for art in config["articoli"]:
        nome, url = art.get("nome", "Articolo"), art["url"]
        volute = [norm(s) for s in art["taglie"]]
        chiave_err = f"errori|{url}"

        try:
            codice, pagina = scarica(url)
        except Exception as e:
            codice, pagina = 0, str(e)

        taglie = leggi_taglie(pagina) if codice == 200 else {}
        print(f"{nome}: HTTP {codice}, taglie lette: {taglie}")

        if not taglie:
            salva_debug(nome, codice, pagina)
            stato[chiave_err] = stato.get(chiave_err, 0) + 1
            if stato[chiave_err] == MAX_ERRORI or test:
                invia(
                    f"⚠️ Non riesco a leggere le taglie di <b>{nome}</b> "
                    f"(HTTP {codice}). Zalando potrebbe bloccare il bot o aver cambiato la pagina."
                )
            continue
        stato[chiave_err] = 0

        lette = {norm(k): v for k, v in taglie.items()}

        if test:
            riga = ", ".join(f"{k} {'✅' if v else '❌'}" for k, v in taglie.items())
            invia(f"🤖 Bot attivo per <b>{nome}</b>\nTaglie viste: {riga}\nTi avviso per: {', '.join(art['taglie'])}")

        for taglia in volute:
            ora = bool(lette.get(taglia))
            chiave = f"{url}|{taglia}"
            prima = stato.get(chiave, False)
            if ora and not prima:
                invia(f"🔔 <b>{nome}</b>: la taglia <b>{taglia.upper()}</b> è di nuovo disponibile!\n{url}")
            if taglia not in lette:
                print(f"  attenzione: taglia '{taglia}' non trovata nella pagina")
            stato[chiave] = ora

    json.dump(stato, open(STATE_FILE, "w", encoding="utf-8"), indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
"""Controlla le taglie di uno o più articoli Zalando e avvisa su Telegram
quando una taglia che ti interessa torna disponibile."""

import json
import os
import re
import sys

from curl_cffi import requests

CONFIG_FILE = "config.json"
STATE_FILE = "state.json"
MAX_ERRORI = 8  # dopo 8 controlli falliti di fila (~2 ore) ti avvisa

TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")


def invia(testo):
    if not TOKEN or not CHAT_ID:
        print("[telegram non configurato]", testo)
        return
    r = requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": testo, "parse_mode": "HTML"},
        timeout=20,
    )
    if r.status_code != 200:
        print("Errore Telegram:", r.status_code, r.text[:300])


def scarica(url):
    r = requests.get(
        url,
        impersonate="chrome",
        timeout=40,
        headers={"Accept-Language": "it-IT,it;q=0.9,en;q=0.8"},
    )
    return r.status_code, r.text


def leggi_taglie(pagina):
    """Restituisce {taglia: True/False} cercando i dati di stock nella pagina."""
    t = pagina.replace('\\"', '"').replace("\\u002F", "/")
    taglie = {}
    for m in re.finditer(r'"size"\s*:\s*"([^"]{1,15})"', t):
        taglia = m.group(1).strip()
        finestra = t[m.end(): m.end() + 1200]
        prossima = re.search(r'"size"\s*:', finestra)
        if prossima:
            finestra = finestra[: prossima.start()]

        disponibile = None
        q = re.search(r'"quantity"\s*:\s*"([A-Z_]+)"', finestra)
        if q:
            disponibile = q.group(1) != "OUT_OF_STOCK"
        else:
            a = re.search(r'"(?:isAvailable|available|inStock|isInStock)"\s*:\s*(true|false)', finestra)
            if a:
                disponibile = a.group(1) == "true"
            else:
                a = re.search(r"(InStock|OutOfStock|SoldOut)", finestra)
                if a:
                    disponibile = a.group(1) == "InStock"

        if disponibile is not None:
            taglie[taglia] = taglie.get(taglia, False) or disponibile
    return taglie


def norm(s):
    return str(s).strip().lower().replace(",", ".")


def main():
    test = "--test" in sys.argv
    config = json.load(open(CONFIG_FILE, encoding="utf-8"))
    try:
        stato = json.load(open(STATE_FILE, encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        stato = {}

    for art in config["articoli"]:
        nome, url = art.get("nome", "Articolo"), art["url"]
        volute = [norm(s) for s in art["taglie"]]
        chiave_err = f"errori|{url}"

        try:
            codice, pagina = scarica(url)
        except Exception as e:
            codice, pagina = 0, str(e)

        taglie = leggi_taglie(pagina) if codice == 200 else {}
        print(f"{nome}: HTTP {codice}, taglie lette: {taglie}")

        if not taglie:
            stato[chiave_err] = stato.get(chiave_err, 0) + 1
            if stato[chiave_err] == MAX_ERRORI or test:
                invia(
                    f"⚠️ Non riesco a leggere le taglie di <b>{nome}</b> "
                    f"(HTTP {codice}). Zalando potrebbe bloccare il bot o aver cambiato la pagina."
                )
            continue
        stato[chiave_err] = 0

        lette = {norm(k): v for k, v in taglie.items()}

        if test:
            riga = ", ".join(f"{k} {'✅' if v else '❌'}" for k, v in taglie.items())
            invia(f"🤖 Bot attivo per <b>{nome}</b>\nTaglie viste: {riga}\nTi avviso per: {', '.join(art['taglie'])}")

        for taglia in volute:
            ora = bool(lette.get(taglia))
            chiave = f"{url}|{taglia}"
            prima = stato.get(chiave, False)
            if ora and not prima:
                invia(f"🔔 <b>{nome}</b>: la taglia <b>{taglia.upper()}</b> è di nuovo disponibile!\n{url}")
            if taglia not in lette:
                print(f"  attenzione: taglia '{taglia}' non trovata nella pagina")
            stato[chiave] = ora

    json.dump(stato, open(STATE_FILE, "w", encoding="utf-8"), indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
