from __future__ import annotations
import threading, time
from fastapi import FastAPI
from bot_daytrade.loop import run_bot_forever, stop_signal, last_heartbeat

app = FastAPI()

thread_handle = None

def _start_loop():
    t = threading.Thread(target=run_bot_forever, name="bot-loop", daemon=True)
    t.start()
    return t

@app.on_event("startup")
def _startup():
    global thread_handle
    thread_handle = _start_loop()

@app.get("/healthz")
def healthz():
    hb = last_heartbeat()
    running = not stop_signal.is_set()
    return {"ok": True, "running": running, "last_heartbeat": hb}

@app.on_event("shutdown")
def _shutdown():
    stop_signal.set()
    time.sleep(0.5)
