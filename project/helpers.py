"""App helper functions
"""
import random


def get_picks():
    avail_picks = ["TW", "PM", "DJ", "AS"]
    return avail_picks


def get_event():
    return "Test Open"


def get_earnings():
    return 100 * random.random()
