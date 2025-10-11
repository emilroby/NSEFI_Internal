# publish_month.py
from __future__ import annotations
import sys
from backend import write_month_snapshot
from backend import harvest_ctuil_month

def main():
    if len(sys.argv) < 3:
        print("Usage: python publish_month.py YYYY MM")
        sys.exit(2)
    y, m = int(sys.argv[1]), int(sys.argv[2])

    central = []
    #try:
        #central += harvest_cerc_month(y, m)
    #except Exception as e:
     #   print("CERC err:", e)
    try:
        central += harvest_ctuil_month(y, m)
    except Exception as e:
        print("CTUIL err:", e)

    # unique + sort
    seen = set()
    out = []
    for it in central:
        k = (it.get("date",""), it.get("title",""), it.get("url",""))
        if k in seen:
            continue
        seen.add(k)
        out.append(it)
    out.sort(key=lambda x: x.get("date",""), reverse=True)

    write_month_snapshot(y, m, {"central": out, "states": [], "uts": []})
    print(f"Published snapshot for {y}-{m:02d} with {len(out)} items")

if __name__ == "__main__":
    main()
