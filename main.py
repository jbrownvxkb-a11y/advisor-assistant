import yfinance as yf
import pandas as pd
import numpy as np

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse

app = FastAPI()

# ---------------- CONFIG ----------------
USERNAME = "5th"
PASSWORD = "ave"
logged_in = False


# ---------------- LOGIN PAGE ----------------
def login_page(error=False):
    error_html = "<p style='color:#f87171;'>Login failed</p>" if error else ""

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Advisor Assistant</title>
        <style>
            body {{
                margin: 0;
                height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                background: #0f172a;
                font-family: Arial, sans-serif;
                color: white;
            }}
            .card {{
                background: #020617;
                padding: 40px;
                width: 360px;
                border-radius: 12px;
                box-shadow: 0 0 30px rgba(0,0,0,0.6);
                text-align: center;
            }}
            h1 {{
                font-size: 28px;
                margin-bottom: 25px;
            }}
            input {{
                width: 100%;
                padding: 12px;
                margin-top: 10px;
                border-radius: 6px;
                border: none;
            }}
            button {{
                margin-top: 20px;
                width: 100%;
                padding: 12px;
                background: #4f46e5;
                border: none;
                border-radius: 6px;
                color: white;
                font-weight: bold;
                cursor: pointer;
            }}
            button:hover {{
                background: #4338ca;
            }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>Advisor Assistant</h1>
            <form method="post" action="/login">
                <input name="username" placeholder="Username" required>
                <input type="password" name="password" placeholder="Password" required>
                <button type="submit">Login</button>
            </form>
            {error_html}
        </div>
    </body>
    </html>
    """


# ---------------- PROFILE PAGE ----------------
def profile_page():
    age_options = "".join(f"<option>{i}</option>" for i in range(18, 101))
    risk_options = "".join(f"<option>{i}</option>" for i in range(1, 11))

    return f"""
    <html>
    <head>
        <title>Investor Profile</title>
        <style>
            body {{
                background: #0f172a;
                color: white;
                font-family: Arial;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
            }}
            .card {{
                background: #020617;
                padding: 40px;
                width: 450px;
                border-radius: 12px;
            }}
            label {{
                font-weight: bold;
            }}
            select {{
                width: 100%;
                padding: 10px;
                margin: 6px 0 16px 0;
                border-radius: 6px;
                border: none;
            }}
            button {{
                width: 100%;
                padding: 12px;
                background: #4f46e5;
                border: none;
                border-radius: 6px;
                color: white;
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
        <div class="card">
            <h2 style="text-align:center;">Investor Profile</h2>

            <form method="post" action="/profile">
                <label>Age</label>
                <select name="age">{age_options}</select>

                <label>Annual Income</label>
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

                <label>Risk Tolerance (1–10)</label>
                <select name="risk">{risk_options}</select>

                <label>Investment Horizon</label>
                <select name="horizon">
                    <option>3 months</option>
                    <option>6 months</option>
                    <option>1 year</option>
                    <option>2–3 years</option>
                    <option>4–5 years</option>
                    <option>6–10 years</option>
                    <option>10+ years</option>
                </select>

                <button type="submit">Continue</button>
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
def submit_profile(
    age: int = Form(...),
    income: str = Form(...),
    risk: int = Form(...),
    horizon: str = Form(...)
):
    if not logged_in:
        return RedirectResponse("/", status_code=302)

    # -------- ASSETS --------
    assets = [
        ("Apple (AAPL)", "Stock", "+18%", "12%", "https://finance.yahoo.com/quote/AAPL"),
        ("Microsoft (MSFT)", "Stock", "+22%", "14%", "https://finance.yahoo.com/quote/MSFT"),
        ("NVIDIA (NVDA)", "Stock", "+95%", "38%", "https://finance.yahoo.com/quote/NVDA"),
        ("Amazon (AMZN)", "Stock", "+45%", "16%", "https://finance.yahoo.com/quote/AMZN"),
        ("Alphabet (GOOGL)", "Stock", "+34%", "15%", "https://finance.yahoo.com/quote/GOOGL"),
        ("Meta Platforms (META)", "Stock", "+60%", "20%", "https://finance.yahoo.com/quote/META"),
        ("Tesla (TSLA)", "Stock", "+12%", "18%", "https://finance.yahoo.com/quote/TSLA"),
        ("Berkshire Hathaway (BRK.B)", "Stock", "+20%", "13%", "https://finance.yahoo.com/quote/BRK-B"),
        ("Visa (V)", "Stock", "+25%", "14%", "https://finance.yahoo.com/quote/V"),
        ("Johnson & Johnson (JNJ)", "Stock", "+10%", "9%", "https://finance.yahoo.com/quote/JNJ"),
    ]

    if age >= 50:
        assets.extend([
            ("US Treasury 10Y Note", "Bond", "+3.8%", "4%", "https://www.treasurydirect.gov"),
            ("Vanguard Total Bond ETF (BND)", "Bond ETF", "+5%", "4.5%", "https://investor.vanguard.com")
        ])

    cards = ""
    for name, typ, recent, yearly, link in assets:
        cards += f"""
        <div class="card">
            <h3>{name}</h3>
            <p><b>Type:</b> {typ}</p>
            <p><b>Recent Performance:</b> {recent}</p>
            <p><b>Avg Yearly Return:</b> {yearly}</p>
            <a href="{link}" target="_blank">Read more →</a>
        </div>
        """

    return f"""
    <html>
    <head>
        <title>Top Assets</title>
        <style>
            body {{
                background: #0f172a;
                color: white;
                font-family: Arial;
                margin: 0;
                padding: 40px;
            }}
            h2 {{
                text-align: center;
            }}
            .summary {{
                text-align: center;
                color: #cbd5f5;
                margin-bottom: 30px;
            }}
            .grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
                gap: 20px;
            }}
            .card {{
                background: #020617;
                padding: 20px;
                border-radius: 10px;
            }}
            a {{
                color: #60a5fa;
                font-weight: bold;
                text-decoration: none;
            }}
        </style>
    </head>
    <body>
        <h2>Suggested Assets (Research Only)</h2>
        <p class="summary">
            Age: {age} | Income: {income} | Risk: {risk} | Horizon: {horizon}
        </p>

        <div class="grid">
            {cards}
        </div>

        <p style="margin-top:40px;color:#94a3b8;text-align:center;">
            Educational purposes only. Not financial advice.
        </p>
    </body>
    </html>
    """
