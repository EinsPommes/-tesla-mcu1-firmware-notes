import sys
import sqfs_patch  # noqa: F401
from PySquashfsImage import SquashFsImage

path = sys.argv[1]
wants = sys.argv[2:]
img = SquashFsImage.from_file(path)

def P(n):
    return n.path.decode("utf8", "replace") if isinstance(n.path, bytes) else n.path

bynode = {P(n): n for n in img.root.riter()}
for w in wants:
    n = bynode.get(w)
    print(f"\n========== {w} ==========")
    if n is None:
        print("  (not found)")
        continue
    if n.is_symlink:
        tgt = n.readlink()
        print("  symlink ->", tgt.decode() if isinstance(tgt, bytes) else tgt)
        continue
    if not n.is_file:
        print("  (not a regular file)")
        continue
    try:
        data = n.read_bytes()
        txt = data[:2000].decode("utf8", "replace")
        print(txt)
    except Exception as e:
        print("  (err)", e)
img.close()
