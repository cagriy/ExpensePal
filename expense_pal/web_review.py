import html
import json
import mimetypes
import socket
import threading
import webbrowser
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, request, send_file

from expense_pal.config import load_descriptions, save_description


_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Review Receipt</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    background: #f0f2f5;
    height: 100vh;
    display: flex;
    flex-direction: column;
  }}
  h1 {{
    font-size: 1.1rem;
    padding: 12px 20px;
    background: #1a1a2e;
    color: #fff;
  }}
  .layout {{
    display: flex;
    flex: 1;
    overflow: hidden;
    gap: 0;
  }}
  .preview {{
    flex: 1;
    background: #222;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: auto;
    padding: 16px;
  }}
  .preview img {{
    max-width: 100%;
    max-height: 100%;
    object-fit: contain;
    border-radius: 4px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.5);
  }}
  .preview iframe {{
    width: 100%;
    height: 100%;
    border: none;
    background: #fff;
  }}
  .panel {{
    width: 380px;
    min-width: 320px;
    background: #fff;
    padding: 24px 20px;
    overflow-y: auto;
    border-left: 1px solid #ddd;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }}
  .panel h2 {{
    font-size: 1rem;
    color: #333;
    margin-bottom: 4px;
  }}
  label {{
    display: block;
    font-size: 0.78rem;
    font-weight: 600;
    color: #555;
    margin-bottom: 4px;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }}
  input, select {{
    width: 100%;
    padding: 8px 10px;
    border: 1px solid #ccc;
    border-radius: 6px;
    font-size: 0.95rem;
    color: #222;
    background: #fafafa;
  }}
  input:focus, select:focus {{
    outline: none;
    border-color: #4f7cf8;
    background: #fff;
  }}
  .buttons {{
    display: flex;
    gap: 10px;
    margin-top: 8px;
  }}
  button {{
    flex: 1;
    padding: 10px;
    border: none;
    border-radius: 6px;
    font-size: 0.95rem;
    font-weight: 600;
    cursor: pointer;
  }}
  .btn-confirm {{
    background: #4f7cf8;
    color: #fff;
  }}
  .btn-confirm:hover {{ background: #3a6ae0; }}
  .btn-cancel {{
    background: #eee;
    color: #555;
  }}
  .btn-cancel:hover {{ background: #ddd; }}
  #done-msg {{
    display: none;
    text-align: center;
    padding: 20px;
    color: #4f7cf8;
    font-weight: 600;
  }}
  .ac-wrapper {{ position: relative; }}
  .ac-dropdown {{
    display: none;
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background: #fff;
    border: 1px solid #ccc;
    border-top: none;
    border-radius: 0 0 6px 6px;
    max-height: 180px;
    overflow-y: auto;
    z-index: 100;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  }}
  .ac-item {{
    padding: 8px 10px;
    font-size: 0.92rem;
    color: #222;
    cursor: pointer;
  }}
  .ac-item:hover {{ background: #e8eeff; color: #3a6ae0; }}
</style>
</head>
<body>
<h1>Review Receipt &mdash; {filename}</h1>
<div class="layout">
  <div class="preview">
    {media_tag}
  </div>
  <div class="panel">
    <h2>Extracted Data</h2>
    <div>
      <label for="date">Date</label>
      <input type="text" id="date" name="date" value="{date}" placeholder="YYYY-MM-DD">
    </div>
    <div>
      <label for="total_amount">Total Amount</label>
      <input type="text" id="total_amount" name="total_amount" value="{total_amount}" placeholder="0.00">
    </div>
    <div>
      <label for="vat_amount">VAT Amount</label>
      <input type="text" id="vat_amount" name="vat_amount" value="{vat_amount}" placeholder="0.00">
    </div>
    <div>
      <label for="description">Description</label>
      <div class="ac-wrapper">
        <input type="text" id="description" name="description" value="{description}" placeholder="Enter description…" autocomplete="off">
        <div class="ac-dropdown" id="desc-dropdown"></div>
      </div>
    </div>
    <div>
      <label for="category">Category</label>
      <select id="category" name="category">
        <option value="">— select —</option>
        {category_options}
      </select>
    </div>
    <div class="buttons">
      <button class="btn-cancel" onclick="doCancel()">Cancel</button>
      <button class="btn-confirm" onclick="doConfirm()">Confirm</button>
    </div>
    <div id="done-msg">Done! You can close this tab.</div>
  </div>
</div>
<script>
  function doConfirm() {{
    const data = {{
      date: document.getElementById('date').value,
      total_amount: document.getElementById('total_amount').value,
      vat_amount: document.getElementById('vat_amount').value,
      description: document.getElementById('description').value,
      category: document.getElementById('category').value,
    }};
    fetch('/submit', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify(data),
    }}).then(() => {{
      document.querySelector('.buttons').style.display = 'none';
      document.getElementById('done-msg').style.display = 'block';
    }});
  }}
  function doCancel() {{
    fetch('/cancel', {{method: 'POST'}}).then(() => {{
      document.querySelector('.buttons').style.display = 'none';
      document.getElementById('done-msg').textContent = 'Cancelled.';
      document.getElementById('done-msg').style.display = 'block';
    }});
  }}
  (function() {{
    const inp = document.getElementById('description');
    const dd = document.getElementById('desc-dropdown');
    const sugg = {description_json};
    inp.addEventListener('focus', function() {{ this.select(); }});
    inp.addEventListener('mouseup', function(e) {{ if (this === document.activeElement) e.preventDefault(); }});
    inp.addEventListener('input', function() {{
      const v = this.value.toLowerCase();
      dd.innerHTML = '';
      const hits = sugg.filter(s => s.toLowerCase().includes(v));
      if (!hits.length) {{ dd.style.display = 'none'; return; }}
      hits.forEach(s => {{
        const el = document.createElement('div');
        el.className = 'ac-item';
        el.textContent = s;
        el.addEventListener('mousedown', e => {{ e.preventDefault(); inp.value = s; dd.style.display = 'none'; }});
        dd.appendChild(el);
      }});
      dd.style.display = 'block';
    }});
    inp.addEventListener('blur', () => {{ setTimeout(() => {{ dd.style.display = 'none'; }}, 150); }});
  }})();
</script>
</body>
</html>
"""


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_for_server(port: int, timeout: float = 3.0):
    """Poll until the server is accepting connections, then return."""
    import time
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.05):
                return
        except OSError:
            time.sleep(0.05)


def review_receipt(extracted_data: dict, categories: list[dict], file_path: Path) -> dict | None:
    """Serve a local web form for reviewing/editing extracted receipt data.

    Blocks until the user confirms or cancels, then returns the result dict
    (or None if cancelled).
    """
    port = _free_port()
    result_holder: list[dict | None] = []
    shutdown_event = threading.Event()

    app = Flask(__name__)
    app.logger.disabled = True
    import logging
    log = logging.getLogger("werkzeug")
    log.setLevel(logging.ERROR)

    suffix = file_path.suffix.lower()
    is_pdf = suffix == ".pdf"

    if is_pdf:
        media_tag = f'<iframe src="/image" title="Receipt PDF"></iframe>'
    else:
        media_tag = f'<img src="/image" alt="Receipt image">'

    llm_category = extracted_data.get("category", "")
    options_html = ""
    for cat in categories:
        desc = cat["description"]
        selected = 'selected' if desc == llm_category else ''
        options_html += f'<option value="{desc}" {selected}>{desc}</option>\n'

    description_json = json.dumps(load_descriptions())

    page_html = _HTML_TEMPLATE.format(
        filename=file_path.name,
        media_tag=media_tag,
        date=extracted_data.get("date", ""),
        total_amount=extracted_data.get("total_amount", ""),
        vat_amount=extracted_data.get("vat_amount", "0.00"),
        description=extracted_data.get("description", ""),
        category_options=options_html,
        description_json=description_json,
    )

    @app.route("/")
    def index():
        return page_html

    @app.route("/image")
    def image():
        mime, _ = mimetypes.guess_type(str(file_path))
        return send_file(str(file_path), mimetype=mime or "application/octet-stream")

    @app.route("/submit", methods=["POST"])
    def submit():
        data = request.get_json(force=True)
        save_description(data.get("description", ""))
        result_holder.append(data)
        shutdown_event.set()
        return "", 204

    @app.route("/cancel", methods=["POST"])
    def cancel():
        result_holder.append(None)
        shutdown_event.set()
        return "", 204

    server_thread = threading.Thread(
        target=lambda: app.run(host="127.0.0.1", port=port, use_reloader=False),
        daemon=True,
    )
    server_thread.start()
    _wait_for_server(port)

    url = f"http://127.0.0.1:{port}/"
    webbrowser.open(url)

    shutdown_event.wait()
    return result_holder[0] if result_holder else None


_MULTI_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Multi-Scan Receipts</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    background: #f0f2f5;
    height: 100vh;
    display: flex;
    flex-direction: column;
  }}
  h1 {{
    font-size: 1.1rem;
    padding: 12px 20px;
    background: #1a1a2e;
    color: #fff;
    flex-shrink: 0;
  }}
  .layout {{
    display: flex;
    flex: 1;
    overflow: hidden;
  }}
  .sidebar {{
    width: 220px;
    min-width: 160px;
    background: #fff;
    border-right: 1px solid #ddd;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }}
  .sidebar h2 {{
    font-size: 0.78rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #888;
    padding: 12px 14px 8px;
    border-bottom: 1px solid #eee;
    flex-shrink: 0;
  }}
  .file-list {{
    list-style: none;
    flex: 1;
    overflow-y: auto;
  }}
  .file-list li {{
    padding: 9px 14px;
    font-size: 0.82rem;
    cursor: pointer;
    color: #333;
    border-bottom: 1px solid #f0f0f0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    transition: background 0.1s;
  }}
  .file-list li:hover {{ background: #f4f6ff; }}
  .file-list li.active {{ background: #e8eeff; color: #3a6ae0; font-weight: 600; }}
  .all-done {{
    padding: 20px 14px;
    text-align: center;
    color: #4f7cf8;
    font-weight: 600;
    font-size: 0.9rem;
    display: none;
  }}
  .preview {{
    flex: 1;
    background: #222;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: auto;
    padding: 16px;
    position: relative;
  }}
  .preview img {{
    max-width: 100%;
    max-height: 100%;
    object-fit: contain;
    border-radius: 4px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.5);
  }}
  .preview iframe {{
    width: 100%;
    height: 100%;
    border: none;
    background: #fff;
  }}
  .preview-placeholder {{
    color: #666;
    text-align: center;
  }}
  .preview-placeholder p {{ margin-top: 8px; font-size: 0.9rem; }}
  .spinner {{
    display: none;
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    color: #fff;
    font-size: 0.9rem;
    background: rgba(0,0,0,0.6);
    padding: 12px 20px;
    border-radius: 8px;
  }}
  .panel {{
    width: 380px;
    min-width: 320px;
    background: #fff;
    padding: 24px 20px;
    overflow-y: auto;
    border-left: 1px solid #ddd;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }}
  .panel h2 {{ font-size: 1rem; color: #333; margin-bottom: 4px; }}
  label {{
    display: block;
    font-size: 0.78rem;
    font-weight: 600;
    color: #555;
    margin-bottom: 4px;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }}
  input, select {{
    width: 100%;
    padding: 8px 10px;
    border: 1px solid #ccc;
    border-radius: 6px;
    font-size: 0.95rem;
    color: #222;
    background: #fafafa;
  }}
  input:focus, select:focus {{ outline: none; border-color: #4f7cf8; background: #fff; }}
  input:disabled, select:disabled {{ opacity: 0.5; cursor: not-allowed; }}
  .buttons {{ display: flex; gap: 8px; margin-top: 8px; flex-wrap: wrap; }}
  button {{
    flex: 1;
    padding: 10px;
    border: none;
    border-radius: 6px;
    font-size: 0.9rem;
    font-weight: 600;
    cursor: pointer;
    min-width: 70px;
  }}
  button:disabled {{ opacity: 0.4; cursor: not-allowed; }}
  .btn-confirm {{ background: #4f7cf8; color: #fff; }}
  .btn-confirm:hover:not(:disabled) {{ background: #3a6ae0; }}
  .btn-reprocess {{ background: #eee; color: #555; }}
  .btn-reprocess:hover:not(:disabled) {{ background: #ddd; }}
  .btn-quit {{ background: #fee2e2; color: #b91c1c; }}
  .btn-quit:hover:not(:disabled) {{ background: #fecaca; }}
  .status-msg {{ font-size: 0.82rem; color: #888; text-align: center; min-height: 18px; }}
  .ac-wrapper {{ position: relative; }}
  .ac-dropdown {{
    display: none;
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background: #fff;
    border: 1px solid #ccc;
    border-top: none;
    border-radius: 0 0 6px 6px;
    max-height: 180px;
    overflow-y: auto;
    z-index: 100;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  }}
  .ac-item {{
    padding: 8px 10px;
    font-size: 0.92rem;
    color: #222;
    cursor: pointer;
  }}
  .ac-item:hover {{ background: #e8eeff; color: #3a6ae0; }}
</style>
</head>
<body>
<h1>expense-pal &mdash; Multi-Scan</h1>
<div class="layout">
  <div class="sidebar">
    <h2>Receipts</h2>
    <ul class="file-list" id="fileList"></ul>
    <div class="all-done" id="allDone">All done!</div>
  </div>
  <div class="preview" id="preview">
    <div class="preview-placeholder" id="placeholder">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#555" stroke-width="1.5">
        <rect x="3" y="3" width="18" height="18" rx="2"/>
        <path d="M3 9h18M9 21V9"/>
      </svg>
      <p>Select a file from the list</p>
    </div>
    <div class="spinner" id="spinner">Scanning with Claude&hellip;</div>
  </div>
  <div class="panel">
    <h2>Extracted Data</h2>
    <div>
      <label for="date">Date</label>
      <input type="text" id="date" name="date" placeholder="YYYY-MM-DD" disabled>
    </div>
    <div>
      <label for="total_amount">Total Amount</label>
      <input type="text" id="total_amount" name="total_amount" placeholder="0.00" disabled>
    </div>
    <div>
      <label for="vat_amount">VAT Amount</label>
      <input type="text" id="vat_amount" name="vat_amount" placeholder="0.00" disabled>
    </div>
    <div>
      <label for="description">Description</label>
      <div class="ac-wrapper">
        <input type="text" id="description" name="description" placeholder="Enter description&hellip;" disabled autocomplete="off">
        <div class="ac-dropdown" id="desc-dropdown"></div>
      </div>
    </div>
    <div>
      <label for="category">Category</label>
      <select id="category" name="category" disabled>
        <option value="">— select —</option>
        {category_options}
      </select>
    </div>
    <div>
      <label for="modelSelect">Model</label>
      <select id="modelSelect" name="modelSelect">
        <option value="claude-haiku-4-5-20251001">Haiku</option>
        <option value="claude-sonnet-4-6" selected>Sonnet</option>
        <option value="claude-opus-4-6">Opus</option>
      </select>
    </div>
    <div class="buttons">
      <button class="btn-confirm" onclick="doConfirm()" disabled id="btnConfirm">Confirm</button>
      <button class="btn-reprocess" onclick="doReprocess()" disabled id="btnReprocess">Re-process</button>
      <button class="btn-quit" onclick="doQuit()" id="btnQuit">Quit</button>
    </div>
    <div class="status-msg" id="statusMsg"></div>
  </div>
</div>
{train_section}
<script>
  const TRAIN_MODE = {train_mode};
  let currentFile = null;

  function setStatus(msg) {{
    document.getElementById('statusMsg').textContent = msg;
  }}

  function setFormEnabled(enabled) {{
    ['date', 'total_amount', 'vat_amount', 'description', 'category'].forEach(id => {{
      document.getElementById(id).disabled = !enabled;
    }});
    document.getElementById('btnConfirm').disabled = !enabled;
    document.getElementById('btnReprocess').disabled = !enabled;
  }}

  function resetForm() {{
    ['date', 'total_amount', 'vat_amount', 'description'].forEach(id => {{
      document.getElementById(id).value = '';
    }});
    document.getElementById('category').value = '';
    setFormEnabled(false);
    currentFile = null;
    const preview = document.getElementById('preview');
    const existing = preview.querySelector('img, iframe');
    if (existing) existing.remove();
    document.getElementById('placeholder').style.display = '';
    document.querySelectorAll('.file-list li').forEach(li => li.classList.remove('active'));
  }}

  function loadFiles() {{
    fetch('/files').then(r => r.json()).then(files => {{
      const list = document.getElementById('fileList');
      list.innerHTML = '';
      if (files.length === 0) {{
        document.getElementById('allDone').style.display = 'block';
        list.style.display = 'none';
        setStatus('All receipts processed!');
        setFormEnabled(false);
        currentFile = null;
        const preview = document.getElementById('preview');
        const existing = preview.querySelector('img, iframe');
        if (existing) existing.remove();
        document.getElementById('placeholder').style.display = '';
        return;
      }}
      document.getElementById('allDone').style.display = 'none';
      list.style.display = '';
      files.forEach(name => {{
        const li = document.createElement('li');
        li.textContent = name;
        li.title = name;
        li.onclick = () => selectFile(name);
        list.appendChild(li);
      }});
      if (currentFile) {{
        list.querySelectorAll('li').forEach(li => {{
          if (li.textContent === currentFile) li.classList.add('active');
        }});
      }}
    }});
  }}

  function selectFile(name) {{
    if (currentFile === name) return;
    currentFile = name;
    document.querySelectorAll('.file-list li').forEach(li => {{
      li.classList.toggle('active', li.textContent === name);
    }});
    const preview = document.getElementById('preview');
    const existing = preview.querySelector('img, iframe');
    if (existing) existing.remove();
    document.getElementById('placeholder').style.display = 'none';
    document.getElementById('spinner').style.display = 'block';
    setFormEnabled(false);
    setStatus('Scanning with Claude\u2026');
    const model = document.getElementById('modelSelect').value;
    fetch('/select/' + encodeURIComponent(name), {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{model: model}}),
    }})
      .then(r => r.json())
      .then(data => {{
        document.getElementById('spinner').style.display = 'none';
        const ext = name.split('.').pop().toLowerCase();
        if (ext === 'pdf') {{
          const iframe = document.createElement('iframe');
          iframe.src = '/image/' + encodeURIComponent(name);
          iframe.title = name;
          preview.appendChild(iframe);
        }} else {{
          const img = document.createElement('img');
          img.src = '/image/' + encodeURIComponent(name);
          img.alt = name;
          preview.appendChild(img);
        }}
        document.getElementById('date').value = data.date || '';
        document.getElementById('total_amount').value = data.total_amount || '';
        document.getElementById('vat_amount').value = data.vat_amount || '';
        document.getElementById('description').value = data.description || '';
        document.getElementById('category').value = data.category || '';
        setFormEnabled(true);
        setStatus('');
      }})
      .catch(() => {{
        document.getElementById('spinner').style.display = 'none';
        document.getElementById('placeholder').style.display = '';
        setStatus('Error scanning file.');
      }});
  }}

  function doConfirm() {{
    if (!currentFile) return;
    const data = {{
      filename: currentFile,
      date: document.getElementById('date').value,
      total_amount: document.getElementById('total_amount').value,
      vat_amount: document.getElementById('vat_amount').value,
      description: document.getElementById('description').value,
      category: document.getElementById('category').value,
    }};
    setFormEnabled(false);
    setStatus('Saving\u2026');
    fetch('/submit', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify(data),
    }}).then(r => r.json()).then(() => {{
      const saved = currentFile;
      currentFile = null;
      resetForm();
      setStatus('Saved: ' + saved);
      loadFiles();
    }});
  }}

  function doReprocess() {{
    if (!currentFile) return;
    const model = document.getElementById('modelSelect').value;
    const name = currentFile;
    const preview = document.getElementById('preview');
    setFormEnabled(false);
    document.getElementById('spinner').style.display = 'block';
    setStatus('Re-scanning with Claude\u2026');
    const reprocessBody = {{model: model}};
    if (TRAIN_MODE) {{
      reprocessBody.prompt_template = document.getElementById('promptEditor').value;
    }}
    fetch('/reprocess/' + encodeURIComponent(name), {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify(reprocessBody),
    }})
      .then(r => r.json())
      .then(data => {{
        document.getElementById('spinner').style.display = 'none';
        document.getElementById('date').value = data.date || '';
        document.getElementById('total_amount').value = data.total_amount || '';
        document.getElementById('vat_amount').value = data.vat_amount || '';
        document.getElementById('description').value = data.description || '';
        document.getElementById('category').value = data.category || '';
        setFormEnabled(true);
        setStatus('');
      }})
      .catch(() => {{
        document.getElementById('spinner').style.display = 'none';
        setStatus('Error re-scanning file.');
      }});
  }}

  function doSavePrompt() {{
    const content = document.getElementById('promptEditor').value;
    fetch('/save-prompt', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{prompt_template: content}}),
    }}).then(r => r.json()).then(data => {{
      const el = document.getElementById('promptStatus');
      if (data.ok) {{
        el.style.color = 'green';
        el.textContent = 'Prompt saved.';
      }} else {{
        el.style.color = 'red';
        el.textContent = 'Error: ' + (data.error || 'unknown');
      }}
    }}).catch(() => {{
      const el = document.getElementById('promptStatus');
      el.style.color = 'red';
      el.textContent = 'Error saving prompt.';
    }});
  }}

  function doQuit() {{
    fetch('/quit', {{method: 'POST'}}).then(() => {{
      document.body.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100vh;font-family:sans-serif;color:#555;font-size:1.1rem;">Session ended. You can close this tab.</div>';
    }});
  }}

  loadFiles();
  (function() {{
    const inp = document.getElementById('description');
    const dd = document.getElementById('desc-dropdown');
    const sugg = {description_json};
    inp.addEventListener('focus', function() {{ if (!this.disabled) this.select(); }});
    inp.addEventListener('mouseup', function(e) {{ if (!this.disabled && this === document.activeElement) e.preventDefault(); }});
    inp.addEventListener('input', function() {{
      if (this.disabled) return;
      const v = this.value.toLowerCase();
      dd.innerHTML = '';
      const hits = sugg.filter(s => s.toLowerCase().includes(v));
      if (!hits.length) {{ dd.style.display = 'none'; return; }}
      hits.forEach(s => {{
        const el = document.createElement('div');
        el.className = 'ac-item';
        el.textContent = s;
        el.addEventListener('mousedown', e => {{ e.preventDefault(); inp.value = s; dd.style.display = 'none'; }});
        dd.appendChild(el);
      }});
      dd.style.display = 'block';
    }});
    inp.addEventListener('blur', () => {{ setTimeout(() => {{ dd.style.display = 'none'; }}, 150); }});
  }})();
</script>
</body>
</html>
"""


def _build_train_section(prompt_text: str) -> str:
    # HTML-escape content, then escape braces so .format() in the outer template doesn't choke on
    # {category_list} / {description_list} placeholders present in the prompt file.
    escaped = html.escape(prompt_text).replace("{", "{{").replace("}", "}}")
    return (
        '<div style="padding:1rem;background:#fff;border-top:1px solid #ddd;">'
        '<label style="font-weight:600;font-size:0.85rem;color:#555;">Extraction Prompt</label>'
        '<textarea id="promptEditor" style="width:100%;height:220px;font-family:monospace;'
        'font-size:0.82rem;border:1px solid #ccc;border-radius:4px;padding:0.5rem;'
        'margin-top:0.5rem;resize:vertical;">' + escaped + "</textarea>"
        '<div style="margin-top:0.5rem;display:flex;align-items:center;gap:0.75rem;">'
        '<button onclick="doSavePrompt()" style="padding:0.4rem 1rem;background:#4a90d9;'
        'color:#fff;border:none;border-radius:4px;cursor:pointer;font-size:0.85rem;">'
        "Save Prompt</button>"
        '<span id="promptStatus" style="font-size:0.82rem;"></span>'
        "</div></div>"
    )


def review_receipts_batch(folder: Path, categories: list[dict], train: bool = False) -> list[dict]:
    """Serve a persistent web UI for batch-processing receipts from a folder.

    Blocks until the user clicks Quit or all files are processed.
    Returns list of all confirmed expense entry dicts (with nominal codes).
    """
    from expense_pal.scanner import scan_receipt
    from expense_pal.categories import get_nominal_code
    from expense_pal.config import EXPENSES_LOG

    SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf"}

    def get_pending_files() -> list[str]:
        return sorted(
            f.name for f in folder.iterdir()
            if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
        )

    port = _free_port()
    confirmed_entries: list[dict] = []
    shutdown_event = threading.Event()
    scan_cache: dict[str, dict] = {}

    app = Flask(__name__)
    app.logger.disabled = True
    import logging
    log = logging.getLogger("werkzeug")
    log.setLevel(logging.ERROR)

    options_html = ""
    for cat in categories:
        desc = cat["description"]
        options_html += f'<option value="{desc}">{desc}</option>\n'

    description_json = json.dumps(load_descriptions())

    from expense_pal.scanner import PROMPTS_FILE
    train_section = _build_train_section(PROMPTS_FILE.read_text()) if train else ""
    train_mode_js = "true" if train else "false"

    page_html = _MULTI_HTML_TEMPLATE.format(
        category_options=options_html,
        description_json=description_json,
        train_section=train_section,
        train_mode=train_mode_js,
    )

    @app.route("/")
    def index():
        return page_html

    @app.route("/files")
    def files():
        return jsonify(get_pending_files())

    @app.route("/select/<filename>", methods=["POST"])
    def select_file(filename):
        file_path = folder / filename
        if not file_path.exists():
            return jsonify({"error": "File not found"}), 404
        if filename in scan_cache:
            return jsonify(scan_cache[filename])
        body = request.get_json(force=True, silent=True) or {}
        model = body.get("model")
        extracted = scan_receipt(file_path, model=model)
        scan_cache[filename] = extracted
        return jsonify(extracted)

    @app.route("/reprocess/<filename>", methods=["POST"])
    def reprocess_file(filename):
        file_path = folder / filename
        if not file_path.exists():
            return jsonify({"error": "File not found"}), 404
        scan_cache.pop(filename, None)
        body = request.get_json(force=True, silent=True) or {}
        model = body.get("model")
        prompt_template = body.get("prompt_template") if train else None
        extracted = scan_receipt(file_path, model=model, prompt_template_override=prompt_template)
        scan_cache[filename] = extracted
        return jsonify(extracted)

    @app.route("/save-prompt", methods=["POST"])
    def save_prompt():
        if not train:
            return jsonify({"error": "Train mode is not enabled"}), 403
        from expense_pal.scanner import PROMPTS_FILE
        body = request.get_json(force=True, silent=True) or {}
        content = body.get("prompt_template", "")
        PROMPTS_FILE.write_text(content)
        return jsonify({"ok": True})

    @app.route("/image/<filename>")
    def image(filename):
        file_path = folder / filename
        mime, _ = mimetypes.guess_type(str(file_path))
        return send_file(str(file_path), mimetype=mime or "application/octet-stream")

    @app.route("/submit", methods=["POST"])
    def submit():
        data = request.get_json(force=True)
        save_description(data.get("description", ""))
        filename = data.get("filename", "")
        file_path = folder / filename
        nominal_code = get_nominal_code(data.get("category", "")) or ""
        entry = {
            "date": data.get("date", ""),
            "total_amount": data.get("total_amount", ""),
            "vat_amount": data.get("vat_amount", ""),
            "category": data.get("category", ""),
            "category_nominal_code": nominal_code,
            "description": data.get("description", ""),
            "source_file": str(file_path),
            "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        confirmed_entries.append(entry)
        with EXPENSES_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        scan_cache.pop(filename, None)
        done_dir = folder / "done"
        done_dir.mkdir(exist_ok=True)
        if file_path.exists():
            file_path.rename(done_dir / filename)
        pending = get_pending_files()
        if not pending:
            t = threading.Timer(1.5, shutdown_event.set)
            t.daemon = True
            t.start()
        return jsonify({"ok": True})

    @app.route("/quit", methods=["POST"])
    def quit_():
        shutdown_event.set()
        return "", 204

    server_thread = threading.Thread(
        target=lambda: app.run(host="127.0.0.1", port=port, use_reloader=False),
        daemon=True,
    )
    server_thread.start()
    _wait_for_server(port)

    url = f"http://127.0.0.1:{port}/"
    webbrowser.open(url)

    shutdown_event.wait()
    return confirmed_entries
