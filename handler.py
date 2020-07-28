from contextlib import redirect_stdout
import json
from io import StringIO
from typing import List

from victoria.script import victoria
from victoria import config


def run_victoria(args: List[str]):
    cfg = config.load("victoria.yaml")
    victoria.cli.main(prog_name="victoria", args=args, obj=cfg)


def handler(event, context):
    body = json.loads(event['body'])

    f = StringIO()
    try:
        with redirect_stdout(f):
            run_victoria(body['args'])
    except SystemExit:
        pass

    response = {"statusCode": 200, "body": json.dumps(f.getvalue())}

    return response
