import mimetypes
import socket
import threading
import webbrowser
from pathlib import Path

from flask import Flask, request, send_file


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
      <input type="text" id="description" name="description" value="{description}" placeholder="Enter description…">
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
</script>
</body>
</html>
"""


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


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

    page_html = _HTML_TEMPLATE.format(
        filename=file_path.name,
        media_tag=media_tag,
        date=extracted_data.get("date", ""),
        total_amount=extracted_data.get("total_amount", ""),
        vat_amount=extracted_data.get("vat_amount", "0.00"),
        description=extracted_data.get("description", ""),
        category_options=options_html,
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

    url = f"http://127.0.0.1:{port}/"
    webbrowser.open(url)

    shutdown_event.wait()
    return result_holder[0] if result_holder else None
