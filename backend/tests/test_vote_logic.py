import pytest
from app.services.vote_service import VoteService

def test_compute_effective_color_less_than_10_votes():
    # Original color is blue
    vote_counts = {"red": 5, "blue": 2, "green": 1} # Total 8 votes
    result = VoteService.compute_effective_color(vote_counts, "blue")
    assert result == "blue"

def test_compute_effective_color_exactly_10_votes_majority_wins():
    # Original color is blue
    vote_counts = {"red": 6, "blue": 3, "green": 1} # Total 10 votes
    result = VoteService.compute_effective_color(vote_counts, "blue")
    assert result == "red"

def test_compute_effective_color_more_than_10_votes_majority_wins():
    # Original color is blue
    vote_counts = {"red": 5, "blue": 2, "green": 8} # Total 15 votes
    result = VoteService.compute_effective_color(vote_counts, "blue")
    assert result == "green"

def test_compute_effective_color_tie_at_10_votes():
    # This behavior depends on how `max` handles ties (it picks the first one in the dict keys order)
    # But it should definitely not be the original unless it's part of the tie and picked first.
    vote_counts = {"red": 5, "blue": 5, "green": 0} # Total 10 votes
    result = VoteService.compute_effective_color(vote_counts, "green")
    assert result in ["red", "blue"]

def test_compute_effective_color_no_votes():
    vote_counts = {"red": 0, "blue": 0, "green": 0}
    result = VoteService.compute_effective_color(vote_counts, "red")
    assert result == "red"
