import sys, os
import sqfs_patch  # noqa: F401
from PySquashfsImage import SquashFsImage

path = sys.argv[1]
outdir = sys.argv[2]
wants = sys.argv[3:]
os.makedirs(outdir, exist_ok=True)
img = SquashFsImage.from_file(path)

def P(n):
    return n.path.decode("utf8", "replace") if isinstance(n.path, bytes) else n.path

bynode = {P(n): n for n in img.root.riter()}
for w in wants:
    n = bynode.get(w)
    if n is None or not n.is_file:
        print("SKIP", w, "(not a regular file)")
        continue
    data = n.read_bytes()
    out = os.path.join(outdir, os.path.basename(w))
    with open(out, "wb") as f:
        f.write(data)
    print(f"WROTE {out}  {len(data):,} bytes")
img.close()
