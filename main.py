from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse
import yfinance as yf
import numpy as np
import time

app = FastAPI()

# ================= CONFIG =================
USERNAME = "5th"
PASSWORD = "ave"
logged_in = False

CACHE_TTL = 60 * 60 * 24  # 24 hours
DATA_CACHE = {}          # {(ticker, period): (timestamp, data)}

# ================= STOCK UNIVERSES =================
STOCK_UNIVERSES = {
    "growth": {
        "NVIDIA (NVDA)": "NVDA",
        "Tesla (TSLA)": "TSLA",
        "Meta Platforms (META)": "META",
        "Amazon (AMZN)": "AMZN",
        "Alphabet (GOOGL)": "GOOGL",
        "Netflix (NFLX)": "NFLX",
    },
    "core": {
        "Apple (AAPL)": "AAPL",
        "Microsoft (MSFT)": "MSFT",
        "Visa (V)": "V",
        "Berkshire Hathaway (BRK.B)": "BRK-B",
    },
    "defensive": {
        "Johnson & Johnson (JNJ)": "JNJ",
        "Procter & Gamble (PG)": "PG",
        "Coca-Cola (KO)": "KO",
        "PepsiCo (PEP)": "PEP",
    },
    "cyclical": {
        "Exxon Mobil (XOM)": "XOM",
        "Chevron (CVX)": "CVX",
        "JPMorgan Chase (JPM)": "JPM",
    }
}

# ================= HELPERS =================
def horizon_to_period(horizon: str) -> str:
    if "3 months" in horizon:
        return "3mo"
    if "6 months" in horizon:
        return "6mo"
    if "1 year" in horizon:
        return "1y"
    if "2–3" in horizon:
        return "3y"
    if "4–5" in horizon:
        return "5y"
    if "6–10" in horizon or "10+" in horizon:
        return "10y"
    return "1y"


def select_universes(risk: int, horizon: str):
    selected = []

    if risk <= 3:
        selected = ["defensive", "core"]
    elif risk <= 6:
        selected = ["core", "growth"]
    else:
        selected = ["growth", "cyclical"]

    if "3 months" in horizon or "6 months" in horizon:
        selected = [u for u in selected if u != "growth"]

    return selected


def get_stock_metrics_cached(ticker: str, period: str):
    key = (ticker, period)
    now = time.time()

    if key in DATA_CACHE:
        ts, data = DATA_CACHE[key]
        if now - ts < CACHE_TTL:
            return data

    try:
        df = yf.download(ticker, period=period, progress=False)
        if df.empty:
            return None

        start = float(df["Close"].iloc[0])
        end = float(df["Close"].iloc[-1])
        ret = (end - start) / start * 100
        vol = df["Close"].pct_change().std() * np.sqrt(252) * 100

        result = {
            "return": round(ret, 2),
            "volatility": round(vol, 2)
        }

        DATA_CACHE[key] = (now, result)
        return result

    except Exception:
        return None

# ================= UI BUILDERS =================
def login_page(error=False):
    error_html = "<p style='color:#f87171;'>Login failed</p>" if error else ""
    return f"""
    <html>
    <body style="background:#0f172a;color:white;font-family:Arial;
                 height:100vh;display:flex;justify-content:center;align-items:center;">
        <div style="background:#020617;padding:40px;width:380px;border-radius:12px;text-align:center;">
            <h1>Advisor Assistant</h1>

            <div style="background:#1e293b;padding:10px;font-size:12px;border-radius:6px;margin-bottom:15px;">
                Research tool only. Historical data. Not investment advice.
            </div>

            <form method="post" action="/login">
                <input name="username" placeholder="Username" required
                       style="width:100%;padding:12px;margin-top:10px;">
                <input type="password" name="password" placeholder="Password" required
                       style="width:100%;padding:12px;margin-top:10px;">
                <button type="submit"
                        style="width:100%;padding:12px;margin-top:10px;
                               background:#4f46e5;color:white;font-weight:bold;border:none;">
                    Login
                </button>
            </form>

            {error_html}

            <div style="margin-top:15px;font-size:11px;color:#94a3b8;">
                Created by Justin Brown
            </div>
        </div>
    </body>
    </html>
    """


def profile_page():
    ages = "".join(f"<option>{i}</option>" for i in range(18, 101))
    risks = "".join(f"<option>{i}</option>" for i in range(1, 11))

    return f"""
    <html>
    <body style="background:#0f172a;color:white;font-family:Arial;
                 height:100vh;display:flex;justify-content:center;align-items:center;">
        <div style="background:#020617;padding:40px;width:450px;border-radius:12px;">
            <h2>Investor Profile</h2>

            <form method="post" action="/profile">
                <label>Age</label>
                <select name="age">{ages}</select>

                <label>Income</label>
                <select name="income">
                    <option>10k–20k</option><option>20k–40k</option>
                    <option>40k–60k</option><option>60k–80k</option>
                    <option>80k–100k</option><option>100k–150k</option>
                    <option>150k–300k</option><option>300k–500k</option>
                    <option>500k–1M</option><option>1M+</option>
                </select>

                <label>Risk (1–10)</label>
                <select name="risk">{risks}</select>

                <label>Horizon</label>
                <select name="horizon">
                    <option>3 months</option><option>6 months</option>
                    <option>1 year</option><option>2–3 years</option>
                    <option>4–5 years</option><option>6–10 years</option>
                    <option>10+ years</option>
                </select>

                <button type="submit"
                        style="width:100%;padding:12px;margin-top:15px;
                               background:#4f46e5;color:white;font-weight:bold;border:none;">
                    View Results
                </button>
            </form>
        </div>
    </body>
    </html>
    """

# ================= ROUTES =================
@app.get("/", response_class=HTMLResponse)
def home():
    return login_page()


@app.post("/login", response_class=HTMLResponse)
def login(username: str = Form(...), password: str = Form(...)):
    global logged_in
    if username == USERNAME and password == PASSWORD:
        logged_in = True
        return RedirectResponse("/profile", status_code=302)
    return login_page(error=True)


@app.get("/profile", response_class=HTMLResponse)
def profile():
    if not logged_in:
        return RedirectResponse("/", status_code=302)
    return profile_page()


@app.post("/profile", response_class=HTMLResponse)
def submit_profile(
    age: int = Form(...),
    income: str = Form(...),
    risk: int = Form(...),
    horizon: str = Form(...)
):
    period = horizon_to_period(horizon)
    universes = select_universes(risk, horizon)

    cards = ""
    assets = []

    for u in universes:
        for name, ticker in STOCK_UNIVERSES[u].items():
            metrics = get_stock_metrics_cached(ticker, period)
            if not metrics:
                continue
            score = metrics["return"] / max(metrics["volatility"], 1)
            assets.append((score, name, ticker, metrics))

    assets.sort(reverse=True)
    assets = assets[:10]

    if not assets:
        cards = """
        <div style="background:#020617;padding:20px;border-radius:10px;">
            <h3>No results available</h3>
            <p>Market data may be temporarily unavailable.</p>
        </div>
        """
    else:
        for score, name, ticker, m in assets:
            cards += f"""
            <div style="background:#020617;padding:20px;border-radius:10px;">
                <h3>{name}</h3>
                <p>Return: {m['return']}%</p>
                <p>Volatility: {m['volatility']}%</p>
                <p>Score: {round(score,2)}</p>
                <a href="https://finance.yahoo.com/quote/{ticker}" target="_blank">
                    Read more →
                </a>
            </div>
            """

    if age >= 50:
        cards += """
        <div style="background:#020617;padding:20px;border-radius:10px;">
            <h3>Vanguard Total Bond ETF (BND)</h3>
            <p>Lower-volatility income asset</p>
            <a href="https://finance.yahoo.com/quote/BND" target="_blank">
                Read more →
            </a>
        </div>
        """

    return f"""
    <html>
    <body style="background:#0f172a;color:white;font-family:Arial;padding:40px;">
        <h2>Suggested Assets</h2>
        <p>Age: {age} | Risk: {risk} | Horizon: {horizon}</p>

        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:20px;">
            {cards}
        </div>
    </body>
    </html>
    """
