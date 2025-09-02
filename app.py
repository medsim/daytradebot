from typing import List, Optional
from fastapi import FastAPI, Query
from pydantic import BaseModel

app = FastAPI(title="Trading Bot API", version="1.0.0")

class Order(BaseModel):
    id: str
    symbol: str
    side: str
    qty: int
    status: str

class Position(BaseModel):
    symbol: str
    qty: int
    avg_price: float

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.get("/")
def root():
    return {"service": "Trading Bot API", "status": "running"}

@app.get("/orders", response_model=List[Order])
def list_orders(status: Optional[str] = Query(default=None)):
    return []

@app.get("/positions", response_model=List[Position])
def list_positions():
    return []
