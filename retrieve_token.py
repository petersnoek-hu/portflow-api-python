"""
Haal de Portflow bearer token op via een browservenster en sla hem op in .env.

Werking (zelfde aanpak als docs/safari-browser-extension.js):
  1. Open een Chrome-venster met een eigen, blijvend profiel (zodat je login bewaard blijft).
  2. Ga naar de Portflow-tool in Canvas. Log zo nodig in.
  3. Luister naar alle uitgaande requests (ook vanuit het Portflow-iframe) en onderschep
     de 'Authorization: Bearer ...' header naar portflow.io / hu.nl / drieam.app.
  4. Controleer de token tegen /api/v1/dashboard en schrijf hem als PORTFLOW_BEARER_TOKEN in .env.

Gebruik:
  python retrieve_token.py [--config pad/naar/.env] [--timeout 300]

Vereist:
  Python 3.10+, requests, playwright en Google Chrome (of Playwright Chromium).
  Bij het starten wordt gecontroleerd of deze aanwezig zijn; ontbrekende onderdelen
  kunnen direct geïnstalleerd worden.
"""

import sys

MIN_PYTHON = (3, 10)


def check_python() -> None:
    """Controleer de Python-versie vóór de rest van het script geladen wordt."""
    version = ".".join(str(v) for v in sys.version_info[:3])
    print("Python: " + version + " (" + sys.executable + ")")
    if sys.version_info < MIN_PYTHON:
        need = ".".join(str(v) for v in MIN_PYTHON)
        sys.exit("Python " + need + " of hoger is vereist; gevonden: " + version + ".")


if __name__ == "__main__":
    check_python()

import argparse
import importlib.metadata
import importlib.util
import platform
import re
import shutil
import subprocess
import time
from pathlib import Path
from urllib.parse import urlparse

CANVAS_URL = "https://canvas.hu.nl/courses/51659/external_tools/1134"
API_BASE_URL = "https://portfolio.drieam.app/api/v1"
TOKEN_HOST_SUFFIXES = ("portflow.io", "hu.nl", "drieam.app")
ENV_KEY = "PORTFLOW_BEARER_TOKEN"


def _get_exe_dir() -> Path:
    """Geef de map terug van het uitvoerbare bestand (PyInstaller-compatibel)."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


# Browserprofiel naast het script, zodat de Canvas/HU-login tussen runs bewaard blijft
PROFILE_DIR = _get_exe_dir() / ".browser-profile"


def _ask_yes(question: str) -> bool:
    answer = input(f"{question} [J/n] ").strip().lower()
    return answer in ("", "j", "ja", "y", "yes")


def ensure_package(module: str, pip_name: str) -> None:
    """Controleer of een Python-pakket aanwezig is; bied installatie aan als het ontbreekt."""
    if importlib.util.find_spec(module) is None:
        print(f"Python-pakket '{pip_name}' is niet geïnstalleerd.")
        if getattr(sys, 'frozen', False) or not _ask_yes(f"'{pip_name}' nu installeren met {sys.executable}?"):
            sys.exit(f"Installeer het met: {sys.executable} -m pip install {pip_name}")
        subprocess.run([sys.executable, "-m", "pip", "install", pip_name], check=True)
        importlib.invalidate_caches()
    print(f"{pip_name}: {importlib.metadata.version(pip_name)}")


def find_chrome() -> Path | None:
    """Zoek een geïnstalleerde Google Chrome (het 'chrome'-kanaal van Playwright)."""
    system = platform.system()
    if system == "Darwin":
        candidates = [
            Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
            Path.home() / "Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        ]
    elif system == "Windows":
        import os
        candidates = [
            Path(os.environ.get(var, "")) / "Google/Chrome/Application/chrome.exe"
            for var in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA")
            if os.environ.get(var)
        ]
    else:
        candidates = [Path(p) for p in (shutil.which("google-chrome"), shutil.which("google-chrome-stable")) if p]
    return next((c for c in candidates if c.exists()), None)


def parse_args():
    parser = argparse.ArgumentParser(description="Haal de Portflow bearer token op via de browser")
    parser.add_argument(
        "--config",
        default=str(_get_exe_dir() / ".env"),
        help="Pad naar het .env configuratiebestand (standaard: map van het script)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Maximaal aantal seconden wachten op de token (standaard: 300)",
    )
    return parser.parse_args()


def _host_matches(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return any(host == s or host.endswith("." + s) for s in TOKEN_HOST_SUFFIXES)


def check_token(token: str) -> int:
    """Live controle van de token tegen een bekend Portflow API-endpoint; geeft de HTTP-status terug."""
    import requests
    try:
        r = requests.get(
            f"{API_BASE_URL}/dashboard",
            headers={"Authorization": f"Bearer {token}", "accept": "*/*"},
            timeout=15,
        )
        return r.status_code
    except requests.RequestException:
        return 0


def save_token_to_env(token: str, env_path: Path) -> None:
    """Schrijft de bearer token naar .env (vervangt een eventuele bestaande waarde)."""
    if env_path.exists():
        content = env_path.read_text(encoding="utf-8")
        if re.search(rf"^{ENV_KEY}=", content, flags=re.MULTILINE):
            content = re.sub(
                rf"^{ENV_KEY}=.*$",
                lambda _m: f"{ENV_KEY}={token}",
                content,
                flags=re.MULTILINE,
            )
        else:
            content = f"{ENV_KEY}={token}\n" + content
    else:
        content = f"{ENV_KEY}={token}\n"
    env_path.write_text(content, encoding="utf-8")
    print(f"Token opgeslagen in {env_path}")


def _launch_context(p):
    """Start Chrome met een blijvend profiel; val terug op Playwright's Chromium."""
    from playwright.sync_api import Error as PlaywrightError

    # chromium_sandbox=True voorkomt dat Playwright Chrome met --no-sandbox start
    kwargs = dict(user_data_dir=str(PROFILE_DIR), headless=False, no_viewport=True, chromium_sandbox=True)

    chrome = find_chrome()
    if chrome:
        print(f"Browser: Google Chrome ({chrome})")
        kwargs["channel"] = "chrome"
    else:
        chromium = Path(p.chromium.executable_path)
        print("Google Chrome niet gevonden.")
        if not chromium.exists():
            if getattr(sys, 'frozen', False) or not _ask_yes("Playwright Chromium nu installeren?"):
                sys.exit(f"Installeer Google Chrome, of voer uit: {sys.executable} -m playwright install chromium")
            subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
        print(f"Browser: Playwright Chromium ({chromium})")

    try:
        context = p.chromium.launch_persistent_context(**kwargs)
    except PlaywrightError:
        sys.exit(
            "Browser kon niet starten. Staat er nog een browservenster van een eerdere run open?\n"
            f"Sluit dat venster (profiel: {PROFILE_DIR}) en probeer opnieuw."
        )
    if context.browser:
        print(f"Browserversie: {context.browser.version}")
    return context


def capture_token(timeout_s: int) -> str | None:
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import sync_playwright

    candidates: list[str] = []
    seen: set[str] = set()

    def on_request(request):
        if not _host_matches(request.url):
            return
        auth = request.headers.get("authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:].strip()
            if token and token not in seen:
                seen.add(token)
                candidates.append(token)
                print("Bearer token onderschept, bezig met controleren...")

    with sync_playwright() as p:
        context = _launch_context(p)
        # Luister op context-niveau: vangt ook requests uit iframes en nieuwe tabbladen
        context.on("request", on_request)

        page = context.pages[0] if context.pages else context.new_page()
        print(f"Openen: {CANVAS_URL}")
        print("Log zo nodig in; het venster sluit automatisch zodra de token is gevonden.")
        try:
            page.goto(CANVAS_URL, wait_until="domcontentloaded")
        except PlaywrightError as e:
            print(f"Waarschuwing bij laden van de pagina: {e}")

        token = None
        deadline = time.monotonic() + timeout_s
        try:
            while time.monotonic() < deadline:
                while candidates:
                    candidate = candidates.pop(0)
                    status = check_token(candidate)
                    if status == 200:
                        token = candidate
                        break
                    print(f"Onderschepte token is niet geldig voor de Portflow API (HTTP {status}), wacht op volgende...")
                if token:
                    break
                if not context.pages:
                    print("Browservenster gesloten voordat er een token gevonden is.")
                    break
                # Laat Playwright events verwerken (time.sleep zou de event loop blokkeren)
                context.pages[0].wait_for_timeout(500)
            else:
                print(f"Geen geldige token gevonden binnen {timeout_s} seconden.")
        except PlaywrightError:
            print("Browservenster gesloten voordat er een token gevonden is.")
        finally:
            try:
                context.close()
            except PlaywrightError:
                pass
        return token


def main():
    args = parse_args()
    env_path = Path(args.config)
    if not env_path.is_absolute():
        env_path = (Path.cwd() / env_path).resolve()

    ensure_package("requests", "requests")
    ensure_package("playwright", "playwright")

    token = capture_token(args.timeout)
    if not token:
        sys.exit(1)
    save_token_to_env(token, env_path)


if __name__ == "__main__":
    main()
