import json
import unittest
from http import HTTPStatus
from typing import Union

import victoria

import handler as h


class TestLambdaHandler(unittest.TestCase):

    @staticmethod
    def api_gateway_event_stub(payload: dict) -> dict:
        return dict(body=json.dumps(payload))

    @staticmethod
    def invoke_lambda_handler(event_args: Union[dict, None]) -> dict:
        event = TestLambdaHandler.api_gateway_event_stub(event_args) if event_args else dict()
        return h.handler(event=event, context={})

    def test_broken_requests(self):
        # Tests that lambda handler correctly processes invalid lambda requests
        # returning HTTPStatus.BAD_REQUEST status code.

        response = self.invoke_lambda_handler(event_args=None)
        self.assertEqual(response['statusCode'], HTTPStatus.BAD_REQUEST)
        self.assertEqual(response['error'], 'Invalid request')

    def test_correct_arguments_for_victoria(self):
        # Tests that Victoria invoked with correct arguments leads to HTTPStatus.OK response dict.

        config_loc = victoria.config.get_config_loc()
        response = self.invoke_lambda_handler({'args': ['config', 'path']})

        self.assertEqual(response, {'statusCode': HTTPStatus.OK,
                                    'body': json.dumps(config_loc)})

    def test_uncaught_victoria_exceptions(self):
        # This case is not handled in Victoria actually: it causes an uncaught ValueError exception.
        # Lambda handler should deal with such corner cases for completeness.

        response = self.invoke_lambda_handler({'args': ['store', 'unknownstore', 'ls', 'ls']})
        self.assertEqual(response['statusCode'], HTTPStatus.INTERNAL_SERVER_ERROR)
        self.assertEqual(response['error'], "Command failed: uncaught Victoria exception detected")

    def test_handled_victoria_errors(self):
        # Tests that Victoria-detected errors result in HTTP.INTERNAL_SERVER_ERROR response in the lambda handler.

        response = self.invoke_lambda_handler({'args': ['store', 'wrong', 'command']})
        self.assertEqual(response['statusCode'], HTTPStatus.INTERNAL_SERVER_ERROR)
        self.assertEqual(response['error'], 'Command failed: non-zero status code')


if __name__ == '__main__':
    unittest.main()
