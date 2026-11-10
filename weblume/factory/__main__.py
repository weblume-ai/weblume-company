"""python -m weblume.factory "اعمل موقع لمطعم …" [folder of the client's photos]
   python -m weblume.factory approve <site folder name>     (the owner liked it: the model learns from it)"""
import json
import sys
from pathlib import Path

from . import approve, build

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    if sys.argv[1] == "approve" and len(sys.argv) > 2:
        print("saved as an example:", approve(sys.argv[2]))
        sys.exit()
    res = build(sys.argv[1], Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    print(json.dumps({k: v for k, v in res.items() if k != "shots"}, ensure_ascii=False, indent=1))
