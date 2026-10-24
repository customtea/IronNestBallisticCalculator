#!/usr/bin/env python3
"""設定ファイル(TOML/JSON)とHTMLテンプレートから、静的な cdu.html を生成する。

使い方:
    python generate_cdu.py                         # cdu_config.toml + cdu_template.html -> cdu.html
    python generate_cdu.py -c my.toml -o out.html

TOML の読み込みには Python 3.11+ の tomllib (または tomli) が必要。
JSON 設定(.json)なら標準ライブラリだけで動く。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover
    try:
        import tomli as tomllib  # type: ignore
    except ModuleNotFoundError:
        tomllib = None  # type: ignore

HERE = Path(__file__).resolve().parent

COLORS = {"w", "g", "c", "m", "a", "r"}
ACTIONS = {"command", "page", "repeat", "exec", "prev", "next", "back", "field", "submit", "reset"}
SLOT_ONLY = {"field", "submit", "reset"}   # ファンクションキーでは使えない(ページ内のラインキー専用)
ARGS = {"none", "opt", "req"}
PAGE_TYPES = {"menu", "output"}
SLOT_RE = re.compile(r"^[LR][1-6]$")
NAME_RE = re.compile(r"^\w+$")
PLACEHOLDER_RE = re.compile(r"\{(\w+)\}")

MAX_LABEL = 12   # ラインキー1つに割り当てられる桁数 (24桁 / 2)
MAX_HINT = 17    # ヒント行(小フォント)に収まる文字数の目安


class ConfigError(Exception):
    pass


def load_config(path: Path) -> dict:
    if path.suffix.lower() == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    if tomllib is None:
        raise ConfigError("TOML の読み込みには Python 3.11+ か `pip install tomli` が必要です (JSON設定なら不要)")
    with path.open("rb") as f:
        return tomllib.load(f)


def norm_key(raw: dict, where: str, errs: list[str], warns: list[str], slot: str | None = None) -> dict | None:
    """キー定義1つを検証し、ブラウザ側が使う形に正規化する。"""
    action = raw.get("action")
    if action is None:
        action = "command" if "command" in raw else "page" if "page" in raw else None
    if action not in ACTIONS:
        errs.append(f"{where}: action が不明です ({action!r})。{sorted(ACTIONS)} のいずれか")
        return None

    if slot is None and action in SLOT_ONLY:
        errs.append(f"{where}: action={action} はページ内のラインキーでのみ使えます")
        return None

    key: dict = {"action": action}
    if action == "field":
        name = str(raw.get("name", ""))
        caption = str(raw.get("label", ""))
        if not NAME_RE.match(name):
            errs.append(f"{where}: field には英数字/_ の name が必要です ({name!r})")
            return None
        if not caption:
            errs.append(f"{where}: field には label (入力欄の見出し) が必要です")
            return None
        length = int(raw.get("len", 5))
        if not 1 <= length <= 11:
            errs.append(f"{where}: len は 1〜11 ({length})")
            return None
        if len(caption) > MAX_HINT:
            warns.append(f"{where}: label {caption!r} が長すぎます (目安 {MAX_HINT} 文字)")
        color = raw.get("color", "g")   # 入力済みの値の色
        if color not in COLORS:
            errs.append(f"{where}: color は {sorted(COLORS)} のいずれか ({color!r})")
            return None
        key.update(name=name, len=length, color=color, hint=caption, label=caption)
        return key
    if action == "submit":
        command = str(raw.get("command", "")).strip()
        if not command:
            errs.append(f"{where}: action=submit には command テンプレートが必要です (例: \"two a {{new}} {{p1}}\")")
            return None
        key.update(command=command, clear=bool(raw.get("clear", False)))
    if action == "command":
        command = str(raw.get("command", "")).strip()
        if not command:
            errs.append(f"{where}: action=command には command が必要です")
            return None
        args = raw.get("args", "none")
        if args not in ARGS:
            errs.append(f"{where}: args は {sorted(ARGS)} のいずれか ({args!r})")
            return None
        key.update(command=command, args=args)
    elif action == "page":
        page = raw.get("page")
        if not page:
            errs.append(f"{where}: action=page には page が必要です")
            return None
        key["page"] = str(page)

    default_label = {"command": key.get("command", "").upper(), "submit": "EXEC", "reset": "CLEAR", "back": "BACK"}.get(action, "")
    label = str(raw.get("label") or default_label)
    if not label:
        errs.append(f"{where}: label が必要です")
        return None

    color = raw.get("color", "w")
    if color not in COLORS:
        errs.append(f"{where}: color は {sorted(COLORS)} のいずれか ({color!r})")
        return None
    key["color"] = color

    if slot is not None:  # ラインキー
        if raw.get("arrow", True):
            label = "<" + label if slot[0] == "L" else label + ">"
        if len(label) > MAX_LABEL:
            warns.append(f"{where}: label {label!r} が {MAX_LABEL} 文字を超えています (表示が重なる可能性)")
        hint = str(raw.get("hint", ""))
        if len(hint) > MAX_HINT:
            warns.append(f"{where}: hint {hint!r} が長すぎます (目安 {MAX_HINT} 文字)")
        key["hint"] = hint
    key["label"] = label
    return key


def normalize(cfg: dict) -> tuple[dict, list[str]]:
    errs: list[str] = []
    warns: list[str] = []

    server = cfg.get("server", {})
    ui = cfg.get("ui", {})

    # --- ファンクションキー ---
    fnkeys = []
    for i, raw in enumerate(cfg.get("fnkeys", []), 1):
        k = norm_key(raw, f"fnkeys[{i}]", errs, warns)
        if k:
            fnkeys.append(k)

    # --- ページ ---
    pages: dict[str, dict] = {}
    groups: dict[str, list[str]] = {}
    for i, raw in enumerate(cfg.get("pages", []), 1):
        pid = raw.get("id")
        where = f"pages[{i}]({pid})"
        if not pid:
            errs.append(f"pages[{i}]: id が必要です")
            continue
        if pid in pages:
            errs.append(f"{where}: id が重複しています")
            continue
        ptype = raw.get("type", "menu")
        if ptype not in PAGE_TYPES:
            errs.append(f"{where}: type は {sorted(PAGE_TYPES)} のいずれか ({ptype!r})")
            continue
        keys: dict[str, dict] = {}
        for j, kr in enumerate(raw.get("keys", []), 1):
            slot = str(kr.get("slot", "")).upper()
            kw = f"{where}.keys[{j}]"
            if not SLOT_RE.match(slot):
                errs.append(f"{kw}: slot は L1〜L6 / R1〜R6 ({slot!r})")
                continue
            if slot in keys:
                errs.append(f"{kw}: slot {slot} が重複しています")
                continue
            k = norm_key(kr, kw, errs, warns, slot=slot)
            if k:
                keys[slot] = k
        group = str(raw.get("group", pid))
        pages[pid] = {"type": ptype, "title": str(raw.get("title", pid)), "group": group, "keys": keys}
        groups.setdefault(group, []).append(pid)

    # --- submit のプレースホルダ検証 ---
    for pid, p in pages.items():
        names = {k["name"] for k in p["keys"].values() if k["action"] == "field"}
        used: set[str] = set()
        for slot, k in p["keys"].items():
            if k["action"] == "submit":
                holders = set(PLACEHOLDER_RE.findall(k["command"]))
                used |= holders
                for h in sorted(holders - names):
                    errs.append(f"pages({pid}).{slot}: {{{h}}} に対応する field (name) がありません")
        for n in sorted(names - used) if used else []:
            warns.append(f"pages({pid}): field {n!r} はどの submit でも使われていません")

    # --- 参照チェック ---
    home = cfg.get("home") or next((p for p, v in pages.items() if v["type"] == "menu"), None)
    result_page = cfg.get("result_page", "output")
    if home not in pages:
        errs.append(f"home: ページ {home!r} が定義されていません")
    if result_page not in pages:
        errs.append(f"result_page: ページ {result_page!r} が定義されていません")
    elif pages[result_page]["type"] != "output":
        errs.append(f"result_page: {result_page!r} は type=\"output\" である必要があります")
    for pid, p in pages.items():
        for slot, k in p["keys"].items():
            if k["action"] == "page" and k["page"] not in pages:
                errs.append(f"pages({pid}).{slot}: 移動先ページ {k['page']!r} が存在しません")
    for n, k in enumerate(fnkeys, 1):
        if k["action"] == "page" and k["page"] not in pages:
            errs.append(f"fnkeys[{n}]: 移動先ページ {k['page']!r} が存在しません")

    if errs:
        raise ConfigError("\n".join("  - " + e for e in errs))

    out = {
        "home": home,
        "result_page": result_page,
        "server": {
            "endpoint": server.get("endpoint", "/api/command"),
            "timeout_ms": int(server.get("timeout_ms", 15000)),
        },
        "ui": {
            "title": ui.get("title", "CDU"),
            "fn_columns": int(ui.get("fn_columns", 5)),
        },
        "fnkeys": fnkeys,
        "pages": pages,
        "groups": groups,
    }
    return out, warns


def render_html(template: str, cfg: dict) -> str:
    # </script> などでスクリプトが途切れないよう "</" をエスケープ
    payload = json.dumps(cfg, ensure_ascii=False, indent=1).replace("</", "<\\/")
    title = cfg["ui"]["title"].replace("&", "&amp;").replace("<", "&lt;")
    if "__CONFIG_JSON__" not in template:
        raise ConfigError("テンプレートに __CONFIG_JSON__ がありません")
    return template.replace("__CONFIG_JSON__", payload).replace("__TITLE__", title)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="CDU の静的HTMLを生成する")
    ap.add_argument("-c", "--config", type=Path, default=HERE / "cdu_config.toml")
    ap.add_argument("-t", "--template", type=Path, default=HERE / "cdu_template.html")
    ap.add_argument("-o", "--output", type=Path, default=HERE / "cdu.html")
    args = ap.parse_args(argv)

    try:
        raw = load_config(args.config)
        cfg, warns = normalize(raw)
        html = render_html(args.template.read_text(encoding="utf-8"), cfg)
    except (ConfigError, OSError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    for w in warns:
        print(f"warning: {w}", file=sys.stderr)
    args.output.write_text(html, encoding="utf-8")
    print(f"generated {args.output}  (pages: {len(cfg['pages'])}, fnkeys: {len(cfg['fnkeys'])})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
