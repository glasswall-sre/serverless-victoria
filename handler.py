import json
import logging
import logging.handlers
import os
from contextlib import redirect_stdout
from http import HTTPStatus
from io import StringIO
from pathlib import Path
from typing import List

from victoria import config
from victoria.script import victoria

PROJECT_PATH = Path(os.path.abspath(os.path.dirname(__file__)))
CONFIG_PATH = PROJECT_PATH / "victoria.yaml"
LOGS_DIR = PROJECT_PATH / 'logs'
LOG_FILE = LOGS_DIR / 'app.log'

# whether or not exception info should be included in the logs
EXC_INFO = True


def setup_logger():
    os.makedirs(LOGS_DIR, exist_ok=True)

    logger = logging.getLogger('handler')
    logger.setLevel(logging.DEBUG)

    file_handle = logging.handlers.RotatingFileHandler(LOG_FILE)
    file_handle.setLevel(logging.DEBUG)
    file_handle.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

    logger.addHandler(file_handle)
    return logger


def run_victoria(args: List[str]):
    """
    Loads local config file and invokes Victoria module through
    CLI capabilities with supplied arguments `args` and config.
    Args:
        args: List[str] arguments passed to Victoria.
    Returns:
        See :func:`handler` function below
    """
    cfg = config.load(CONFIG_PATH)
    victoria.cli.main(prog_name="victoria", args=args, obj=cfg)


def read_output_val(f: StringIO) -> str:
    """
    Retrieves the content of StringIO object without trailing whitespace.
    Args:
        f: StringIO object
    Returns:
        String content of `f` StringIO object with trailing whitespace removed.
    """
    return f.getvalue().rstrip()


def handler(event, context):
    """
    Lambda function handler.
    Executes Victoria and returns an appropriate HTTP response dict.
    Reads Victoria's standard output stream for gathering text output of execution.

    It assumes that Victoria performs sys.exit(...) upon execution, which results in SystemExit exception
    with the code 0 designating success of operation and others standing for errors.
    It returns BAD_REQUEST when this assumption is not met.

    It returns INTERNAL_SERVER_ERROR status code when Victoria responded with the code other than 0
    or when an exception other than SystemExit has been thrown during execution.

    It provides a "message" field in HTTP response for failures of execution, which is built from
    standard output stream or an exception details, if any.

    Args:
        event: Lambda-handler event data.
        context: Lambda-handler runtime information (context object).
    Returns:
        A dict with status code and body or error details.
    """

    app_logger = setup_logger()

    try:
        body = json.loads(event['body'])
    except (KeyError, ValueError) as e:
        app_logger.exception("Invalid request.", exc_info=EXC_INFO)
        return {'statusCode': HTTPStatus.BAD_REQUEST,
                'error': 'Invalid request',
                'message': str(e)}

    f = StringIO()
    try:
        with redirect_stdout(f):
            run_victoria(body['args'])
    except SystemExit as e:
        output = read_output_val(f)

        if e.code == 0:
            app_logger.info("Victoria completed successfully.")
            return {'statusCode': HTTPStatus.OK,
                    'body': json.dumps(output)}
        else:
            app_logger.error(msg='Command failed: non-zero status code %s.' % e.code)
            return {'statusCode': HTTPStatus.INTERNAL_SERVER_ERROR,
                    'error': 'Command failed: non-zero status code',
                    'message': output}
    except Exception as e:
        app_logger.exception("Uncaught Victoria exception detected.", exc_info=EXC_INFO)
        return {'statusCode': HTTPStatus.INTERNAL_SERVER_ERROR,
                'error': 'Command failed: uncaught Victoria exception detected',
                'message': str(e)}

    # For completeness: in case Victoria didn't exit with sys.exit(...) and didn't throw any exceptions
    app_logger.error("Victoria didn't exit with sys.exit(...) and didn't throw any exceptions.")
    return {'statusCode': HTTPStatus.BAD_REQUEST,
            'error': 'Invalid request',
            'message': ''}
