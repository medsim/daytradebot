
import os, pathlib

ENV_SYMS = os.getenv("UNIVERSE", "")
UNIVERSE_FILE = os.getenv("UNIVERSE_FILE", "")

HARDCODED = ["AAPL","MSFT","NVDA","AMZN","META","GOOGL","GOOG","TSLA","AMD","NFLX",
"AVGO","CRM","COST","PEP","ADBE","CSCO","LIN","INTC","QCOM","TXN",
"AMAT","IBM","ORCL","PYPL","NOW","PANW","SNOW","SHOP","ABNB","UBER",
"PLTR","MU","INTU","BKNG","MRVL","ARM","SMCI","TSM","V","MA",
"JPM","BAC","WFC","C","MS","GS","T","VZ","KO","PG",
"PFE","MRK","JNJ","LLY","ABBV","TMO","UNH","CVS","BMY","AMGN",
"XOM","CVX","COP","SLB","EOG","FANG","ET","OXY","MPC","PSX",
"NKE","SBUX","HD","LOW","TGT","WMT","DG","DPZ","MCD","KO",
"CAT","DE","BA","GE","LMT","RTX","HON","MMM","F","GM"]

def _read_file(path):
    p = pathlib.Path(path)
    if not p.exists(): return []
    return [ln.strip().upper() for ln in p.read_text().splitlines() if ln.strip()]

def symbols():
    if UNIVERSE_FILE:
        s = _read_file(UNIVERSE_FILE)
        if s: return s
    if ENV_SYMS:
        s = [x.strip().upper() for x in ENV_SYMS.split(",") if x.strip()]
        if s: return s
    return HARDCODED
