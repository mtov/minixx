import pytest

from src.scheduler import build_stages


def test_independent_tasks_share_a_stage_in_input_order():
    tasks = [
        {"name": "lint", "deps": []},
        {"name": "test", "deps": []},
        {"name": "deploy", "deps": ["test"]},
    ]
    assert build_stages(tasks) == [["lint", "test"], ["deploy"]]


def test_dependencies_must_be_in_earlier_stages():
    tasks = [
        {"name": "deploy", "deps": ["test", "package"]},
        {"name": "package", "deps": ["build"]},
        {"name": "build", "deps": []},
        {"name": "test", "deps": ["build"]},
    ]
    assert build_stages(tasks) == [["build"], ["package", "test"], ["deploy"]]


def test_each_task_appears_exactly_once():
    tasks = [
        {"name": "build", "deps": []},
        {"name": "test", "deps": ["build"]},
        {"name": "deploy", "deps": ["test"]},
    ]
    stages = build_stages(tasks)
    flattened = [task for stage in stages for task in stage]

    assert stages == [["build"], ["test"], ["deploy"]]
    assert flattened == ["build", "test", "deploy"]


def test_missing_dependency_raises_key_error():
    tasks = [
        {"name": "deploy", "deps": ["build"]},
    ]
    with pytest.raises(KeyError):
        build_stages(tasks)


def test_missing_dependency_is_not_reported_as_cycle():
    tasks = [
        {"name": "lint", "deps": []},
        {"name": "deploy", "deps": ["build"]},
    ]
    with pytest.raises(KeyError):
        build_stages(tasks)


def test_cycle_raises_value_error():
    tasks = [
        {"name": "build", "deps": ["test"]},
        {"name": "test", "deps": ["build"]},
    ]
    with pytest.raises(ValueError):
        build_stages(tasks)
