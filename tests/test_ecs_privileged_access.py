import pytest

from . import mock_ecs
from  library.aws.ecs import ECSChecker
from library.aws.utility import Account

region = "us-east-1"

task_definitions = {
        "tas_definition1": {
            "family": 'test_ecs_privileged_access1',
            "Description": "ECS task enabled privileged access",
            "CheckShouldPass": False,
            "containerDefinitions": [
                {
                    'name': 'hello_world1',
                    'image': 'docker/hello-world:latest',
                    'cpu': 1024,
                    'memory': 400,
                    'essential': True,
                    'privileged': True
                }
            ]
        },
        "tas_definition2": {
            "family": 'test_ecs_privileged_access2',
            "Description": "ECS task disabled privileged access",
            "CheckShouldPass": True,
            "containerDefinitions": [
                {
                    'name': 'hello_world2',
                    'image': 'docker/hello-world:latest',
                    'cpu': 1024,
                    'memory': 400,
                    'essential': True,
                    'privileged': False
                }
            ]
        }
}


def find_task_definition_name(task_definition_details):
    for taskDefinition, props in task_definitions.items():
        if props["family"] == task_definition_details.name:
            return taskDefinition
    return None


def ident_task_definition_test(task_definition_details):
    """
    Used to build identification string for each autogenerated test (for easy recognition of failed tests).

    :param task_definition_details: dict with information about rules from
                        ECSChecker(...)
    :return: identification string with task_definition_name.
    """

    name = find_task_definition_name(task_definition_details)
    descr = task_definitions.get(name, {}).get("Description", "default description")
    return f"params: {name} ({descr})"


def pytest_generate_tests(metafunc):
    """
    Entrypoint for tests (built-in pytest function for dynamic generation of test cases).
    """
    # Launch ECS mocking and env preparation
    mock_ecs.start()
    test_task_definitions = mock_ecs.create_env_task_definitions(task_definitions, region)

    account = Account(region=region)

    # validate ebs volumes in mocked env
    checker = ECSChecker(account)
    checker.check(ids=test_task_definitions)

    # create test cases for each response
    metafunc.parametrize("task_definition_details", checker.task_definitions, ids=ident_task_definition_test)


@pytest.mark.ecs_privileged_access
def test_task(task_definition_details):
    """
    Actual testing function.

    :param task_definition_details: dict with information about rules from
                        ECSChecker(...)
    :return: nothing, raises AssertionError if actual test result is not matched with expected
    """
    name = find_task_definition_name(task_definition_details)
    expected = task_definitions.get(name, {})["CheckShouldPass"]
    assert expected == task_definition_details.is_privileged