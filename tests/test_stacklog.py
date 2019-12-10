#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `stacklog` package."""

from __future__ import print_function

import logging

import pytest

from stacklog import stacklog


def test_logs_success(caplog):
    """On normal resolution, stack with DONE is logged"""
    msg = 'Running'

    with stacklog(logging.critical, msg):
        pass

    expected = ['Running...', 'Running...DONE']
    actual = caplog.messages
    assert actual == expected


def test_logs_failure(caplog):
    """On error, stack with FAILURE is logged"""
    msg = 'Running'
    e = ValueError

    with pytest.raises(e):
        with stacklog(logging.critical, msg):
            raise e

    expected = ['Running...', 'Running...FAILURE']
    actual = caplog.messages
    assert actual == expected


def test_logs_custom_condition(caplog):
    """On custom error, stack with SKIPPED (e.g.) is logged"""
    msg = 'Running'
    e = NotImplementedError
    condition = (e, 'SKIPPED')

    with pytest.raises(e):
        with stacklog(logging.critical, msg, conditions=[condition]):
            raise e

    expected = ['Running...', 'Running...SKIPPED']
    actual = caplog.messages
    assert actual == expected


def test_decorator(caplog):
    msg = 'Running'

    @stacklog(logging.critical, msg)
    def run():
        pass

    run()

    expected = ['Running...', 'Running...DONE']
    actual = caplog.messages
    assert actual == expected
