import sys
import sqfs_patch  # noqa: F401  (patches LZ4 to raw block format)
from PySquashfsImage import SquashFsImage

path = sys.argv[1]
img = SquashFsImage.from_file(path)

files = []
dirs = 0
total = 0
tops = {}

for node in img.root.riter():
    if node.is_dir:
        dirs += 1
        continue
    try:
        size = node.size
    except Exception:
        size = 0
    p = node.path
    if isinstance(p, bytes):
        p = p.decode("utf8", "replace")
    files.append((size, p, node.is_symlink))
    total += size

print(f"TOTAL files={len(files)} dirs={dirs} bytes={total:,}")

print("\n=== Top-level entries ===")
for c in img.root.iterdir():
    nm = c.name.decode("utf8", "replace") if isinstance(c.name, bytes) else c.name
    print(("DIR  " if c.is_dir else "FILE ") + nm)

print("\n=== Top 50 largest files ===")
for size, p, link in sorted(files, reverse=True)[:50]:
    print(f"{size:>12,}  {p}")

img.close()
