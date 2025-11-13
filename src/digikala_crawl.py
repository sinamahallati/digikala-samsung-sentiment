import argparse
import csv
import time
from typing import Any, Dict, List, Optional

import requests

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

HEADERS_BASE = {
    "User-Agent": USER_AGENT,
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "fa-IR,fa;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive",
    "Referer": "https://www.digikala.com/",
}

HOME = "https://www.digikala.com/"
CAT_SEARCH = "https://api.digikala.com/v1/categories/mobile-phone/search/"
PDP_V2 = "https://api.digikala.com/v2/product/{id}/"
PDP_V1 = "https://api.digikala.com/v1/product/{id}/"
CMT_V2 = "https://api.digikala.com/v2/product/{id}/comments/"
CMT_V1 = "https://api.digikala.com/v1/product/{id}/comments/"

SAMSUNG_TEXTS = {"Samsung","SAMSUNG","samsung","سامسونگ"}


def safe_get(d: Dict[str, Any], path: List[str], default=None):
    cur = d
    for p in path:
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        else:
            return default
    return cur

def build_session(headers_extra: Optional[Dict[str, str]] = None) -> requests.Session:
    s = requests.Session()
    headers = HEADERS_BASE.copy()
    if headers_extra:
        headers.update(headers_extra)
    s.headers.update(headers)
    try:
        s.get(HOME, timeout=15)
    except Exception:
        pass
    return s

def fetch_json(s: requests.Session, url: str, params: Optional[Dict[str, Any]] = None, retries: int = 2, pause: float = 0.8) -> Optional[Dict[str, Any]]:
    for i in range(retries + 1):
        try:
            r = s.get(url, params=params, timeout=25)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return r.json()
        except Exception:
            if i < retries:
                time.sleep(pause * (i + 1))
            else:
                return None

def pager_total_pages(payload: Dict[str, Any]) -> Optional[int]:
    for keys in (["data","pager","total_pages"], ["data","pager","total"]):
        v = safe_get(payload, keys)
        if isinstance(v, int) and v > 0:
            return v
    return None

def is_samsung_from_pdp(detail: Dict[str, Any]) -> bool:
    pr = safe_get(detail, ["data","product"], {}) or {}
    b_fa = safe_get(pr, ["brand","title_fa"]) or safe_get(pr, ["brand","title"])
    b_en = safe_get(pr, ["brand","title_en"])
    b_code = safe_get(pr, ["brand","code"])
    return any(str(x).strip() in SAMSUNG_TEXTS for x in [b_fa, b_en, b_code])

def enumerate_all_mobile_ids(s: requests.Session, list_pages: int, delay: float, debug: bool) -> List[int]:
    ids: List[int] = []
    page, total_pages = 1, None
    while True:
        payload = fetch_json(s, CAT_SEARCH, params={"page": page})
        if not payload:
            if debug: print(f"[DEBUG] page {page}: no payload")
            break
        products = safe_get(payload, ["data","products"], [])
        if isinstance(products, list):
            for p in products:
                pid = p.get("id") or safe_get(p, ["data","id"])
                if isinstance(pid, int):
                    ids.append(pid)
        if total_pages is None:
            total_pages = pager_total_pages(payload)
            if debug: print(f"[DEBUG] total_pages={total_pages}")
        if list_pages and page >= list_pages:
            break
        if isinstance(total_pages, int) and page >= total_pages:
            break
        if not products:
            break
        page += 1
        if delay: time.sleep(delay)
    return list(dict.fromkeys(ids))

def pdp_info(s: requests.Session, pid: int) -> Optional[Dict[str, Any]]:
    for tmpl in (PDP_V2, PDP_V1):
        data = fetch_json(s, tmpl.format(id=pid))
        if data:
            return data
    return None

def pick_product_row(detail: Dict[str, Any]) -> Dict[str, Any]:
    p = safe_get(detail, ["data","product"], {}) or {}
    pid = p.get("id")
    title_fa = p.get("title_fa") or p.get("title")
    title_en = p.get("title_en")
    selling = (safe_get(p, ["default_variant","price","selling_price"]) or
               safe_get(p, ["price","selling_price"]) or
               safe_get(p, ["default_variant_price"]) or None)
    rrp = (safe_get(p, ["default_variant","price","rrp_price"]) or
           safe_get(p, ["price","rrp_price"]) or None)
    rating_avg = safe_get(p, ["rating","rate"]) or safe_get(p, ["rating","rating"])
    rating_count = safe_get(p, ["rating","count"]) or safe_get(p, ["review_count"])
    return {
        "id": pid,
        "title_fa": title_fa,
        "title_en": title_en,
        "selling_price": selling,
        "rrp_price": rrp,
        "rating_avg": rating_avg,
        "rating_count": rating_count,
    }

def fetch_comments_min(s: requests.Session, pid: int, per_product_pages: int, delay: float, max_comments: int) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for base in (CMT_V2, CMT_V1):
        page = 1
        stop = False
        while True:
            if max_comments and len(rows) >= max_comments:
                stop = True
                break
            data = fetch_json(s, base.format(id=pid), params={"page": page})
            if not data:
                break
            comments = safe_get(data, ["data","comments"]) or safe_get(data, ["data","product","comments"])
            if isinstance(comments, dict) and "comments" in comments:
                comments = comments["comments"]
            if not isinstance(comments, list) or not comments:
                break
            for c in comments:
                if max_comments and len(rows) >= max_comments:
                    stop = True
                    break
                cid = c.get("id") or c.get("comment_id") or ""
                text = c.get("body") or c.get("text") or c.get("title") or ""
                created = (c.get("created_at") or c.get("creation_date") or
                           c.get("created_at_fa") or c.get("date") or "")
                rating = c.get("rate") or c.get("rating") or c.get("score") or None
                rows.append({
                    "product_id": pid,
                    "product_title": None,  # fill later
                    "comment_id": cid,
                    "created_at": created,
                    "rating": rating,
                    "comment_text": text,
                })
            if stop:
                break
            if per_product_pages and page >= per_product_pages:
                break
            page += 1
            if delay: time.sleep(delay)
        if rows:
            break
    return rows

def run(list_pages: int = 0,
        max_products: int = 0,
        per_product_pages: int = 0,
        per_product_max_comments: int = 500,
        delay: float = 0.6,
        debug: bool = False):
    s = build_session()

    ids = enumerate_all_mobile_ids(s, list_pages=list_pages, delay=delay, debug=debug)
    if debug:
        print(f"[DEBUG] enumerated {len(ids)} product IDs from ALL mobile pages")

    if not ids:
        print("[ERROR] No product IDs from category pages."); return

    products_out: List[Dict[str, Any]] = []
    reviews_out: List[Dict[str, Any]] = []

    count = 0
    for pid in ids:
        if max_products and count >= max_products:
            break

        detail = pdp_info(s, pid)
        if not detail or not is_samsung_from_pdp(detail):
            continue

        prod = pick_product_row(detail)
        products_out.append(prod)

        cmts = fetch_comments_min(s, pid, per_product_pages=per_product_pages, delay=delay, max_comments=per_product_max_comments)
        if cmts:
            title = prod.get("title_fa") or prod.get("title_en")
            for r in cmts:
                r["product_title"] = title
                reviews_out.append(r)

        count += 1
        if debug and count % 20 == 0:
            print(f"[DEBUG] processed {count} products; reviews so far: {len(reviews_out)}")
        if delay: time.sleep(delay)

    if not products_out and not reviews_out:
        print("[DONE] Nothing collected."); return

    prod_file = "Digikala_products.csv"
    rev_file  = "Digikala_comments.csv"

    prod_keys = ["id","title_fa","title_en","selling_price","rrp_price","rating_avg","rating_count"]
    with open(prod_file, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=prod_keys)
        w.writeheader()
        for r in products_out:
            w.writerow({k: r.get(k) for k in prod_keys})

    rev_keys = ["product_id","product_title","comment_id","created_at","rating","comment_text"]
    with open(rev_file, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rev_keys)
        w.writeheader()
        for r in reviews_out:
            w.writerow({k: r.get(k) for k in rev_keys})

    print(f"[DONE] Wrote {prod_file} ({len(products_out)} products) and {rev_file} ({len(reviews_out)} reviews).")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list-pages", type=int, default=0)
    ap.add_argument("--max-products", type=int, default=0)
    ap.add_argument("--per-product-pages", type=int, default=0)
    ap.add_argument("--per-product-max-comments", type=int, default=500)
    ap.add_argument("--delay", type=float, default=0.6)
    ap.add_argument("--debug", action="store_true")
    args, _ = ap.parse_known_args()

    run(
        list_pages=args.list_pages,
        max_products=args.max_products,
        per_product_pages=args.per_product_pages,
        per_product_max_comments=args.per_product_max_comments,
        delay=args.delay,
        debug=args.debug
    )


if __name__ == "__main__":
    main()
