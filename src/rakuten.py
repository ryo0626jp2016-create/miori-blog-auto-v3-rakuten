import os, requests

RAKUTEN_ENDPOINT = "https://app.rakuten.co.jp/services/api/IchibaItem/Search/20170706"

def is_ready():
    return bool(os.getenv("RAKUTEN_APPLICATION_ID") and os.getenv("RAKUTEN_AFFILIATE_ID"))

def search_items(keyword: str, hits: int = 3):
    """
    Returns list of items: [{name, price, affiliateUrl, shopName}]
    If affiliateId is set, response includes affiliateUrl (otherwise normal itemUrl).
    """
    params = {
        "applicationId": os.getenv("RAKUTEN_APPLICATION_ID",""),
        "affiliateId": os.getenv("RAKUTEN_AFFILIATE_ID",""),
        "keyword": keyword,
        "hits": hits,
        "sort": "-reviewAverage",   # レビュー平均の高い順（必要に応じて変更可）
        "imageFlag": 1
    }
    r = requests.get(RAKUTEN_ENDPOINT, params=params, timeout=20)
    r.raise_for_status()
    js = r.json()
    items = []
    for it in js.get("Items", []):
        i = it.get("Item", {})
        items.append({
            "name": i.get("itemName",""),
            "price": f"¥{i.get('itemPrice', '')}",
            "affiliateUrl": i.get("affiliateUrl") or i.get("itemUrl",""),
            "shopName": i.get("shopName",""),
            "imageUrl": i.get("mediumImageUrls",[{"imageUrl":""}])[0]["imageUrl"]
        })
    return items
