from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .storage import atomic_write_text


def _embedded_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def render_dashboard(entries: list[dict[str, Any]]) -> str:
    data = _embedded_json(entries)
    return f"""<!doctype html>
<html lang=\"ja\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">
  <title>Slide System - 制作一覧</title>
  <style>
    :root {{ color-scheme: light; --bg:#f5f2f0; --surface:#fffaf7; --text:#443a3a; --muted:#746868; --accent:#de837d; --line:#eaded8; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:var(--bg); color:var(--text); font-family:"Noto Sans JP","Yu Gothic",Meiryo,sans-serif; }}
    header {{ padding:36px clamp(20px,5vw,72px) 24px; background:var(--surface); border-bottom:1px solid var(--line); }}
    h1 {{ margin:0 0 8px; font-size:clamp(28px,4vw,44px); }}
    header p {{ margin:0; color:var(--muted); }}
    main {{ max-width:1280px; margin:auto; padding:28px clamp(20px,5vw,72px) 64px; }}
    .tools {{ display:flex; flex-wrap:wrap; gap:12px; margin-bottom:24px; }}
    input,select {{ min-height:44px; border:1px solid var(--line); border-radius:12px; background:white; color:var(--text); padding:0 14px; font:inherit; }}
    input {{ flex:1 1 280px; }}
    .count {{ margin:0 0 16px; color:var(--muted); }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(300px,1fr)); gap:20px; }}
    article {{ overflow:hidden; background:white; border:1px solid var(--line); border-radius:20px; box-shadow:0 10px 28px #5d45450d; }}
    .thumb {{ display:grid; place-items:center; aspect-ratio:16/9; background:var(--surface); border-bottom:1px solid var(--line); color:var(--muted); }}
    .thumb img {{ width:100%; height:100%; object-fit:cover; }}
    .body {{ padding:20px; }}
    .status {{ display:inline-block; margin-bottom:12px; border-radius:999px; background:#fde7e3; color:#8c4540; padding:6px 10px; font-size:13px; font-weight:700; }}
    h2 {{ margin:0 0 8px; font-size:21px; line-height:1.4; }}
    .summary {{ min-height:3em; margin:0 0 14px; color:var(--muted); line-height:1.55; }}
    dl {{ display:grid; grid-template-columns:auto 1fr; gap:6px 12px; margin:0 0 16px; font-size:14px; }}
    dt {{ color:var(--muted); }} dd {{ margin:0; }}
    .next {{ margin:0 0 16px; padding:12px; border-left:4px solid var(--accent); background:var(--surface); font-size:14px; line-height:1.5; }}
    .actions {{ display:flex; flex-wrap:wrap; gap:8px; }}
    a {{ display:inline-flex; align-items:center; min-height:38px; border-radius:10px; background:var(--text); color:white; padding:0 12px; text-decoration:none; font-size:14px; font-weight:700; }}
    a.secondary {{ background:white; color:var(--text); border:1px solid var(--line); }}
    .empty {{ padding:48px 24px; text-align:center; background:white; border:1px dashed var(--line); border-radius:20px; color:var(--muted); }}
  </style>
</head>
<body>
  <header><h1>Slide System</h1><p>過去の制作をタイトル、更新日時、状態から探せます。</p></header>
  <main>
    <div class=\"tools\">
      <input id=\"query\" type=\"search\" placeholder=\"タイトル・概要・タグで検索\" aria-label=\"制作を検索\">
      <select id=\"status\" aria-label=\"状態で絞り込み\"><option value=\"\">すべての状態</option></select>
    </div>
    <p class=\"count\" id=\"count\"></p>
    <section class=\"grid\" id=\"grid\"></section>
  </main>
  <script type=\"application/json\" id=\"run-index\">{data}</script>
  <script>
    const runs = JSON.parse(document.getElementById('run-index').textContent);
    const query = document.getElementById('query');
    const status = document.getElementById('status');
    const grid = document.getElementById('grid');
    const count = document.getElementById('count');
    const statuses = [...new Map(runs.map(run => [run.status, run.status_label])).entries()];
    for (const [value,label] of statuses) {{ const option=document.createElement('option'); option.value=value; option.textContent=label; status.appendChild(option); }}
    const text = (tag,value,cls) => {{ const node=document.createElement(tag); node.textContent=value || ''; if(cls) node.className=cls; return node; }};
    function card(run) {{
      const article=document.createElement('article');
      const thumb=text('div','表紙プレビュー未生成','thumb');
      if(run.thumbnail) {{ const img=document.createElement('img'); img.src=run.thumbnail; img.alt=`${{run.title}}の表紙`; thumb.replaceChildren(img); }}
      const body=text('div','','body'); body.append(text('span',run.status_label,'status'),text('h2',run.title),text('p',run.summary || '概要はまだ登録されていません。','summary'));
      const dl=document.createElement('dl');
      for(const [label,value] of [['更新',run.updated_label],['AI',run.adapter || '未設定'],['デザイン',run.design_pack || '未設定']]) {{ dl.append(text('dt',label),text('dd',value)); }}
      body.append(dl,text('p',run.next_action || '次の操作はまだ登録されていません。','next'));
      const actions=text('div','','actions');
      if(run.html) {{ const a=text('a','HTMLを開く'); a.href=run.html; actions.append(a); }}
      if(run.pdf) {{ const a=text('a','PDFを開く','secondary'); a.href=run.pdf; actions.append(a); }}
      const folder=text('a','制作フォルダ','secondary'); folder.href=`./${{run.run_id}}/`; actions.append(folder); body.append(actions);
      article.append(thumb,body); return article;
    }}
    function render() {{
      const q=query.value.trim().toLocaleLowerCase('ja');
      const visible=runs.filter(run => (!status.value || run.status===status.value) && (!q || run.search_text.includes(q)));
      count.textContent=`${{visible.length}}件の制作`;
      grid.replaceChildren(...(visible.length ? visible.map(card) : [text('div','該当する制作はありません。','empty')]));
    }}
    query.addEventListener('input',render); status.addEventListener('change',render); render();
  </script>
</body>
</html>
"""


def write_dashboard(path: Path, entries: list[dict[str, Any]]) -> None:
    atomic_write_text(path, render_dashboard(entries))
