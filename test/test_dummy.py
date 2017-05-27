import pytest, sys, os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../")
from unittest import TestCase


class TestDummy(TestCase):
    def test_dummy(self):
        pass