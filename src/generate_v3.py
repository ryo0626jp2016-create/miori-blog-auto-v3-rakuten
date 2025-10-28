import os, json, datetime as dt, re, random, requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI
from .rakuten import is_ready as rak_ready, search_items

def load_env():
    load_dotenv()
    env = {
        "OPENAI_MODEL": os.getenv("OPENAI_MODEL","gpt-4.1-mini"),
        "DEFAULT_RAKUTEN_LINK": os.getenv("DEFAULT_RAKUTEN_LINK",""),
        "DEFAULT_SOURCE_URL": os.getenv("DEFAULT_SOURCE_URL","https://example.com"),
        # WordPress
        "WP_BASE_URL": os.getenv("WP_BASE_URL",""),
        "WP_USERNAME": os.getenv("WP_USERNAME",""),
        "WP_APP_PASSWORD": os.getenv("WP_APP_PASSWORD",""),
        "WP_POST_STATUS": os.getenv("WP_POST_STATUS","draft"),
        "WP_CATEGORY_ID": os.getenv("WP_CATEGORY_ID","0"),
        "WP_TAGS": os.getenv("WP_TAGS","美容,レビュー,みおり"),
    }
    return env

def fetch_meta(url: str):
    try:
        r = requests.get(url, timeout=20, headers={"User-Agent":"Mozilla/5.0 (Miori-v3)"})
        r.raise_for_status()
        html = r.text
    except Exception:
        html = ""
    soup = BeautifulSoup(html, "lxml") if html else BeautifulSoup("", "lxml")
    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    ogd = soup.find("meta", attrs={"property":"og:description"}) or soup.find("meta", attrs={"name":"description"})
    desc = ogd["content"].strip() if ogd and ogd.get("content") else ""
    ogi = soup.find("meta", attrs={"property":"og:image"})
    img = ogi["content"].strip() if ogi and ogi.get("content") else ""
    return {"title":title, "description":desc, "image":img}

def load_keywords(path: str):
    if not os.path.exists(path): return []
    with open(path, "r", encoding="utf-8") as f:
        return [x.strip() for x in f.read().splitlines() if x.strip()]

def build_variables(meta: dict, rakuten_link: str, keyword: str, rakuten_items: list):
    today = dt.datetime.now().strftime("%Y/%m/%d")
    raw_title = meta.get("title","")
    product = re.sub(r"【.*?】|\|.*$", "", raw_title).strip()[:60] or "サンプル商品"
    sneak = "無理なく続ければ体感しやすいポイントがいくつかありました"

    # Defaults
    vars = {
        "商品名": product,
        "ブランド名": "",
        "特集キーワード": keyword or "スキンケア",
        "悩みキーワード": keyword or "肌荒れ",
        "更新日": today,
        "継続日数": "14日",
        "推奨期間": "14日〜4週間",
        "主成分": "",
        "形状": "サプリ/美容液/クリーム など",
        "内容量": "",
        "使用タイミング": "朝/夜",
        "用量": "",
        "併用スキンケア": "",
        "失敗回避": "飲み忘れアラーム/パッチテスト など",
        "変化_日": "7",
        "感じた変化_日": "",
        "変化_週": "2",
        "感じた変化_週": "",
        "変化_月": "1",
        "感じた変化_月": "",
        "結論チラ見せ": sneak,
        "学術メモ本文": "",
        "豆知識1": "",
        "豆知識2": "",
        "豆知識3": "",
        "特徴_本品": "",
        "価格_本品": "¥◯◯◯〜（ポイント◯倍時）",
        "比較商品A_名称": "",
        "比較商品A_特徴": "",
        "比較商品A_成分量": "",
        "比較商品A_価格": "",
        "比較商品B_名称": "",
        "比較商品B_特徴": "",
        "比較商品B_成分量": "",
        "比較商品B_価格": "",
        "良い口コミ1": "",
        "良い口コミ1_属性": "",
        "良い口コミ2": "",
        "良い口コミ2_属性": "",
        "悪い口コミ1": "",
        "悪い口コミ2": "",
        "レビュー件数": "",
        "目安期間": "14日〜4週間",
        "注意成分": "ビタミンA/ピーリング/薬の飲み合わせ など",
        "商品画像URL1": meta.get("image",""),
        "商品画像URL2": meta.get("image",""),
        "楽天_最安候補": rakuten_link,
        "楽天_販売ページA": rakuten_link,
        "楽天_比較A": rakuten_link,
        "楽天_比較B": rakuten_link,
        "楽天_レビュー多い店舗": rakuten_link,
        "楽天_価格比較まとめ": rakuten_link
    }

    # Fill from Rakuten API top 3 items
    if rakuten_items:
        # top-1 to CTA
        top = rakuten_items[0]
        vars["楽天_最安候補"] = top.get("affiliateUrl") or top.get("itemUrl","") or rakuten_link
        vars["商品名"] = vars["商品名"] or top.get("name","")
        if top.get("imageUrl"): vars["商品画像URL1"] = top["imageUrl"]
        vars["価格_本品"] = top.get("price","")

        # top-2 & top-3 for comparison rows
        if len(rakuten_items) > 1:
            a = rakuten_items[1]
            vars["比較商品A_名称"] = a.get("name","")
            vars["比較商品A_特徴"] = a.get("shopName","")
            vars["比較商品A_価格"] = a.get("price","")
            vars["楽天_比較A"] = a.get("affiliateUrl") or a.get("itemUrl","") or rakuten_link
        if len(rakuten_items) > 2:
            b = rakuten_items[2]
            vars["比較商品B_名称"] = b.get("name","")
            vars["比較商品B_特徴"] = b.get("shopName","")
            vars["比較商品B_価格"] = b.get("price","")
            vars["楽天_比較B"] = b.get("affiliateUrl") or b.get("itemUrl","") or rakuten_link

    return vars

def render_prompt(template_html: str, variables: dict):
    here = os.path.dirname(__file__)
    with open(os.path.join(here, "prompt_master.txt"), "r", encoding="utf-8") as f:
        master = f.read()
    return master.replace("{{TEMPLATE_HTML}}", template_html)\
                 .replace("{{VARIABLES_JSON}}", json.dumps(variables, ensure_ascii=False))

def call_openai(prompt: str, model: str, max_tokens: int = 3600) -> str:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role":"system","content":"指定以外の文字を出さず、HTML本文のみを返します。本文が2000〜3000字になるように調整し、豆知識×3と学術メモを必ず含めてください。"},
            {"role":"user","content":prompt}
        ],
        temperature=0.5,
        max_tokens=max_tokens
    )
    return resp.choices[0].message.content.strip()

def save_html(text: str) -> str:
    out_dir = os.path.join(os.path.dirname(__file__), "..", "dist")
    os.makedirs(out_dir, exist_ok=True)
    ts = dt.datetime.now().strftime("%Y%m%d_%H%M")
    path = os.path.join(out_dir, f"{ts}_miori.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return path

def try_post_wp(html: str, env: dict) -> str:
    base = env.get("WP_BASE_URL","").strip()
    user = env.get("WP_USERNAME","").strip()
    app = env.get("WP_APP_PASSWORD","").strip()
    status = env.get("WP_POST_STATUS","draft")
    cat_id = int(env.get("WP_CATEGORY_ID","0") or 0)
    tags = [t.strip() for t in env.get("WP_TAGS","").split(",") if t.strip()]
    if not (base and user and app):
        print("[INFO] WP env not set. Skip posting.")
        return ""
    import base64, requests, re, json as _json
    token = base64.b64encode(f"{user}:{app}".encode()).decode()
    headers = {"Authorization": f"Basic {token}", "Content-Type":"application/json"}
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S)
    title = m.group(1).strip() if m else "自動生成記事"
    data = {"title": title, "content": html, "status": status}
    if cat_id: data["categories"] = [cat_id]
    if tags: data["tags"] = tags
    api = f"{base.rstrip('/')}/wp-json/wp/v2/posts"
    r = requests.post(api, headers=headers, data=_json.dumps(data), timeout=30)
    if r.status_code not in (200,201):
        raise RuntimeError(f"WP post error: {r.status_code} {r.text}")
    link = r.json().get("link","")
    return link

def main(url: str, keyword: str = "", post: bool = False):
    env = load_env()

    # Meta
    meta = fetch_meta(url)

    # Keyword
    if not keyword:
        pool = []
        try:
            with open(os.path.join(os.path.dirname(__file__), "..", "data", "keywords.txt"), "r", encoding="utf-8") as f:
                pool = [x.strip() for x in f.read().splitlines() if x.strip()]
        except Exception:
            pass
        if pool:
            keyword = random.choice(pool)
        else:
            keyword = "スキンケア"

    # Rakuten API fetch (best-effort)
    rakuten_items = []
    if rak_ready():
        try:
            rakuten_items = search_items(keyword, hits=3)
        except Exception as e:
            print("[WARN] Rakuten API error:", e)

    # Variables
    rak_base = env["DEFAULT_RAKUTEN_LINK"]
    variables = build_variables(meta, rak_base, keyword, rakuten_items)

    # Prompt
    here = os.path.dirname(__file__)
    with open(os.path.join(here, "template_wp.html"), "r", encoding="utf-8") as f:
        template_html = f.read()
    prompt = render_prompt(template_html, variables)

    # LLM
    html = call_openai(prompt, env["OPENAI_MODEL"])

    # Save
    out_path = save_html(html)
    print("[OK] Saved:", out_path)

    # Post
    if post:
        link = try_post_wp(html, env)
        if link:
            print("[OK] Posted to WordPress:", link)

if __name__ == "__main__":
    import argparse, datetime as dt
    p = argparse.ArgumentParser()
    p.add_argument("--url", default=os.getenv("DEFAULT_SOURCE_URL","https://example.com"))
    p.add_argument("--keyword", default="")
    p.add_argument("--post", default="false")
    a = p.parse_args()
    main(a.url, a.keyword, str(a.post).lower() in ("1","true","yes","on"))
