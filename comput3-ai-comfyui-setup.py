#!/usr/bin/env python3
# comput3_custom_comfyui_setup.py
#
# Comput3 AI ComfyUI Setup Python Script
#
# Copyright © 2025 Daïm Al-Yad (@daimalyad)
# Licensed under the MIT License
#
# USAGE INSTRUCTIONS:
#
# 1. **Get Your API Key**
#    - Log in to your Comput3 dashboard.
#    - Copy your Comput3 API key (it usually begins with `c3_api_...`).
#    - Paste it into the `COMPUT3_API_KEY` variable below.
#
# 2. **Choose Workload Type and Duration**
#    - By default, `WORKLOAD_TYPE` is set to `"media:fast"`, the only type as of August of 2025.
#    - `WORKLOAD_HOURS` controls how many hours your Comput3 ComfyUI node will run.
#
# 3. **Add Whitelisted Nodes**
#    - In `NODE_QUERIES`, list any nodes that are available in Comput3's **whitelisted** catalog.
#    - Use full names copied from the whitelist, or partial names / repo titles — the script will try to figure it out.
#
# 4. **Add Whitelisted Models**
#    - In `WHITELISTED_MODEL_QUERIES`, list models from the Comput3 **whitelisted** catalog.
#    - You can use the display name from the whitelist, the filename, or part of either.
#
# 5. **Add Custom GitHub Nodes (Optional)**
#    - In `GITHUB_NODE_URLS`, list full GitHub repository URLs for custom nodes you want installed.
#    - The script *always* installs `apeirography/daimalyadnodes` automatically, to allow non-whitelisted model installations.
#
# 6. **Add Non-Whitelisted Models (Optional)**
#    - In `NON_WHITELISTED_MODELS`, provide a list of dictionaries with:
#        - `"url"`: direct download link to the model file.
#        - `"filename"`: desired filename (must match exactly what the server saves).
#        - `"subfolder"`: target subfolder in `/models/` (e.g., `"diffusion_models"`, `"loras"`).
#        - `"sha256"`: optional checksum for integrity verification.
#
# 7. **Run the Script**
#    - Save your changes.
#    - Run from terminal: `python comput3_custom_comfyui_setup.py`
#    - The script will launch your Comput3 ComfyUI workload and setup everything you specified in a few minutes.
#
# 8. Start using ComfyUI
# 
#    - Return to your Comput3 AI Dashboard dashboard and go into ComfyUI to use your fully setup instance.
#
# Cheers!

import json, time, sys, re
import requests
from datetime import datetime

# =========================
# USER CONFIG (edit these!)
# =========================
COMPUT3_API_KEY   = "c3_api_************************" # replace with Comput3 AI API key from post-login dashboard page
COMFY_USER_KEY    = COMPUT3_API_KEY

WORKLOAD_TYPE     = "media:fast"  # leave as "media:fast" until Comput3 AI offers more ComfyUI workload types
WORKLOAD_HOURS    = 1.0   # how long should the workload be reserved for

# Step 2: whitelisted node searches (lenient / partial / repo-or-title)
NODE_QUERIES = [
    # "ComfyUI_UltimateSDUpscale",
    # "JPS Custom Nodes for ComfyUI",
    # "Various ComfyUI Nodes by Type",
    # "ComfyUI Impact Pack",
    # "ComfyUI ArtVenture",
    # "mikey_nodes",
]

# Step 3: whitelisted model searches (lenient / partial / filename-or-name)
WHITELISTED_MODEL_QUERIES = [
    # "Comfy Org/FLUX.1 [dev] Checkpoint model (fp8)",
    # "4x-UltraSharp",
    # "sd_xl_base_1.0.safetensors",
    # "stable-diffusion-xl-refiner-1.0",
]

# Step 4: additional custom nodes to install from GitHub URL (supports multiple)
# NOTE: apeirography/daimalyadnodes is always installed silently even if not listed here.
GITHUB_NODE_URLS = [
    # "https://github.com/username/reponame",
]

# Step 6: non-whitelisted models by URL
# Each item: {"url": "...", "filename": "...", "subfolder": "diffusion_models" (or other), "sha256": "" (optional)}
NON_WHITELISTED_MODELS = [
    # {
    #   "url": "https://huggingface.co/lodestones/Chroma1-HD/resolve/main/Chroma-HD.safetensors",
    #   "filename": "Chroma-HD.safetensors",
    #   "subfolder": "diffusion_models",
    #   "sha256": ""
    # },
    # {
    #   "url": "https://huggingface.co/silveroxides/Chroma-LoRA-Experiments/resolve/main/Hyper-Chroma-low-step-LoRA.safetensors",
    #   "filename": "Hyper-Chroma-low-step-LoRA.safetensors",
    #   "subfolder": "loras",
    #   "sha256": ""
    # },
]

# DaimalyadModelDownloader defaults (only used by fallback workflow)
DOWNLOADER_DEFAULTS = {
    "overwrite": True,
    "timeout_s": 120,
    "retries": 3,
    "user_agent": "ComfyUI-DaimalyadModelDownloader/1.0",
}

# =========================
# HTTP helpers (session + auth)
# =========================
S = requests.Session()

def log(msg, *, level="info"):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {level.upper():7s} {msg}")

def ensure(cond, err):
    if not cond:
        raise RuntimeError(err)

def normalize(x: str) -> str:
    if x is None:
        return ""
    return re.sub(r"\s+", " ", str(x).strip().lower())

def truthy(x) -> bool:
    if isinstance(x, bool): return x
    if isinstance(x, (int, float)): return x != 0
    if isinstance(x, str):
        return normalize(x) in {"true","1","yes","installed","ok","enabled","active","success","completed","done"}
    return False

def _apply_auth(is_comput3=True):
    S.headers.update({
        "Accept": "*/*",
        "User-Agent": "daim-init/1.1",
    })
    if COMFY_USER_KEY:
        S.headers["Authorization"] = "Bearer " + COMFY_USER_KEY
        S.headers["comfy-user"]    = COMFY_USER_KEY
    if is_comput3 and COMPUT3_API_KEY:
        S.headers["X-C3-API-KEY"] = COMPUT3_API_KEY
        # Some proxies like cookie form:
        try:
            S.cookies.set("c3_api_key", COMPUT3_API_KEY)
        except Exception:
            pass

def get(url, *, is_comput3=True, timeout=30):
    _apply_auth(is_comput3)
    r = S.get(url, timeout=timeout)
    return r.status_code, r.text

def post(url, payload_bytes, *, content_type="application/json", is_comput3=True, timeout=120):
    _apply_auth(is_comput3)
    h = {"Content-Type": content_type or "application/json"}
    r = S.post(url, data=payload_bytes, headers=h, timeout=timeout)
    return r.status_code, r.text

def jpost(url, obj, **kw):
    return post(url, json.dumps(obj).encode("utf-8"), content_type="application/json", **kw)

# =========================
# 1) Launch Comput3 workload
# =========================
def launch_comput3_media(workload_type: str, hours: float):
    ensure(COMPUT3_API_KEY, "COMPUT3_API_KEY is required.")
    url = "https://api.comput3.ai/api/v0/launch"
    expires = int(time.time() + hours * 3600)
    body = {"type": workload_type, "expires": expires}
    log(f"Launching Comput3 workload {workload_type} for {hours:.1f}h ...")
    r = S.post(url, headers={"X-C3-API-KEY": COMPUT3_API_KEY, "Content-Type": "application/json"},
               data=json.dumps(body), timeout=30)
    ensure(r.status_code == 200, f"Launch failed ({r.status_code}): {r.text}")
    wl = r.json()
    node = wl.get("node", "")
    ensure(node, f"Launch succeeded but no node in response: {r.text}")
    host = node if node.startswith("ui-") else f"ui-{node}"
    api_base  = f"https://{host}/api"
    root_base = f"https://{host}"
    log(f"Launch OK. Node={node}  API={api_base}")
    return {"api_base": api_base, "root_base": root_base, "workload": wl.get("workload","")}

# =========================
# Readiness/warmup
# =========================
def wait_for_comfy_ready(api_base, initial_sleep=30, timeout_s=420):
    """
    Wait for /queue and at least one of catalogs to be 200.
    Tolerate 404/502 during warm-up. Exponential backoff.
    """
    if initial_sleep > 0:
        log(f"[ready] Initial sleep {initial_sleep}s to let the node boot ...")
        time.sleep(initial_sleep)

    start = time.time()
    backoff = 1.5
    attempt = 0

    def ok(c): return c == 200

    while time.time() - start < timeout_s:
        attempt += 1
        code_q, _  = get(f"{api_base}/queue")
        # try both shapes for nodes/models (some builds prefer /model/getlist)
        code_cn, _ = get(f"{api_base}/customnode/getlist?mode=cache&skip_update=true")
        code_em, _ = get(f"{api_base}/externalmodel/getlist?mode=cache&skip_update=true")
        code_m , _ = get(f"{api_base}/model/getlist?mode=cache&skip_update=true")
        if ok(code_q) and (ok(code_cn) or ok(code_em) or ok(code_m)):
            log(f"[ready] API is up (queue={code_q}, customnode={code_cn}, externalmodel={code_em}, model={code_m})")
            return True
        log(f"[ready] warming (attempt {attempt}): queue={code_q}, customnode={code_cn}, externalmodel={code_em}, model={code_m}")
        time.sleep(backoff)
        backoff = min(backoff * 1.7, 10.0)

    log(f"[ready] Timed out after {timeout_s}s waiting for ComfyUI Manager.", level="error")
    return False

# =========================
# Catalog fetchers
# =========================
def get_nodes_catalog(api_base):
    u = f"{api_base}/customnode/getlist?mode=cache&skip_update=true"
    code, body = get(u)
    ensure(code == 200, f"customnode getlist failed: {code} {body}")
    data = json.loads(body)
    if isinstance(data, dict) and "custom_nodes" in data:
        arr = data["custom_nodes"]
    elif isinstance(data, dict) and "node_packs" in data:
        arr = []
        for k, v in (data["node_packs"] or {}).items():
            if isinstance(v, dict):
                v = dict(v)
                v["id"] = k
                arr.append(v)
    elif isinstance(data, list):
        arr = data
    else:
        raise RuntimeError("unexpected customnode getlist shape")
    return arr

def get_models_catalog(api_base):
    for path in ("/externalmodel/getlist?mode=cache&skip_update=true",
                 "/model/getlist?mode=cache&skip_update=true"):
        code, body = get(f"{api_base}{path}")
        if code != 200:
            continue
        data = json.loads(body)
        if isinstance(data, dict) and "models" in data:
            return data["models"]
        if isinstance(data, list):
            return data
    raise RuntimeError("models getlist returned no usable result")

# =========================
# Lenient pickers
# =========================
def pick_node(catalog, query):
    q = normalize(query)
    best, best_score = None, -1
    for m in catalog:
        mid   = normalize(m.get("id"))
        title = normalize(m.get("title"))
        repo  = normalize(m.get("repository") or m.get("repo") or m.get("pkg_name"))
        state = normalize(m.get("state"))
        score = 0
        if mid == q or title == q: score = 10_000
        else:
            if q and mid.find(q)   >= 0: score += 400
            if q and title.find(q) >= 0: score += 350
            if q and repo.find(q)  >= 0: score += 250
        if state == "not-installed" or (state == "" and not (truthy(m.get("installed")) or truthy(m.get("is_installed")))):
            score += 50
        if score > best_score:
            best, best_score = m, score
    return best, best_score

def pick_model(catalog, query):
    q = normalize(query)
    best, best_score = None, -1
    for m in catalog:
        fn = normalize(m.get("filename"))
        nm = normalize(m.get("name"))
        installed = truthy(m.get("installed"))
        score = 0
        if fn == q or nm == q: score = 1000
        else:
            if q and fn.find(q) >= 0: score += 400
            if q and nm.find(q) >= 0: score += 300
            if not installed:         score += 50
            looks_file = "." in q
            if looks_file and not (fn == q or fn.find(q) >= 0):
                score = -1
        if score > best_score:
            best, best_score = m, score
    return (best if best_score >= 250 else None), best_score

# =========================
# Queue helpers
# =========================
def queue_reset(api_base):
    get(f"{api_base}/manager/queue/reset")

def queue_start(api_base):
    get(f"{api_base}/manager/queue/start")

def wait_queue_idle(api_base, timeout_s=180, poll_s=1.5):
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        code, body = get(f"{api_base}/manager/queue/status")
        if code == 200:
            try:
                s = json.loads(body)
                if not s.get("is_processing") and int(s.get("in_progress_count", 0)) == 0:
                    return True
            except Exception:
                pass
        time.sleep(poll_s)
    return False

# =========================
# 2) Install whitelisted nodes by query (Go parity)
# =========================
def node_versions(api_base, slug_id):
    code, body = get(f"{api_base}/customnode/versions/{slug_id}")
    if code != 200: return []
    try:
        return json.loads(body)
    except Exception:
        return []

def _catalog_entry_for_install(picked, slug, latest_tag):
    # mirror ensureCatalogInstallShape + keep useful fields from GUI list
    entry = {
        "author":            picked.get("author",""),
        "title":             picked.get("title",""),
        "id":                slug,
        "install_type":      picked.get("install_type") or ("git-clone" if "github.com" in str(picked.get("repository","")).lower() else "git-clone"),
        "repository":        picked.get("repository") or picked.get("repo") or "",
        "reference":         picked.get("reference") or picked.get("repository") or picked.get("repo") or "",
        "files":             [picked.get("repository") or picked.get("repo")] if (picked.get("repository") or picked.get("repo")) else [],
        "channel":           "default",
        "mode":              "cache",
        "selected_version":  "latest",  # exact GUI behavior
        "skip_post_install": False,
        "state":             "not-installed",
        "trust":             True,
        "ui_id":             picked.get("ui_id",""),
        # bonus metadata (harmless if present)
        "version":           picked.get("version") or latest_tag or "",
        "cnr_latest":        picked.get("cnr_latest") or latest_tag or "",
        "last_update":       picked.get("last_update",""),
        "stars":             picked.get("stars", 0),
        "health":            picked.get("health","-"),
        "description":       picked.get("description",""),
        "is_favorite":       bool(picked.get("is_favorite", False)),
        "preemptions":       picked.get("preemptions", []),
        "update-state":      picked.get("update-state","false"),
    }
    # prune empties that could upset strict servers
    for k in list(entry.keys()):
        v = entry[k]
        if v in ("", None, [], {}):
            del entry[k]
    return entry

def install_node_by_query(api_base, query):
    catalog = get_nodes_catalog(api_base)
    picked, score = pick_node(catalog, query)
    if not picked:
        log(f"[nodes] No match for {query!r}", level="warn")
        return False

    slug = (picked.get("id") or picked.get("title") or "").strip().lower().replace(" ", "-")
    title = picked.get("title", "")
    repo = picked.get("repository") or picked.get("repo") or ""
    install_type = picked.get("install_type") or ("git-clone" if "github.com" in str(repo).lower() else "git-clone")

    log(f"[nodes] '{query}' → id={slug!r} title={title!r} type={install_type} repo={repo!r}")

    # 2) versions (best-effort)
    vers = node_versions(api_base, slug)
    latest_tag = ""
    if isinstance(vers, list) and vers:
        # pick newest by createdAt if present
        def _ts(v): return v.get("createdAt") or ""
        vers_sorted = sorted(vers, key=_ts, reverse=True)
        latest_tag = str(vers_sorted[0].get("version","")).strip() or ""

    # 3) build single-object payload, GUI-parity
    entry = _catalog_entry_for_install(picked, slug, latest_tag)
    payload = json.dumps(entry).encode("utf-8")

    # 4) reset queue, enqueue, start, wait (w/ transient retry)
    queue_reset(api_base)
    attempts, backoff = 0, 1.5
    while attempts < 6:
        attempts += 1
        code, body = post(f"{api_base}/manager/queue/install", payload,
                          content_type="text/plain;charset=UTF-8")
        if code == 200:
            queue_start(api_base)
            ok = wait_queue_idle(api_base)
            log(f"[nodes] install {'OK' if ok else 'timeout'} for {title!r}")
            return ok
        if code in (404, 409, 429, 500, 502, 503, 504):
            log(f"[nodes] enqueue transient {code} (attempt {attempts}) — backing off {backoff:.1f}s")
            time.sleep(backoff); backoff = min(backoff * 1.7, 10.0)
            continue
        raise RuntimeError(f"[nodes] enqueue failed {code}: {body}")

    log(f"[nodes] enqueue failed after retries for {title!r}", level="warn")
    return False

# =========================
# 3) Install whitelisted models by query
# =========================
def wait_model_installed(api_base, filename, timeout_s=180, poll_s=1.5):
    deadline = time.time() + timeout_s
    last_note = 0
    while time.time() < deadline:
        try:
            all_models = get_models_catalog(api_base)
            for m in all_models:
                if str(m.get("filename","")).lower() == filename.lower() and truthy(m.get("installed")):
                    return True
        except Exception:
            pass
        now = time.time()
        if now - last_note > 10:
            log(f"[models] waiting for {filename} ...")
            last_note = now
        time.sleep(poll_s)
    return False

def install_model_by_query(api_base, query):
    models = get_models_catalog(api_base)
    picked, score = pick_model(models, query)
    if not picked:
        log(f"[models] No match for {query!r}", level="warn")
        return False

    base = (picked.get("base") or "").strip()
    save_path = (picked.get("save_path") or "").strip()
    filename = (picked.get("filename") or "").strip()
    ensure(base and save_path and filename, f"[models] matched entry missing base/save_path/filename: {picked}")

    log(f"[models] '{query}' → name={picked.get('name')!r} filename={filename!r} base={base!r} save_path={save_path!r}")

    queue_reset(api_base)
    payload = json.dumps(picked).encode("utf-8")
    attempts, backoff = 0, 1.5
    while attempts < 6:
        attempts += 1
        code, body = post(f"{api_base}/manager/queue/install_model", payload,
                          content_type="text/plain;charset=UTF-8")
        if code == 200:
            queue_start(api_base)
            ok = wait_model_installed(api_base, filename, timeout_s=600)
            log(f"[models] install {'OK' if ok else 'timeout'} for {filename!r}")
            return ok
        if code in (404, 409, 429, 500, 502, 503, 504):
            log(f"[models] enqueue transient {code} (attempt {attempts}) — backing off {backoff:.1f}s")
            time.sleep(backoff); backoff = min(backoff * 1.7, 10.0)
            continue
        raise RuntimeError(f"[models] enqueue failed {code}: {body}")

    log(f"[models] enqueue failed after retries for {filename!r}", level="warn")
    return False

# =========================
# 4) Install custom nodes from GitHub
# =========================
def install_node_from_github(api_base, git_url):
    log(f"[github-node] Installing {git_url} ...")
    attempts, backoff = 0, 1.5
    while attempts < 8:
        attempts += 1
        code, body = post(f"{api_base}/customnode/install/git_url",
                          git_url.encode("utf-8"),
                          content_type="text/plain;charset=UTF-8")
        if code == 200:
            queue_start(api_base)
            ok = wait_queue_idle(api_base)
            log(f"[github-node] install {'OK' if ok else 'timeout'}")
            return ok

        code2, body2 = jpost(f"{api_base}/customnode/install/git_url", {"url": git_url})
        if code2 == 200:
            queue_start(api_base)
            ok = wait_queue_idle(api_base)
            log(f"[github-node] install {'OK' if ok else 'timeout'}")
            return ok

        # Retry on warmup/proxy errors
        if code in (404, 409, 429, 500, 502, 503, 504) or code2 in (404, 409, 429, 500, 502, 503, 504):
            log(f"[github-node] transient ({code}/{code2}) attempt {attempts}; sleeping {backoff:.1f}s")
            time.sleep(backoff); backoff = min(backoff * 1.7, 10.0)
            continue

        # Hard failure
        raise RuntimeError(f"[github-node] install failed ({code}/{code2}): {(body or body2)[:400]}")

    log("[github-node] giving up after retries", level="warn")
    return False

# =========================
# 5) Reboot ComfyUI — detect full cycle, then wait 30s
# =========================
def reboot_comfy_cycle(api_base, extra_wait_after_up_s=30, total_timeout_s=900):
    """
    Mirrors robust behavior:
      - request reboot (retry/backoff; 5xx accepted as "initiated")
      - Phase A: wait until /queue returns a non-200 at least once (downtime seen)
      - Phase B: wait until readiness probe is healthy again
      - Sleep extra 30s after UP before returning
    """
    log("[reboot] Requesting ComfyUI reboot ...")
    # Issue reboot (retry & tolerate proxy 5xx as accepted)
    attempts, backoff = 0, 1.5
    reboot_accepted = False
    last_err = None
    while attempts < 8 and not reboot_accepted:
        attempts += 1
        code, body = get(f"{api_base}/manager/reboot")
        if code == 200:
            reboot_accepted = True
            break
        if code in (502, 503, 504):
            # treat as accepted; Cloudflare may proxy-error immediately
            last_err = f"{code}: {body[:160]}"
            log(f"[reboot] proxy {code} — assuming reboot initiated (attempt {attempts})")
            reboot_accepted = True
            break
        last_err = f"{code}: {body[:160]}"
        log(f"[reboot] unexpected {code} (attempt {attempts}) — backoff {backoff:.1f}s")
        time.sleep(backoff); backoff = min(backoff * 1.7, 10.0)

    ensure(reboot_accepted, f"[reboot] could not initiate reboot: {last_err}")

    # PHASE A: observe at least one non-200 on /queue (downtime)
    log("[reboot] Waiting to observe API downtime ...")
    saw_down = False
    phaseA_deadline = time.time() + min(120, total_timeout_s // 3)
    backoff = 1.2
    while time.time() < phaseA_deadline:
        code, _ = get(f"{api_base}/queue")
        if code != 200:
            saw_down = True
            log(f"[reboot] downtime observed: /queue → {code}")
            break
        time.sleep(backoff)
        backoff = min(backoff * 1.4, 4.0)

    if not saw_down:
        log("[reboot] Did not observe explicit downtime; continuing to Phase B anyway", level="warn")

    # PHASE B: wait for ready again
    log("[reboot] Waiting for API to come back healthy ...")
    came_back = wait_for_comfy_ready(api_base, initial_sleep=0, timeout_s=max(180, total_timeout_s - 60))
    ensure(came_back, "[reboot] API did not become healthy again within timeout")

    # POST-DETECT WAIT
    log(f"[reboot] API healthy — extra wait {extra_wait_after_up_s}s before continuing ...")
    time.sleep(extra_wait_after_up_s)
    log("[reboot] Reboot cycle complete")

# =========================
# 6) Non-whitelisted model installs
#   A) try Manager URL endpoints
#   B) fallback to downloader workflow (DaimalyadModelDownloader)
# =========================
_INSTALL_URL_PATHS = [
    "/externalmodel/install_url",
    "/model/install_url",
    "/externalmodel/add_by_url",
    "/model/add_by_url",
]

def install_nonwhitelisted_model_via_manager(api_base, spec):
    url      = spec.get("url","").strip()
    filename = spec.get("filename","").strip()
    subfolder= spec.get("subfolder","").strip()
    sha256   = spec.get("sha256","").strip()

    ensure(url and filename and subfolder, f"[nonwhite] url/filename/subfolder required: {spec}")
    log(f"[nonwhite] Manager-URL install → {filename}  into /models/{subfolder}")

    queue_reset(api_base)
    last_err = None

    candidates = [
        {"url": url, "filename": filename, "subfolder": subfolder, "sha256": sha256 or ""},
        {"url": url, "filename": filename, "save_path": f"/app/ComfyUI/models/{subfolder}", "sha256": sha256 or ""},
    ]
    for path in _INSTALL_URL_PATHS:
        endpoint = f"{api_base}{path}"
        for payload in candidates:
            code, body = jpost(endpoint, payload)
            if code == 200:
                queue_start(api_base)
                ok = wait_queue_idle(api_base, timeout_s=900)
                log(f"[nonwhite] {filename}: {'OK' if ok else 'timeout'} via {path}")
                return ok
            else:
                last_err = f"{path} → {code} {(body or '')[:260]}"

    log(f"[nonwhite] Manager-URL methods failed for {filename}. Last err: {last_err}", level="warn")
    return False

# ----- Workflow helpers (prompt submission & completion wait) -----
def _prompt_post_try(api_base, root_base, body_bytes, content_type):
    # Try /api/prompt then /prompt (both seen in the wild)
    for base in (api_base, root_base):
        endpoint = f"{base}/prompt"
        code, text = post(endpoint, body_bytes, content_type=content_type)
        if code == 200:
            try:
                return True, json.loads(text)
            except Exception:
                return True, {"raw": text}
    return False, text

def extract_prompt_id(resp_json):
    """
    Handle common shapes:
      - {"prompt_id":"..."} (typical)
      - {"node_errors":...,"prompt_id":"..."} (errors present)
      - {"id":"..."} (alt)
      - {"data":{"id":"..."}} (alt)
      - {"raw": "..."} (unparseable; none)
    """
    if not isinstance(resp_json, dict):
        return None
    for k in ("prompt_id", "promptId", "id"):
        v = resp_json.get(k)
        if isinstance(v, str) and v:
            return v
    data = resp_json.get("data")
    if isinstance(data, dict):
        for k in ("prompt_id", "promptId", "id"):
            v = data.get(k)
            if isinstance(v, str) and v:
                return v
    return None

def _history_fetch(api_base, prompt_id):
    # ComfyUI typically returns {"<prompt_id>": {...}} for /history/{id}
    code, body = get(f"{api_base}/history/{prompt_id}")
    if code != 200:
        return code, None
    try:
        obj = json.loads(body)
    except Exception:
        return 200, None

    if isinstance(obj, dict):
        if prompt_id in obj and isinstance(obj[prompt_id], dict):
            return 200, obj[prompt_id]
        # Some builds return {"status":{...}, "outputs":{...}}
        if "status" in obj or "outputs" in obj:
            return 200, obj
    return 200, None

def _is_workflow_done(hist_obj):
    if not isinstance(hist_obj, dict):
        return False, None
    st = hist_obj.get("status") or {}
    # status might be nested or strings; be lenient
    if isinstance(st, dict):
        if truthy(st.get("completed")):
            return True, "success"
        sstr = normalize(st.get("status") or st.get("status_str") or st.get("state") or "")
        if sstr in {"success","complete","completed","done"}:
            return True, "success"
        if sstr in {"error","failed","fail","exception"} or truthy(st.get("error")):
            return True, "error"
    # Heuristic: presence of outputs may indicate completion
    if hist_obj.get("outputs"):
        return True, "success"
    return False, None

def wait_workflow_complete(api_base, prompt_id, timeout_s=1800, poll_s=1.5):
    """
    Poll /history/{prompt_id} until status is completed (success or error).
    Tolerates initial 404 while the record is being created.
    """
    log(f"[workflow] waiting for prompt {prompt_id} to complete ...")
    deadline = time.time() + timeout_s
    last_note = 0.0
    while time.time() < deadline:
        code, hist = _history_fetch(api_base, prompt_id)
        if code == 200 and hist is not None:
            done, result = _is_workflow_done(hist)
            if done:
                log(f"[workflow] {prompt_id} → {result or 'done'}")
                return result != "error"
        # periodic heartbeat
        now = time.time()
        if now - last_note > 10:
            if code == 200:
                log(f"[workflow] still pending")
            else:
                log(f"[workflow] polling history ... (code={code})")
            last_note = now
        time.sleep(poll_s)
    log(f"[workflow] timeout waiting for {prompt_id}", level="warn")
    return False

# ----- Downloader workflow fallback -----
def run_downloader_workflow(api_base, root_base, spec):
    """
    Submit a tiny graph with a single DaimalyadModelDownloader node,
    then block until that specific workflow run is finished (Go parity).
    """
    url      = spec.get("url","").strip()
    filename = spec.get("filename","").strip()
    subfolder= spec.get("subfolder","").strip()
    sha256   = (spec.get("sha256","") or "").strip()

    ensure(url and filename and subfolder, f"[downloader] url/filename/subfolder required")

    node_id = "20"  # arbitrary key, matches example
    inputs = {
        "url": url,
        "subfolder": subfolder,
        "filename": filename,
        "overwrite": DOWNLOADER_DEFAULTS["overwrite"],
        "sha256": sha256,
        "timeout_s": DOWNLOADER_DEFAULTS["timeout_s"],
        "retries": DOWNLOADER_DEFAULTS["retries"],
        "user_agent": DOWNLOADER_DEFAULTS["user_agent"],
    }
    graph = {
        node_id: {
            "inputs": inputs,
            "class_type": "DaimalyadModelDownloader",
            "_meta": {"title": "Model Downloader by DaimAlYad"}
        }
    }

    payload = {
        "prompt": graph,
        "client_id": "bootstrap-nonwhite-installer",
    }

    ok, resp = _prompt_post_try(api_base, root_base, json.dumps(payload).encode("utf-8"), "application/json")
    ensure(ok, f"[downloader] /prompt POST failed: {resp}")

    prompt_id = extract_prompt_id(resp)
    if not prompt_id:
        log("[workflow] no prompt_id returned; falling back to queue idle only", level="warn")
        queue_start(api_base)  # best-effort
        done = wait_queue_idle(api_base, timeout_s=900)
        log(f"[downloader] {'OK' if done else 'timeout'} for {filename} (no prompt_id)")
        return done

    # Start queue then wait SPECIFIC workflow to finish
    queue_start(api_base)  # harmless if already running
    ok = wait_workflow_complete(api_base, prompt_id, timeout_s=1800, poll_s=1.5)

    # As an extra safety (mirrors Go “drain” semantics), also ensure queue idle
    drained = wait_queue_idle(api_base, timeout_s=300)
    log(f"[downloader] {'OK' if (ok and drained) else 'timeout'} for {filename}")
    return ok and drained

def install_nonwhitelisted_model(api_base, root_base, spec):
    # First try Manager URL methods
    if install_nonwhitelisted_model_via_manager(api_base, spec):
        return True
    # Fallback to downloader workflow
    log("[nonwhite] Falling back to DaimalyadModelDownloader workflow ...")
    return run_downloader_workflow(api_base, root_base, spec)

# =========================
# MAIN
# =========================
def main():
    try:
        # 1) Launch
        wl = launch_comput3_media(WORKLOAD_TYPE, WORKLOAD_HOURS)
        api_base  = wl["api_base"]
        root_base = wl["root_base"]

        # Readiness after launch
        wait_for_comfy_ready(api_base, initial_sleep=30, timeout_s=420)

        # 2) Whitelisted nodes
        if NODE_QUERIES:
            log(f"Installing {len(NODE_QUERIES)} whitelisted node(s) ...")
        for q in NODE_QUERIES:
            try:
                install_node_by_query(api_base, q)
            except Exception as e:
                log(f"[nodes] {q!r}: {e}", level="warn")

        # 3) Whitelisted models
        if WHITELISTED_MODEL_QUERIES:
            log(f"Installing {len(WHITELISTED_MODEL_QUERIES)} whitelisted model(s) ...")
        for q in WHITELISTED_MODEL_QUERIES:
            try:
                install_model_by_query(api_base, q)
            except Exception as e:
                log(f"[models] {q!r}: {e}", level="warn")

        # 4) Custom nodes from GitHub
        # 4a) Always install DaimalyadNodes silently (required for downloader fallback)
        try:
            install_node_from_github(api_base, "https://github.com/apeirography/daimalyadnodes")
        except Exception as e:
            log(f"[github-node] daimalyadnodes: {e}", level="warn")

        # 4b) User-provided list
        if GITHUB_NODE_URLS:
            log(f"Installing {len(GITHUB_NODE_URLS)} GitHub custom node(s) ...")
        for git_url in GITHUB_NODE_URLS:
            try:
                install_node_from_github(api_base, git_url)
            except Exception as e:
                log(f"[github-node] {git_url}: {e}", level="warn")

        # 5) Reboot cycle detection (DOWN → UP → extra 30s)
        reboot_comfy_cycle(api_base, extra_wait_after_up_s=30, total_timeout_s=900)

        # 6) Non-whitelisted models by URL (Manager endpoints → downloader fallback)
        if NON_WHITELISTED_MODELS:
            log(f"Installing {len(NON_WHITELISTED_MODELS)} non-whitelisted model(s) by URL ...")
        for spec in NON_WHITELISTED_MODELS:
            try:
                install_nonwhitelisted_model(api_base, root_base, spec)
            except Exception as e:
                log(f"[nonwhite] {spec.get('filename','(unknown)')}: {e}", level="warn")

        log("All done.")
    except Exception as e:
        log(f"FATAL: {e}", level="error")
        sys.exit(1)

if __name__ == "__main__":
    main()
