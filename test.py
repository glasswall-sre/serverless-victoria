from contextlib import redirect_stdout
import json
from io import StringIO
import sys
from typing import ContextManager, List

from victoria.script import victoria
from victoria import config


def run_victoria(args: List[str]):
    cfg = config.load("victoria.yaml")
    victoria.cli.main(prog_name="victoria", args=args, obj=cfg)


if __name__ == "__main__":
    f = StringIO()
    try:
        with redirect_stdout(f):
            run_victoria(["config", "view"])
    except SystemExit:
        pass
    print(f.getvalue())