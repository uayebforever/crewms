#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `crewms.training` package."""

import pytest

import crewms

from crewms.training import *


def test_training_skills_link():

    t1 = Task()
    t2 = Task()

    assert len(t1.skills) == 0

    s1 = Skill()
    s2 = Skill()
    s3 = Skill()

    t1.skills.append(s1)
    t1.skills.append(s2)

    t2.skills.append(s2)
    t2.skills.append(s3)

    assert s1 in t1.skills
    assert s2 in t1.skills

    assert t1 in s1.tasks

    assert s2 in t2.skills
    assert s3 in t2.skills
    assert s1 not in t2.skills
