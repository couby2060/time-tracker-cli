# Test Suite for Time Tracker (tt.py)

## Overview

This test suite provides comprehensive coverage for the `tt.py` time tracker application. It includes 78 tests organized into 11 test classes, covering all major functionality.

## Installation

Install the test dependencies:

```bash
pip install -r requirements-dev.txt
```

Or install individually:

```bash
pip install pytest pytest-cov pytest-mock
```

## Running Tests

### Basic Test Run

```bash
pytest test_tt.py -v
```

### With Coverage Report

```bash
pytest test_tt.py -v --cov=tt --cov-report=html
```

Then open `htmlcov/index.html` in your browser to view detailed coverage.

### Quick Coverage Summary

```bash
pytest test_tt.py --cov=tt --cov-report=term
```

### Run Specific Test Class

```bash
pytest test_tt.py::TestDataManagement -v
```

### Run Specific Test

```bash
pytest test_tt.py::TestDataManagement::test_round_seconds_to_15min_one_minute -v
```

## Test Coverage

The test suite covers:

### 1. Data Management (17 tests)
- ✅ JSON file loading (valid, invalid, non-existent files)
- ✅ JSON file saving
- ✅ Duration formatting (hours, minutes)
- ✅ Time rounding to 15-minute blocks
- ✅ Clipboard operations (success and error cases)

### 2. Timer Logic (4 tests)
- ✅ Starting and stopping timers
- ✅ Time rounding for billing
- ✅ Handling negative duration (clock changes)
- ✅ No active timer scenarios

### 3. Interactive Menu (8 tests)
- ✅ List selection by number
- ✅ List selection by text input
- ✅ Empty list handling
- ✅ Invalid input handling
- ✅ Keyboard interrupt (Ctrl+C)

### 4. Customer & Project Selection (8 tests)
- ✅ Interactive mode
- ✅ Partial arguments
- ✅ Full arguments with notes
- ✅ ID-based selection
- ✅ Name-based selection

### 5. Start Command (5 tests)
- ✅ Basic start
- ✅ Start with notes
- ✅ Auto-stopping existing timer
- ✅ Shortcut usage (@shortcut, -s shortcut)
- ✅ Invalid shortcut handling

### 6. Note Command (3 tests)
- ✅ Adding notes to running timer
- ✅ No timer running error
- ✅ Empty note validation

### 7. Stop Command (2 tests)
- ✅ Successfully stopping timer
- ✅ No timer running scenario

### 8. Report Command (4 tests)
- ✅ Empty report
- ✅ Report with historical entries
- ✅ Report including current running timer
- ✅ Copy to clipboard mode

### 9. Shortcut Management (8 tests)
- ✅ List shortcuts (empty and populated)
- ✅ Add new shortcuts
- ✅ Delete shortcuts
- ✅ Validation and error handling
- ✅ Shell completion support (--complete flag)
- ✅ FZF integration (pick command)

### 10. Add Customer/Project (3 tests)
- ✅ Adding new customers
- ✅ Adding projects to existing customers
- ✅ Input validation

### 11. Reset & Help (4 tests)
- ✅ Reset with confirmation
- ✅ Reset cancellation
- ✅ Help command output

### 12. Main Entry Point (12 tests)
- ✅ All command routing
- ✅ Default behavior
- ✅ Shortcut syntax
- ✅ All command-line flags

## Test Structure

Each test class is organized around a specific component:

```python
class TestDataManagement:
    """Tests for utility functions"""
    
class TestTimerLogic:
    """Tests for timer start/stop logic"""
    
class TestCmdStart:
    """Tests for the start command"""
    
# ... and so on
```

## What the Tests Protect Against

These tests ensure that future changes don't break:

1. **Time Calculation**: 15-minute rounding, duration formatting
2. **Data Persistence**: JSON loading/saving, file handling
3. **User Input**: Interactive menus, argument parsing
4. **Edge Cases**: Empty lists, negative durations, missing files
5. **Command Flow**: All CLI commands and their options
6. **Integration**: Shortcuts, notes, multi-timer handling

## Continuous Integration

You can integrate these tests into CI/CD pipelines:

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements-dev.txt
      - name: Run tests
        run: |
          pytest test_tt.py -v --cov=tt
```

## Mocking Strategy

The tests use mocking to avoid side effects:

- **File I/O**: Mocked with `tmp_path` fixtures and `mock_open`
- **Time**: Mocked with `@patch('time.time')`
- **User Input**: Mocked with `@patch('builtins.input')`
- **System Calls**: Mocked with `@patch('subprocess.Popen')`

This ensures tests run fast and don't modify your actual data files.

## Adding New Tests

When adding new features to `tt.py`, follow this pattern:

```python
class TestNewFeature:
    """Test description."""
    
    @patch('tt.some_dependency')
    def test_feature_basic_case(self, mock_dep, capsys):
        """Test basic functionality."""
        # Arrange
        mock_dep.return_value = expected_value
        
        # Act
        result = tt.new_feature()
        
        # Assert
        assert result == expected_result
        captured = capsys.readouterr()
        assert "Expected output" in captured.out
```

## Troubleshooting

### Tests fail with "ModuleNotFoundError"
```bash
# Make sure you're in the project directory
cd "/Users/johanneswilhelm/Documents/PY Projects/2025-tt"

# Ensure tt.py is importable
python3 -c "import tt"
```

### Tests fail with import errors
```bash
# Reinstall dependencies
pip install -r requirements-dev.txt --force-reinstall
```

### Coverage reports not generating
```bash
# Install coverage separately
pip install coverage pytest-cov
```

## Benefits

With this test suite, you can:

1. ✅ **Refactor confidently** - Tests catch regressions
2. ✅ **Document behavior** - Tests show how functions should work
3. ✅ **Catch bugs early** - Run tests before committing
4. ✅ **Validate fixes** - Add tests for bug reports
5. ✅ **Maintain quality** - Ensure code quality over time

---

**Total Tests**: 78  
**Test Classes**: 11  
**Last Updated**: 2025-11-22

