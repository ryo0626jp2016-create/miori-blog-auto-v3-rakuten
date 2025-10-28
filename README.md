# みおりのブログ自動更新 — v3（Rakuten自動アフィリンク対応）

- v2の機能（2000〜3000字、豆知識×3、学術メモ、キーワードローテ、Actions、自動投稿）に加え、
- **楽天APIでアフィリエイトリンクを自動生成**（CTAや比較欄に反映）
  - APIが未設定のときは **`DEFAULT_RAKUTEN_LINK` に自動フォールバック**

## 必要なもの
- OpenAI API キー
- **楽天アプリID**（applicationId）
- **楽天アフィリエイトID**（affiliateId）

## .env（ローカル開発用）
```
OPENAI_API_KEY=YOUR_OPENAI_KEY
OPENAI_MODEL=gpt-4.1-mini
TIMEZONE=Asia/Tokyo
DEFAULT_RAKUTEN_LINK=
DEFAULT_SOURCE_URL=https://example.com

# --- Rakuten API ---
RAKUTEN_APPLICATION_ID=
RAKUTEN_AFFILIATE_ID=

# --- WordPress（任意） ---
WP_BASE_URL=
WP_USERNAME=
WP_APP_PASSWORD=
WP_POST_STATUS=draft
WP_CATEGORY_ID=0
WP_TAGS=美容,レビュー,みおり
```

## GitHub Secrets（Actions用）
- `OPENAI_API_KEY`（必須）
- `OPENAI_MODEL`（任意）
- `DEFAULT_SOURCE_URL`（任意）
- **`RAKUTEN_APPLICATION_ID` / `RAKUTEN_AFFILIATE_ID`（推奨）**
- （任意）`WP_BASE_URL` / `WP_USERNAME` / `WP_APP_PASSWORD` / `WP_POST_STATUS` / `WP_CATEGORY_ID` / `WP_TAGS`

## 使い方
```bash
pip install -r requirements.txt
cp .env.example .env
# .env に各キーを設定

# 生成のみ（APIが設定されていれば楽天リンク自動生成）
python run.py --url "https://example.com"

# キーワード固定＆WP投稿
python run.py --url "https://example.com" --keyword "ビタミンC" --post true
```
