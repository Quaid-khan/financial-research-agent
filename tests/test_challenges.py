"""Unit tests verifying all 8 end-to-end benchmark challenges (Phase 7)."""

import pytest

from eval.challenges import (
    run_challenge_01,
    run_challenge_02,
    run_challenge_03,
    run_challenge_04,
    run_challenge_05,
    run_challenge_06,
    run_challenge_07,
    run_challenge_08,
)


def test_challenge_01():
    res = run_challenge_01()
    assert res["passed"] is True


def test_challenge_02():
    res = run_challenge_02()
    assert res["passed"] is True


def test_challenge_03():
    res = run_challenge_03()
    assert res["passed"] is True


def test_challenge_04():
    res = run_challenge_04()
    assert res["passed"] is True


def test_challenge_05():
    res = run_challenge_05()
    assert res["passed"] is True


def test_challenge_06():
    res = run_challenge_06()
    assert res["passed"] is True


def test_challenge_07():
    res = run_challenge_07()
    assert res["passed"] is True


def test_challenge_08():
    res = run_challenge_08()
    assert res["passed"] is True
