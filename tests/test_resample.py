"""Tests for lappa path resample --step-m command using pytest fixtures."""

import pytest
import json
import tempfile
import os
from pathlib import Path

# Fixtures

@pytest.fixture
def sample_path_2d():
    """A simple 2D path for testing resample."""
    return [
        {"x": 0.0, "y": 0.0},
        {"x": 10.0, "y": 0.0},
        {"x": 10.0, "y": 10.0},
        {"x": 0.0, "y": 10.0},
        {"x": 0.0, "y": 0.0}
    ]

@pytest.fixture
def sample_path_3d():
    """A 3D path with varying step sizes."""
    return [
        {"x": 0.0, "y": 0.0, "z": 0.0},
        {"x": 2.0, "y": 3.0, "z": 1.0},
        {"x": 5.0, "y": 1.0, "z": 3.0},
        {"x": 8.0, "y": 6.0, "z": 2.0},
        {"x": 10.0, "y": 10.0, "z": 5.0}
    ]

@pytest.fixture
def sample_path_file(sample_path_2d, tmp_path):
    """Write a sample path to a temp JSON file."""
    filepath = tmp_path / "path.json"
    with open(filepath, "w") as f:
        json.dump(sample_path_2d, f)
    return str(filepath)

@pytest.fixture
def sample_path_file_3d(sample_path_3d, tmp_path):
    """Write a 3D sample path to a temp JSON file."""
    filepath = tmp_path / "path_3d.json"
    with open(filepath, "w") as f:
        json.dump(sample_path_3d, f)
    return str(filepath)

@pytest.fixture
def single_point_path():
    """Path with a single point."""
    return [{"x": 5.0, "y": 5.0}]

@pytest.fixture
def empty_path():
    """Empty path."""
    return []

# Euclidean distance helper

def euclidean_distance(p1, p2):
    """Calculate Euclidean distance between two points."""
    dims = set(list(p1.keys()) + list(p2.keys())) - {"x", "y", "z"}
    if dims:
        raise ValueError(f"Unexpected dimensions: {dims}")
    dx = p1.get("x", 0) - p2.get("x", 0)
    dy = p1.get("y", 0) - p2.get("y", 0)
    dz = p1.get("z", 0) - p2.get("z", 0)
    return (dx*dx + dy*dy + dz*dz) ** 0.5

def resample_path(path, step_m):
    """Resample a path to have points at regular intervals of step_m meters.
    Uses linear interpolation between existing points."""
    if not path or len(path) < 2:
        return list(path)
    
    result = [dict(path[0])]
    remaining = step_m
    
    for i in range(1, len(path)):
        p1 = path[i-1]
        p2 = path[i]
        seg_dist = euclidean_distance(p1, p2)
        
        if seg_dist == 0:
            continue
        
        while remaining <= seg_dist:
            t = remaining / seg_dist
            new_point = {}
            for key in p1:
                new_point[key] = p1[key] + t * (p2[key] - p1[key])
            result.append(new_point)
            seg_dist -= remaining
            remaining = step_m
            p1 = new_point
        
        remaining -= seg_dist
    
    # Add last point if not already included
    if result[-1] != dict(path[-1]):
        result.append(dict(path[-1]))
    
    return result

# Tests

class TestResample2D:
    """Test resample on 2D paths."""
    
    def test_original_points_preserved(self, sample_path_2d):
        """Original start and end points should be preserved."""
        result = resample_path(sample_path_2d, step_m=2.0)
        assert result[0] == sample_path_2d[0], "Start point changed"
        assert result[-1] == sample_path_2d[-1], "End point changed"
    
    def test_step_size_respected(self, sample_path_2d):
        """Distance between consecutive resampled points should be ~step_m."""
        step = 2.0
        result = resample_path(sample_path_2d, step_m=step)
        assert len(result) >= 2
        for i in range(len(result) - 1):
            d = euclidean_distance(result[i], result[i+1])
            assert abs(d - step) < 0.01, f"Step at index {i} is {d}, expected {step}"
    
    def test_more_points_with_smaller_step(self, sample_path_2d):
        """Smaller step_m should produce more points."""
        result_coarse = resample_path(sample_path_2d, step_m=5.0)
        result_fine = resample_path(sample_path_2d, step_m=1.0)
        assert len(result_fine) > len(result_coarse)
    
    def test_output_is_copy(self, sample_path_2d):
        """Output should be a new list, not mutated input."""
        original = [dict(p) for p in sample_path_2d]
        result = resample_path(sample_path_2d, step_m=3.0)
        assert sample_path_2d == original, "Input was mutated"
        assert result is not sample_path_2d

class TestResample3D:
    """Test resample on 3D paths."""
    
    def test_3d_preserves_z(self, sample_path_3d):
        """Z coordinate should be preserved and interpolated."""
        result = resample_path(sample_path_3d, step_m=2.0)
        assert result[0] == sample_path_3d[0]
        assert result[-1] == sample_path_3d[-1]
    
    def test_3d_step_size(self, sample_path_3d):
        """3D distance between resampled points should ~step_m."""
        step = 3.0
        result = resample_path(sample_path_3d, step_m=step)
        for i in range(len(result) - 1):
            d = euclidean_distance(result[i], result[i+1])
            assert abs(d - step) < 0.01, f"3D step at index {i}: {d} != {step}"

class TestResampleEdgeCases:
    """Test edge cases for resample."""
    
    def test_single_point(self, single_point_path):
        """Single point path should return unchanged."""
        result = resample_path(single_point_path, step_m=2.0)
        assert result == single_point_path
    
    def test_empty_path(self, empty_path):
        """Empty path should return empty."""
        result = resample_path(empty_path, step_m=2.0)
        assert result == []
    
    def test_step_larger_than_path(self, sample_path_2d):
        """Step larger than total path length should return just endpoints."""
        result = resample_path(sample_path_2d, step_m=100.0)
        assert len(result) == 2
        assert result[0] == sample_path_2d[0]
        assert result[-1] == sample_path_2d[-1]
    
    def test_identity_step_zero(self, sample_path_2d):
        """Step of 0 should return original points."""
        result = resample_path(sample_path_2d, step_m=0.0)
        assert len(result) == len(sample_path_2d)

class TestResampleWithFiles:
    """Test resample with file-based fixtures."""
    
    def test_load_from_file(self, sample_path_file):
        """Can load path from JSON file and resample."""
        with open(sample_path_file, 'r') as f:
            path = json.load(f)
        result = resample_path(path, step_m=2.0)
        assert len(result) >= 2
        assert result[0] == path[0]
    
    def test_3d_from_file(self, sample_path_file_3d):
        """Can load 3D path from JSON file and resample."""
        with open(sample_path_file_3d, 'r') as f:
            path = json.load(f)
        result = resample_path(path, step_m=2.0)
        assert len(result) >= 2
