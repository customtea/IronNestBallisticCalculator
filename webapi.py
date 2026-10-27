from typing import IO
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse, JSONResponse
# from main import IronNestShell
from webui import IronNestShell
import io
from contextlib import redirect_stdout

with open("./cdu_webui/cdu.html") as f:
    MAINPAGE = f.read()

app = FastAPI()

ironnest = IronNestShell()
def get_shell(sessionId) -> IronNestShell:
    return ironnest


@app.get("/", response_class=JSONResponse)
async def root():
    return JSONResponse("Hello World")


@app.get("/main", response_class=JSONResponse)
async def mainpage():
    return HTMLResponse(MAINPAGE)




@app.post("/api/command", response_class=JSONResponse)
async def api_command(request: Request):
    body = await request.json()
    # print(body)
    line = body["line"]
    sessionId = body["session"]
    shell = get_shell(sessionId)
    buf = io.StringIO()
    with redirect_stdout(buf):
        shell.onecmd(line)
    output = buf.getvalue()

    if output is None:
        output = ""

    return JSONResponse({"output":output, "session":sessionId}, media_type="application/json")
