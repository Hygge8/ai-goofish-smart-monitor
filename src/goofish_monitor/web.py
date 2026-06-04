from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from .config import load_config
from .db import SeenStore

app = FastAPI(title="闲鱼摩托车监控助手")


@app.get("/", response_class=HTMLResponse)
def index():
    try:
        config = load_config("config.yaml")
        store = SeenStore(config.storage_db)
        items = store.latest(30)
    except Exception as exc:
        items = []
        error = str(exc)
    else:
        error = ""

    rows = "".join(
        f"""
        <tr>
          <td><img src="{item.get('image_url','')}" style="width:80px;height:80px;object-fit:cover;border-radius:8px"></td>
          <td>{item.get('title','')}</td>
          <td>{item.get('price','')}</td>
          <td>{item.get('location','')}</td>
          <td><a href="{item.get('item_link','#')}" target="_blank">查看</a></td>
        </tr>
        """
        for item in items
    )
    return f"""
    <!doctype html>
    <html lang="zh-CN">
    <head>
      <meta charset="utf-8" />
      <title>闲鱼摩托车监控助手</title>
      <style>
        body {{ font-family: Arial, 'Microsoft YaHei', sans-serif; margin: 24px; background: #f6f7f9; }}
        .card {{ background:#fff; border-radius:12px; padding:20px; box-shadow:0 2px 12px rgba(0,0,0,.06); }}
        table {{ border-collapse: collapse; width:100%; }}
        th,td {{ border-bottom:1px solid #eee; padding:10px; text-align:left; }}
        th {{ background:#fafafa; }}
        .error {{ color:#b00020; }}
      </style>
    </head>
    <body>
      <div class="card">
        <h1>闲鱼摩托车监控助手</h1>
        <p class="error">{error}</p>
        <table>
          <thead><tr><th>图片</th><th>标题</th><th>价格</th><th>地区</th><th>链接</th></tr></thead>
          <tbody>{rows}</tbody>
        </table>
      </div>
    </body>
    </html>
    """


@app.get("/api/latest")
def latest(limit: int = 20):
    config = load_config("config.yaml")
    return SeenStore(config.storage_db).latest(limit)
