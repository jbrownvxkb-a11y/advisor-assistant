from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse
import yfinance as yf
import numpy as np
import time

app = FastAPI()

# ---------------- CONFIG ----------------
USERNAME = "5th"
PASSWORD = "ave"
logged_in = False

CACHE_TTL = 60 * 60 * 24  # 24 hours
DATA_CACHE = {}          # {(ticker, period): (timestamp, data)}


# ---------------- REAL DATA HELPERS ----------------
def horizon_to_period(horizon: str):
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


def get_stock_metrics_cached(ticker: str, period: str):
    cache_key = (ticker, period)
    now = time.time()

    # Return cached data if fresh
    if cache_key in DATA_CACHE:
        ts, data = DATA_CACHE[cache_key]
        if now - ts < CACHE_TTL:
            return data

    # Fetch real data
    data = yf.download(ticker, period=period, progress=False)

    if data.empty:
        return None

    start_price = data["Close"].iloc[0]
    end_price = data["Close"].iloc[-1]

    total_return = (end_price - start_price) / start_price * 100
    volatility = data["Close"].pct_change().std() * np.sqrt(252) * 100

    result = {
        "return": round(total_return, 2),
        "volatility": round(volatility, 2)
    }

    DATA_CACHE[cache_key] = (now, result)
    return result


STOCKS = {
    "Apple (AAPL)": "AAPL",
    "Microsoft (MSFT)": "MSFT",
    "NVIDIA (NVDA)": "NVDA",
    "Amazon (AMZN)": "AMZN",
    "Alphabet (GOOGL)": "GOOGL",
    "Meta Platforms (META)": "META",
    "Tesla (TSLA)": "TSLA",
    "Berkshire Hathaway (BRK.B)": "BRK-B",
    "Visa (V)": "V",
    "Johnson & Johnson (JNJ)": "JNJ"
}


# ---------------- LOGIN PAGE ----------------
def login_page(error=False):
    error_html = "<p style='color:#f87171;'>Login failed</p>" if error else ""

    return f"""
    <html>
    <head>
        <title>Advisor Assistant</title>
        <style>
            body {{
                background:#0f172a;
                color:white;
                font-family:Arial;
                height:100vh;
                display:flex;
                justify-content:center;
                align-items:center;
            }}
            .card {{
                background:#020617;
                padding:40px;
                width:380px;
                border-radius:12px;
                text-align:center;
            }}
            .warning {{
                background:#1e293b;
                color:#cbd5f5;
                font-size:12px;
                padding:10px;
                border-radius:6px;
                margin-bottom:15px;
            }}
            input,button {{
                width:100%;
                padding:12px;
                margin-top:10px;
            }}
            button {{
                background:#4f46e5;
                border:none;
                color:white;
                font-weight:bold;
            }}
            .footer {{
                margin-top:15px;
                font-size:11px;
                color:#94a3b8;
            }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>Advisor Assistant</h1>

            <div class="warning">
                Research tool only. Not investment advice.
                Market data is historical and informational.
            </div>

            <form method="post" action="/login">
                <input name="username" placeholder="Username" required>
                <input type="password" name="password" placeholder="Password" required>
                <button type="submit">Login</button>
            </form>

            {error_html}

            <div class="footer">
                Created by Justin Brown
            </div>
        </div>
    </body>
    </html>
    """


# ---------------- PROFILE PAGE ----------------
def profile_page():
    age_opts = "".join(f"<option>{i}</option>" for i in range(18, 101))
    risk_opts = "".join(f"<option>{i}</option>" for i in range(1, 11))

    return f"""
    <html>
    <head>
        <style>
            body {{
                background:#0f172a;
                color:white;
                font-family:Arial;
                display:flex;
                justify-content:center;
                align-items:center;
                height:100vh;
            }}
            .card {{
                background:#020617;
                padding:40px;
                width:450px;
                border-radius:12px;
            }}
            select,button {{
                width:100%;
                padding:10px;
                margin-bottom:15px;
            }}
            button {{
                background:#4f46e5;
                border:none;
                color:white;
                font-weight:bold;
            }}
        </style>
    </head>
    <body>
        <div class="card">
            <h2>Investor Profile</h2>
            <form method="post" action="/profile">
                <label>Age</label>
                <select name="age">{age_opts}</select>

                <label>Income</label>
                <select name="income">
                    <option>10k–20k</option>
                    <option>20k–40k</option>
                    <option>40k–60k</option>
                    <option>60k–80k</option>
                    <option>80k–100k</option>
                    <option>100k–150k</option>
                    <option>150k–300k</option>
                    <option>300k–500k</option>
                    <option>500k–1M</option>
                    <option>1M+</option>
                </select>

                <label>Risk (1–10)</label>
                <select name="risk">{risk_opts}</select>

                <label>Horizon</label>
                <select name="horizon">
                    <option>3 months</option>
                    <option>6 months</option>
                    <option>1 year</option>
                    <option>2–3 years</option>
                    <option>4–5 years</option>
                    <option>6–10 years</option>
                    <option>10+ years</option>
                </select>

                <button type="submit">View Results</button>
            </form>
        </div>
    </body>
    </html>
    """


# ---------------- ROUTES ----------------
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
def submit_profile(age: int = Form(...), income: str = Form(...),
                   risk: int = Form(...), horizon: str = Form(...)):

    period = horizon_to_period(horizon)
    cards = ""

    for name, ticker in STOCKS.items():
        metrics = get_stock_metrics_cached(ticker, period)
        if not metrics:
            continue

        cards += f"""
        <div class="card">
            <h3>{name}</h3>
            <p><b>Return:</b> {metrics['return']}%</p>
            <p><b>Volatility:</b> {metrics['volatility']}%</p>
            <a href="https://finance.yahoo.com/quote/{ticker}" target="_blank">
                Read more →
            </a>
        </div>
        """

    if age >= 50:
        cards += """
        <div class="card">
            <h3>Vanguard Total Bond ETF (BND)</h3>
            <p>Lower volatility income-focused asset</p>
            <a href="https://finance.yahoo.com/quote/BND" target="_blank">
                Read more →
            </a>
        </div>
        """

    return f"""
    <html>
    <head>
        <style>
            body {{
                background:#0f172a;
                color:white;
                font-family:Arial;
                padding:40px;
            }}
            .grid {{
                display:grid;
                grid-template-columns:repeat(auto-fit,minmax(260px,1fr));
                gap:20px;
            }}
            .card {{
                background:#020617;
                padding:20px;
                border-radius:10px;
            }}
            a {{
                color:#60a5fa;
                text-decoration:none;
                font-weight:bold;
            }}
        </style>
    </head>
    <body>
        <h2>Suggested Assets</h2>
        <p>Age: {age} | Risk: {risk} | Horizon: {horizon}</p>

        <div class="grid">
            {cards}
        </div>
    </body>
    </html>
    """
