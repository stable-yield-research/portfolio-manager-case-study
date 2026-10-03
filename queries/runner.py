"""
Run query blocks.

  python queries/runner.py                  # all blocks
  python queries/runner.py block1_example   # one block
  python queries/runner.py --list
"""

import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import project_config as cfg  # noqa: E402


def main(argv):
    if "--list" in argv:
        for name, script in cfg.QUERY_BLOCKS.items():
            print(f"{name:30s} queries/{script}")
        return 0
    names = [a for a in argv if not a.startswith("--")] or list(cfg.QUERY_BLOCKS)
    unknown = [n for n in names if n not in cfg.QUERY_BLOCKS]
    if unknown:
        print(f"Unknown block(s): {unknown}. Use --list.")
        return 2

    failed = []
    for name in names:
        t0 = time.time()
        print(f"\n=== {name} ===", flush=True)
        rc = subprocess.call([sys.executable, "-u", str(HERE / cfg.QUERY_BLOCKS[name])], cwd=str(HERE))
        print(f"=== {name}: {'ok' if rc == 0 else 'FAILED'} in {time.time() - t0:.0f}s ===", flush=True)
        if rc != 0:
            failed.append(name)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
