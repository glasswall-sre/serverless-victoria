import json
from http import HTTPStatus

import boto3
import pytest


# fixtures for tests
@pytest.fixture()
def region_name():
    return 'eu-west-2'


@pytest.fixture()
def lambda_name():
    return 'serverless-victoria-service-prod-hello'


@pytest.fixture()
def account_id():
    return '433250546572'


@pytest.fixture()
def fn_name(region_name, lambda_name, account_id):
    return "arn:aws:lambda:{region}:{account_id}:function:{name}".format(
        region=region_name, account_id=account_id, name=lambda_name)


@pytest.fixture()
def lambda_client(region_name):
    return boto3.client('lambda', region_name=region_name)


@pytest.fixture
def payload(request):
    return json.dumps({'body': json.dumps({'args': request.param})
                       }) if request.param else ""


@pytest.fixture()
def lambda_client_json_response(payload, lambda_client, fn_name):
    try:
        r = lambda_client.invoke(FunctionName=fn_name,
                                 InvocationType='RequestResponse',
                                 Payload=payload)

        resp_data = r['Payload'].read()
        return json.loads(resp_data)
    except Exception:
        return False


@pytest.mark.parametrize('payload', [['config', 'path']], indirect=True)
def test_correct_arguments_for_victoria(lambda_client_json_response, payload):

    # verify the response
    assert type(
        lambda_client_json_response) == dict, "Incorrect response received."

    assert 'statusCode' in lambda_client_json_response, "Response should contain `statusCode` field."
    assert 'body' in lambda_client_json_response, "Response should contain `body` field."

    assert lambda_client_json_response['statusCode'] == HTTPStatus.OK
    assert lambda_client_json_response['body'].endswith('victoria.yaml"')


@pytest.mark.parametrize('payload', [['store', 'unknownstore', 'ls', 'ls']],
                         indirect=True)
def test_uncaught_victoria_exceptions(lambda_client_json_response, payload):
    assert type(
        lambda_client_json_response) == dict, "Incorrect response received."

    assert 'statusCode' in lambda_client_json_response, "Response should contain `statusCode` field."
    assert 'error' in lambda_client_json_response, "Response should contain `error` field."

    assert lambda_client_json_response[
        'statusCode'] == HTTPStatus.INTERNAL_SERVER_ERROR
    assert lambda_client_json_response[
        'error'] == "Command failed: uncaught Victoria exception detected"


@pytest.mark.parametrize('payload', [['store', 'wrong', 'command']],
                         indirect=True)
def test_handled_victoria_errors(lambda_client_json_response, payload):
    assert type(
        lambda_client_json_response) == dict, "Incorrect response received."

    assert 'statusCode' in lambda_client_json_response, "Response should contain `statusCode` field."
    assert 'error' in lambda_client_json_response, "Response should contain `error` field."

    assert lambda_client_json_response[
        'statusCode'] == HTTPStatus.INTERNAL_SERVER_ERROR
    assert lambda_client_json_response[
        'error'] == 'Command failed: non-zero status code'


@pytest.mark.parametrize('payload', [None], indirect=True)
def test_broken_request(lambda_client_json_response, payload):
    assert type(
        lambda_client_json_response) == dict, "Incorrect response received."

    assert 'statusCode' in lambda_client_json_response, "Response should contain `statusCode` field."
    assert 'error' in lambda_client_json_response, "Response should contain `error` field."

    assert lambda_client_json_response['statusCode'] == HTTPStatus.BAD_REQUEST
    assert lambda_client_json_response['error'] == 'Invalid request'
