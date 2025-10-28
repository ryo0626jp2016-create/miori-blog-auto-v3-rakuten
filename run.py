import argparse
from src.generate_v3 import main

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--url", default="https://example.com")
    p.add_argument("--keyword", default="")
    p.add_argument("--post", default="false")
    args = p.parse_args()
    main(args.url, args.keyword, str(args.post).lower() in ("1","true","yes","on"))
