#!/usr/bin/env python3
"""
Comprehensive test suite for tt.py time tracker application.
Run with: pytest test_tt.py -v
"""

import pytest
import json
import time
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open, call
import tempfile

# Import the module to test
import tt


class TestDataManagement:
    """Test data loading, saving, and utility functions."""
    
    def test_load_json_file_not_exists(self):
        """Test loading JSON when file doesn't exist."""
        non_existent = Path("/tmp/nonexistent_file_test_12345.json")
        result = tt.load_json(non_existent, {"default": "value"})
        assert result == {"default": "value"}
    
    def test_load_json_valid_file(self, tmp_path):
        """Test loading valid JSON file."""
        test_file = tmp_path / "test.json"
        test_data = {"test": "data", "number": 42}
        test_file.write_text(json.dumps(test_data))
        
        result = tt.load_json(test_file, {})
        assert result == test_data
    
    def test_load_json_invalid_json(self, tmp_path, capsys):
        """Test loading invalid JSON returns default."""
        test_file = tmp_path / "invalid.json"
        test_file.write_text("{ invalid json }")
        
        result = tt.load_json(test_file, {"default": "fallback"})
        assert result == {"default": "fallback"}
        
        captured = capsys.readouterr()
        assert "Warning" in captured.out
    
    def test_save_json(self, tmp_path):
        """Test saving JSON to file."""
        test_file = tmp_path / "save_test.json"
        test_data = {"saved": True, "count": 3}
        
        tt.save_json(test_file, test_data)
        
        # Read back and verify
        with open(test_file) as f:
            loaded = json.load(f)
        assert loaded == test_data
    
    def test_get_formatted_duration_zero(self):
        """Test duration formatting with zero seconds."""
        h, m = tt.get_formatted_duration(0)
        assert h == 0
        assert m == 0
    
    def test_get_formatted_duration_minutes(self):
        """Test duration formatting with only minutes."""
        h, m = tt.get_formatted_duration(300)  # 5 minutes
        assert h == 0
        assert m == 5
    
    def test_get_formatted_duration_hours_and_minutes(self):
        """Test duration formatting with hours and minutes."""
        h, m = tt.get_formatted_duration(4500)  # 1h 15m
        assert h == 1
        assert m == 15
    
    def test_get_formatted_duration_multiple_hours(self):
        """Test duration formatting with multiple hours."""
        h, m = tt.get_formatted_duration(7200)  # 2h
        assert h == 2
        assert m == 0
    
    def test_round_seconds_to_15min_zero(self):
        """Test rounding zero or negative seconds."""
        assert tt.round_seconds_to_15min(0) == 0
        assert tt.round_seconds_to_15min(-100) == 0
    
    def test_round_seconds_to_15min_one_minute(self):
        """Test rounding 1 minute to 15 minutes."""
        assert tt.round_seconds_to_15min(60) == 900  # rounds up to 15m
    
    def test_round_seconds_to_15min_exact_15(self):
        """Test exact 15 minute input."""
        assert tt.round_seconds_to_15min(900) == 900  # stays 15m
    
    def test_round_seconds_to_15min_16_minutes(self):
        """Test 16 minutes rounds to 30."""
        assert tt.round_seconds_to_15min(960) == 1800  # rounds to 30m
    
    def test_round_seconds_to_15min_44_minutes(self):
        """Test 44 minutes rounds to 45."""
        assert tt.round_seconds_to_15min(2640) == 2700  # rounds to 45m
    
    def test_round_seconds_to_15min_one_hour(self):
        """Test 1 hour exactly."""
        assert tt.round_seconds_to_15min(3600) == 3600  # stays 1h
    
    @patch('subprocess.Popen')
    def test_copy_to_clipboard_success(self, mock_popen):
        """Test successful clipboard copy."""
        mock_process = Mock()
        mock_process.communicate = Mock()
        mock_popen.return_value = mock_process
        
        tt.copy_to_clipboard("test text")
        
        mock_popen.assert_called_once()
        mock_process.communicate.assert_called_once_with(b'test text')
    
    @patch('subprocess.Popen', side_effect=FileNotFoundError)
    def test_copy_to_clipboard_pbcopy_not_found(self, mock_popen, capsys):
        """Test clipboard copy when pbcopy is not available."""
        tt.copy_to_clipboard("test")
        
        captured = capsys.readouterr()
        assert "not found" in captured.out
    
    @patch('subprocess.Popen', side_effect=Exception("Test error"))
    def test_copy_to_clipboard_general_error(self, mock_popen, capsys):
        """Test clipboard copy with general error."""
        tt.copy_to_clipboard("test")
        
        captured = capsys.readouterr()
        assert "Error copying" in captured.out


class TestTimerLogic:
    """Test timer start/stop logic."""
    
    def test_stop_current_no_timer_running(self, capsys):
        """Test stopping when no timer is running."""
        data = {"current": None, "history": []}
        result = tt.stop_current(data, verbose=True)
        
        assert result is False
        assert data["current"] is None
        assert len(data["history"]) == 0
    
    @patch('time.time')
    def test_stop_current_with_timer(self, mock_time, capsys):
        """Test stopping an active timer."""
        start_time = 1000.0
        end_time = 1900.0  # 900 seconds = 15 minutes
        mock_time.return_value = end_time
        
        data = {
            "current": {
                "customer": "TestCust",
                "project": "TestProj",
                "start_timestamp": start_time,
                "notes": ["Test note"]
            },
            "history": []
        }
        
        result = tt.stop_current(data, verbose=True)
        
        assert result is True
        assert data["current"] is None
        assert len(data["history"]) == 1
        
        entry = data["history"][0]
        assert entry["customer"] == "TestCust"
        assert entry["project"] == "TestProj"
        assert entry["duration_seconds"] == 900  # rounded to 15min
        assert entry["raw_seconds"] == 900
        assert entry["notes"] == ["Test note"]
        assert "start_str" in entry
        assert "end_str" in entry
        
        captured = capsys.readouterr()
        assert "Stopped" in captured.out
    
    @patch('time.time')
    def test_stop_current_rounds_up(self, mock_time):
        """Test that stopping rounds up to nearest 15 min."""
        start_time = 1000.0
        end_time = 1060.0  # 60 seconds = 1 minute
        mock_time.return_value = end_time
        
        data = {
            "current": {
                "customer": "Test",
                "project": "Proj",
                "start_timestamp": start_time,
                "notes": []
            },
            "history": []
        }
        
        tt.stop_current(data, verbose=False)
        
        # 1 minute should round up to 15 minutes
        assert data["history"][0]["duration_seconds"] == 900
        assert data["history"][0]["raw_seconds"] == 60
    
    @patch('time.time')
    def test_stop_current_negative_duration(self, mock_time):
        """Test handling of negative duration (clock change)."""
        start_time = 2000.0
        end_time = 1000.0  # Earlier than start
        mock_time.return_value = end_time
        
        data = {
            "current": {
                "customer": "Test",
                "project": "Proj",
                "start_timestamp": start_time,
                "notes": []
            },
            "history": []
        }
        
        tt.stop_current(data, verbose=False)
        
        # Should handle gracefully with 0 duration
        assert data["history"][0]["duration_seconds"] == 0
        assert data["history"][0]["raw_seconds"] == 0


class TestSelectFromList:
    """Test interactive list selection."""
    
    @patch('builtins.input', return_value='1')
    def test_select_from_list_by_number(self, mock_input, capsys):
        """Test selecting item by number."""
        items = [{"name": "Item1"}, {"name": "Item2"}]
        result = tt.select_from_list(items, "Select")
        
        assert result == {"name": "Item1"}
    
    @patch('builtins.input', return_value='2')
    def test_select_from_list_by_number_second(self, mock_input):
        """Test selecting second item by number."""
        items = ["First", "Second", "Third"]
        result = tt.select_from_list(items, "Select")
        
        assert result == "Second"
    
    @patch('builtins.input', return_value='CustomName')
    def test_select_from_list_by_text(self, mock_input):
        """Test selecting by typing custom text."""
        items = [{"name": "Item1"}]
        result = tt.select_from_list(items, "Select")
        
        assert result == "CustomName"
    
    @patch('builtins.input', return_value='999')
    def test_select_from_list_invalid_number(self, mock_input, capsys):
        """Test selecting with invalid number."""
        items = [{"name": "Item1"}]
        result = tt.select_from_list(items, "Select")
        
        assert result is None
        captured = capsys.readouterr()
        assert "Invalid number" in captured.out
    
    @patch('builtins.input', return_value='')
    def test_select_from_list_empty_input(self, mock_input, capsys):
        """Test empty input."""
        items = [{"name": "Item1"}]
        result = tt.select_from_list(items, "Select")
        
        assert result is None
        captured = capsys.readouterr()
        assert "Invalid input" in captured.out
    
    @patch('builtins.input', return_value='NewItem')
    def test_select_from_list_empty_list(self, mock_input, capsys):
        """Test selecting from empty list with text input."""
        items = []
        result = tt.select_from_list(items, "Select")
        
        assert result == "NewItem"
        captured = capsys.readouterr()
        assert "empty" in captured.out
    
    @patch('builtins.input', return_value='5')
    def test_select_from_list_empty_list_number(self, mock_input, capsys):
        """Test selecting from empty list with number."""
        items = []
        result = tt.select_from_list(items, "Select")
        
        assert result is None
        captured = capsys.readouterr()
        assert "empty" in captured.out
    
    @patch('builtins.input', side_effect=KeyboardInterrupt)
    def test_select_from_list_keyboard_interrupt(self, mock_input):
        """Test handling Ctrl+C."""
        items = [{"name": "Item1"}]
        
        with pytest.raises(SystemExit):
            tt.select_from_list(items, "Select")


class TestGetCustomerAndProject:
    """Test customer and project selection logic."""
    
    @patch('tt.select_from_list')
    def test_interactive_with_dict_customer(self, mock_select):
        """Test interactive selection with dictionary customer."""
        mock_select.side_effect = [
            {"name": "Acme", "projects": ["Proj1", "Proj2"]},
            "Proj1"
        ]
        
        customer, project, note = tt.get_customer_and_project([])
        
        assert customer == "Acme"
        assert project == "Proj1"
        assert note is None
    
    @patch('tt.select_from_list', return_value="NewCustomer")
    @patch('builtins.input', return_value="NewProject")
    def test_interactive_with_string_customer(self, mock_input, mock_select):
        """Test interactive with string customer name."""
        customer, project, note = tt.get_customer_and_project([])
        
        assert customer == "NewCustomer"
        assert project == "NewProject"
        assert note is None
    
    @patch('tt.load_json')
    @patch('tt.select_from_list', return_value="TestProj")
    def test_one_arg_with_customer_id(self, mock_select, mock_load):
        """Test with customer ID as argument."""
        mock_load.return_value = {
            "customers": [
                {"name": "Customer1", "projects": ["Proj1"]},
                {"name": "Customer2", "projects": ["Proj2"]}
            ]
        }
        
        customer, project, note = tt.get_customer_and_project(["1"])
        
        assert customer == "Customer1"
        assert project == "TestProj"
        assert note is None
    
    @patch('tt.load_json')
    def test_one_arg_invalid_customer_id(self, mock_load, capsys):
        """Test with invalid customer ID."""
        mock_load.return_value = {"customers": [{"name": "Cust1", "projects": []}]}
        
        with pytest.raises(SystemExit):
            tt.get_customer_and_project(["999"])
        
        captured = capsys.readouterr()
        assert "not found" in captured.out
    
    @patch('tt.load_json')
    @patch('builtins.input', return_value="TestProject")
    def test_one_arg_with_customer_name(self, mock_input, mock_load):
        """Test with customer name as argument."""
        mock_load.return_value = {"customers": []}
        
        customer, project, note = tt.get_customer_and_project(["MyCustomer"])
        
        assert customer == "MyCustomer"
        assert project == "TestProject"
        assert note is None
    
    @patch('tt.load_json')
    def test_two_args_with_ids(self, mock_load):
        """Test with both customer and project IDs."""
        mock_load.return_value = {
            "customers": [
                {"name": "Cust1", "projects": ["Proj1", "Proj2"]}
            ]
        }
        
        customer, project, note = tt.get_customer_and_project(["1", "2"])
        
        assert customer == "Cust1"
        assert project == "Proj2"
        assert note is None
    
    @patch('tt.load_json')
    def test_args_with_note(self, mock_load):
        """Test with customer, project and note."""
        mock_load.return_value = {
            "customers": [
                {"name": "Cust1", "projects": ["Proj1"]}
            ]
        }
        
        customer, project, note = tt.get_customer_and_project(
            ["1", "1", "This", "is", "a", "note"]
        )
        
        assert customer == "Cust1"
        assert project == "Proj1"
        assert note == "This is a note"
    
    @patch('tt.load_json')
    def test_args_with_names(self, mock_load):
        """Test with customer and project names directly."""
        mock_load.return_value = {"customers": []}
        
        customer, project, note = tt.get_customer_and_project(
            ["MyCustomer", "MyProject"]
        )
        
        assert customer == "MyCustomer"
        assert project == "MyProject"
        assert note is None


class TestCmdStart:
    """Test the start command."""
    
    @patch('tt.load_json')
    @patch('tt.save_json')
    @patch('time.time', return_value=1000.0)
    @patch('tt.get_customer_and_project')
    def test_cmd_start_basic(self, mock_get_cp, mock_time, mock_save, mock_load, capsys):
        """Test basic start command."""
        mock_load.return_value = {"current": None, "history": []}
        mock_get_cp.return_value = ("TestCust", "TestProj", None)
        
        tt.cmd_start([])
        
        # Verify save was called with correct data structure
        save_calls = mock_save.call_args_list
        saved_data = save_calls[0][0][1]
        
        assert saved_data["current"]["customer"] == "TestCust"
        assert saved_data["current"]["project"] == "TestProj"
        assert saved_data["current"]["start_timestamp"] == 1000.0
        
        captured = capsys.readouterr()
        assert "Started" in captured.out
    
    @patch('tt.load_json')
    @patch('tt.save_json')
    @patch('time.time', return_value=2000.0)
    @patch('tt.get_customer_and_project')
    def test_cmd_start_with_note(self, mock_get_cp, mock_time, mock_save, mock_load, capsys):
        """Test start with a note."""
        mock_load.return_value = {"current": None, "history": []}
        mock_get_cp.return_value = ("Cust", "Proj", "My task note")
        
        tt.cmd_start([])
        
        saved_data = mock_save.call_args_list[0][0][1]
        assert saved_data["current"]["notes"] == ["My task note"]
        
        captured = capsys.readouterr()
        assert "My task note" in captured.out
    
    @patch('tt.load_json')
    @patch('tt.save_json')
    @patch('time.time')
    @patch('tt.stop_current')
    @patch('tt.get_customer_and_project')
    def test_cmd_start_stops_existing(self, mock_get_cp, mock_stop, mock_time, 
                                       mock_save, mock_load):
        """Test that starting a new timer stops the current one."""
        mock_load.return_value = {
            "current": {"customer": "Old", "project": "Old", "start_timestamp": 100},
            "history": []
        }
        mock_get_cp.return_value = ("New", "New", None)
        mock_time.return_value = 200.0
        
        tt.cmd_start([])
        
        mock_stop.assert_called_once()
    
    @patch('tt.load_json')
    @patch('tt.save_json')
    @patch('time.time', return_value=1000.0)
    def test_cmd_start_with_shortcut(self, mock_time, mock_save, mock_load, capsys):
        """Test starting with a shortcut."""
        mock_load.side_effect = [
            {"current": None, "history": []},  # DATA_FILE
            {  # CONFIG_FILE
                "customers": [],
                "shortcuts": {
                    "daily": {
                        "customer": "Acme",
                        "project": "Management",
                        "note": "Daily standup"
                    }
                }
            }
        ]
        
        tt.cmd_start(["@daily"])
        
        saved_data = mock_save.call_args_list[0][0][1]
        assert saved_data["current"]["customer"] == "Acme"
        assert saved_data["current"]["project"] == "Management"
        assert saved_data["current"]["notes"] == ["Daily standup"]
        
        captured = capsys.readouterr()
        assert "shortcut" in captured.out
    
    @patch('tt.load_json')
    def test_cmd_start_with_invalid_shortcut(self, mock_load, capsys):
        """Test starting with non-existent shortcut."""
        mock_load.side_effect = [
            {"current": None, "history": []},
            {"customers": [], "shortcuts": {}}
        ]
        
        tt.cmd_start(["@nonexistent"])
        
        captured = capsys.readouterr()
        assert "not found" in captured.out


class TestCmdNote:
    """Test the note command."""
    
    @patch('tt.load_json')
    @patch('tt.save_json')
    def test_cmd_note_adds_to_current(self, mock_save, mock_load, capsys):
        """Test adding a note to running timer."""
        mock_load.return_value = {
            "current": {
                "customer": "Test",
                "project": "Proj",
                "start_timestamp": 100,
                "notes": ["First note"]
            },
            "history": []
        }
        
        tt.cmd_note(["Second", "note"])
        
        saved_data = mock_save.call_args_list[0][0][1]
        assert len(saved_data["current"]["notes"]) == 2
        assert saved_data["current"]["notes"][1] == "Second note"
        
        captured = capsys.readouterr()
        assert "Note added" in captured.out
    
    @patch('tt.load_json')
    def test_cmd_note_no_timer(self, mock_load, capsys):
        """Test adding note when no timer is running."""
        mock_load.return_value = {"current": None, "history": []}
        
        tt.cmd_note(["Some note"])
        
        captured = capsys.readouterr()
        assert "No timer running" in captured.out
    
    @patch('tt.load_json')
    def test_cmd_note_empty(self, mock_load, capsys):
        """Test adding empty note."""
        mock_load.return_value = {
            "current": {"customer": "Test", "project": "Proj", "start_timestamp": 100},
            "history": []
        }
        
        tt.cmd_note([])
        
        captured = capsys.readouterr()
        assert "cannot be empty" in captured.out


class TestCmdStop:
    """Test the stop command."""
    
    @patch('tt.load_json')
    @patch('tt.save_json')
    @patch('tt.stop_current', return_value=True)
    def test_cmd_stop_success(self, mock_stop, mock_save, mock_load):
        """Test successful stop."""
        mock_load.return_value = {"current": {}, "history": []}
        
        tt.cmd_stop()
        
        mock_stop.assert_called_once()
        mock_save.assert_called_once()
    
    @patch('tt.load_json')
    @patch('tt.stop_current', return_value=False)
    def test_cmd_stop_no_timer(self, mock_stop, mock_load, capsys):
        """Test stop when no timer running."""
        mock_load.return_value = {"current": None, "history": []}
        
        tt.cmd_stop()
        
        captured = capsys.readouterr()
        assert "No timer running" in captured.out


class TestCmdReport:
    """Test the report command."""
    
    @patch('tt.load_json')
    def test_cmd_report_empty(self, mock_load, capsys):
        """Test report with no data."""
        mock_load.return_value = {"current": None, "history": []}
        
        tt.cmd_report(copy_mode=False)
        
        captured = capsys.readouterr()
        assert "DAILY REPORT" in captured.out
        assert "TOTAL: 00:00" in captured.out
    
    @patch('tt.load_json')
    def test_cmd_report_with_history(self, mock_load, capsys):
        """Test report with historical entries."""
        mock_load.return_value = {
            "current": None,
            "history": [
                {
                    "customer": "Acme",
                    "project": "Website",
                    "duration_seconds": 900,  # 15 minutes
                    "notes": ["Bug fix"],
                    "start_str": "09:00",
                    "end_str": "09:15"
                },
                {
                    "customer": "Acme",
                    "project": "Website",
                    "duration_seconds": 900,
                    "notes": ["Testing"],
                    "start_str": "10:00",
                    "end_str": "10:15"
                }
            ]
        }
        
        tt.cmd_report(copy_mode=False)
        
        captured = capsys.readouterr()
        assert "Acme" in captured.out
        assert "Website" in captured.out
        assert "Bug fix" in captured.out
        assert "Testing" in captured.out
        assert "00:30" in captured.out  # Total: 30 minutes
    
    @patch('tt.load_json')
    @patch('time.time', return_value=2000.0)
    def test_cmd_report_with_current(self, mock_time, mock_load, capsys):
        """Test report includes running timer."""
        mock_load.return_value = {
            "current": {
                "customer": "Beta",
                "project": "App",
                "start_timestamp": 1100.0,  # 900 seconds ago = 15 min
                "notes": ["In progress"]
            },
            "history": []
        }
        
        tt.cmd_report(copy_mode=False)
        
        captured = capsys.readouterr()
        assert "Beta" in captured.out
        assert "App" in captured.out
        assert "running timer" in captured.out
    
    @patch('tt.load_json')
    @patch('tt.copy_to_clipboard')
    def test_cmd_report_copy_mode(self, mock_clipboard, mock_load, capsys):
        """Test report with clipboard copy."""
        mock_load.return_value = {
            "current": None,
            "history": [
                {
                    "customer": "TestCo",
                    "project": "Project1",
                    "duration_seconds": 900,
                    "notes": ["Task 1"],
                    "start_str": "09:00",
                    "end_str": "09:15"
                }
            ]
        }
        
        tt.cmd_report(copy_mode=True)
        
        mock_clipboard.assert_called_once()
        clipboard_text = mock_clipboard.call_args[0][0]
        assert "TestCo" in clipboard_text
        assert "Project1" in clipboard_text
        
        captured = capsys.readouterr()
        assert "copied to clipboard" in captured.out


class TestCmdShortcut:
    """Test shortcut management."""
    
    @patch('tt.load_json')
    def test_cmd_shortcut_list_empty(self, mock_load, capsys):
        """Test listing shortcuts when none exist."""
        mock_load.return_value = {"customers": [], "shortcuts": {}}
        
        tt.cmd_shortcut(["list"])
        
        captured = capsys.readouterr()
        assert "No shortcuts" in captured.out
    
    @patch('tt.load_json')
    def test_cmd_shortcut_list_with_shortcuts(self, mock_load, capsys):
        """Test listing existing shortcuts."""
        mock_load.return_value = {
            "customers": [],
            "shortcuts": {
                "daily": {
                    "customer": "Acme",
                    "project": "Management",
                    "note": "Daily standup"
                },
                "dev": {
                    "customer": "Beta",
                    "project": "Development",
                    "note": ""
                }
            }
        }
        
        tt.cmd_shortcut(["list"])
        
        captured = capsys.readouterr()
        assert "@daily" in captured.out
        assert "@dev" in captured.out
        assert "Acme" in captured.out
        assert "Management" in captured.out
    
    @patch('tt.load_json')
    @patch('tt.save_json')
    def test_cmd_shortcut_add(self, mock_save, mock_load, capsys):
        """Test adding a new shortcut."""
        mock_load.return_value = {"customers": [], "shortcuts": {}}
        
        tt.cmd_shortcut(["add", "meeting", "Acme", "Planning", "Weekly", "sync"])
        
        saved_config = mock_save.call_args[0][1]
        assert "meeting" in saved_config["shortcuts"]
        assert saved_config["shortcuts"]["meeting"]["customer"] == "Acme"
        assert saved_config["shortcuts"]["meeting"]["project"] == "Planning"
        assert saved_config["shortcuts"]["meeting"]["note"] == "Weekly sync"
        
        captured = capsys.readouterr()
        assert "created" in captured.out
    
    @patch('tt.load_json')
    def test_cmd_shortcut_add_missing_args(self, mock_load, capsys):
        """Test adding shortcut without enough arguments."""
        mock_load.return_value = {"customers": [], "shortcuts": {}}
        
        tt.cmd_shortcut(["add", "name"])
        
        captured = capsys.readouterr()
        assert "Usage" in captured.out
    
    @patch('tt.load_json')
    @patch('tt.save_json')
    def test_cmd_shortcut_delete(self, mock_save, mock_load, capsys):
        """Test deleting a shortcut."""
        mock_load.return_value = {
            "customers": [],
            "shortcuts": {
                "daily": {"customer": "Acme", "project": "Mgmt", "note": ""}
            }
        }
        
        tt.cmd_shortcut(["delete", "daily"])
        
        saved_config = mock_save.call_args[0][1]
        assert "daily" not in saved_config["shortcuts"]
        
        captured = capsys.readouterr()
        assert "deleted" in captured.out
    
    @patch('tt.load_json')
    def test_cmd_shortcut_delete_not_found(self, mock_load, capsys):
        """Test deleting non-existent shortcut."""
        mock_load.return_value = {"customers": [], "shortcuts": {}}
        
        tt.cmd_shortcut(["delete", "nonexistent"])
        
        captured = capsys.readouterr()
        assert "not found" in captured.out
    
    @patch('tt.load_json')
    def test_cmd_shortcut_complete(self, mock_load, capsys):
        """Test --complete flag for shell completion."""
        mock_load.return_value = {
            "customers": [],
            "shortcuts": {
                "daily": {"customer": "A", "project": "B", "note": ""},
                "dev": {"customer": "C", "project": "D", "note": ""}
            }
        }
        
        tt.cmd_shortcut(["--complete"])
        
        captured = capsys.readouterr()
        assert "@daily" in captured.out
        assert "@dev" in captured.out
    
    @patch('tt.load_json')
    def test_cmd_shortcut_pick(self, mock_load, capsys):
        """Test pick flag for fzf integration."""
        mock_load.return_value = {
            "customers": [],
            "shortcuts": {
                "daily": {
                    "customer": "Acme",
                    "project": "Management",
                    "note": "Standup"
                }
            }
        }
        
        tt.cmd_shortcut(["pick"])
        
        captured = capsys.readouterr()
        # Should be tab-separated
        assert "daily\t" in captured.out
        assert "Acme" in captured.out
        assert "Management" in captured.out


class TestCmdAdd:
    """Test the add customer/project command."""
    
    @patch('tt.load_json')
    @patch('tt.save_json')
    @patch('builtins.input')
    def test_cmd_add_new_customer(self, mock_input, mock_save, mock_load, capsys):
        """Test adding a new customer with projects."""
        mock_load.return_value = {"customers": []}
        mock_input.side_effect = ["NewCorp", "Project1", "Project2", ""]
        
        tt.cmd_add()
        
        saved_config = mock_save.call_args[0][1]
        assert len(saved_config["customers"]) == 1
        assert saved_config["customers"][0]["name"] == "NewCorp"
        assert "Project1" in saved_config["customers"][0]["projects"]
        assert "Project2" in saved_config["customers"][0]["projects"]
        
        captured = capsys.readouterr()
        assert "Saved" in captured.out
    
    @patch('tt.load_json')
    @patch('tt.save_json')
    @patch('builtins.input')
    def test_cmd_add_existing_customer(self, mock_input, mock_save, mock_load):
        """Test adding projects to existing customer."""
        mock_load.return_value = {
            "customers": [
                {"name": "ExistingCorp", "projects": ["OldProject"]}
            ]
        }
        mock_input.side_effect = ["ExistingCorp", "NewProject", ""]
        
        tt.cmd_add()
        
        saved_config = mock_save.call_args[0][1]
        customer = saved_config["customers"][0]
        assert len(customer["projects"]) == 2
        assert "NewProject" in customer["projects"]
        assert "OldProject" in customer["projects"]
    
    @patch('tt.load_json')
    @patch('builtins.input', return_value="")
    def test_cmd_add_empty_customer_name(self, mock_input, mock_load, capsys):
        """Test adding with empty customer name."""
        mock_load.return_value = {"customers": []}
        
        tt.cmd_add()
        
        captured = capsys.readouterr()
        assert "cannot be empty" in captured.out


class TestCmdReset:
    """Test the reset command."""
    
    @patch('builtins.input', return_value='y')
    @patch('os.path.exists', return_value=True)
    @patch('os.remove')
    def test_cmd_reset_confirmed(self, mock_remove, mock_exists, mock_input, capsys):
        """Test reset with confirmation."""
        tt.cmd_reset()
        
        mock_remove.assert_called_once()
        captured = capsys.readouterr()
        assert "cleared" in captured.out
    
    @patch('builtins.input', return_value='n')
    def test_cmd_reset_cancelled(self, mock_input, capsys):
        """Test reset cancelled."""
        tt.cmd_reset()
        
        captured = capsys.readouterr()
        assert "Cancelled" in captured.out
    
    @patch('builtins.input', return_value='y')
    @patch('os.path.exists', return_value=False)
    def test_cmd_reset_file_not_exists(self, mock_exists, mock_input, capsys):
        """Test reset when file doesn't exist."""
        tt.cmd_reset()
        
        captured = capsys.readouterr()
        assert "cleared" in captured.out


class TestCmdHelp:
    """Test the help command."""
    
    def test_cmd_help_output(self, capsys):
        """Test help command displays information."""
        tt.cmd_help()
        
        captured = capsys.readouterr()
        assert "TIME TRACKER HELP" in captured.out
        assert "tt start" in captured.out
        assert "tt stop" in captured.out
        assert "tt report" in captured.out
        assert "shortcut" in captured.out


class TestMain:
    """Test the main entry point."""
    
    @patch('sys.argv', ['tt.py'])
    @patch('tt.cmd_start')
    def test_main_no_args(self, mock_start):
        """Test main with no arguments defaults to start."""
        tt.main()
        mock_start.assert_called_once_with([])
    
    @patch('sys.argv', ['tt.py', 'start', '1', '2'])
    @patch('tt.cmd_start')
    def test_main_start_command(self, mock_start):
        """Test main with start command."""
        tt.main()
        mock_start.assert_called_once_with(['1', '2'])
    
    @patch('sys.argv', ['tt.py', 'stop'])
    @patch('tt.cmd_stop')
    def test_main_stop_command(self, mock_stop):
        """Test main with stop command."""
        tt.main()
        mock_stop.assert_called_once()
    
    @patch('sys.argv', ['tt.py', 'report'])
    @patch('tt.cmd_report')
    def test_main_report_command(self, mock_report):
        """Test main with report command."""
        tt.main()
        mock_report.assert_called_once_with(copy_mode=False)
    
    @patch('sys.argv', ['tt.py', 'copy'])
    @patch('tt.cmd_report')
    def test_main_copy_command(self, mock_report):
        """Test main with copy command."""
        tt.main()
        mock_report.assert_called_once_with(copy_mode=True)
    
    @patch('sys.argv', ['tt.py', 'note', 'Test', 'note'])
    @patch('tt.cmd_note')
    def test_main_note_command(self, mock_note):
        """Test main with note command."""
        tt.main()
        mock_note.assert_called_once_with(['Test', 'note'])
    
    @patch('sys.argv', ['tt.py', 'add'])
    @patch('tt.cmd_add')
    def test_main_add_command(self, mock_add):
        """Test main with add command."""
        tt.main()
        mock_add.assert_called_once()
    
    @patch('sys.argv', ['tt.py', 'shortcut', 'list'])
    @patch('tt.cmd_shortcut')
    def test_main_shortcut_command(self, mock_shortcut):
        """Test main with shortcut command."""
        tt.main()
        mock_shortcut.assert_called_once_with(['list'])
    
    @patch('sys.argv', ['tt.py', 'reset'])
    @patch('tt.cmd_reset')
    def test_main_reset_command(self, mock_reset):
        """Test main with reset command."""
        tt.main()
        mock_reset.assert_called_once()
    
    @patch('sys.argv', ['tt.py', 'help'])
    @patch('tt.cmd_help')
    def test_main_help_command(self, mock_help):
        """Test main with help command."""
        tt.main()
        mock_help.assert_called_once()
    
    @patch('sys.argv', ['tt.py', '--help'])
    @patch('tt.cmd_help')
    def test_main_help_flag(self, mock_help):
        """Test main with --help flag."""
        tt.main()
        mock_help.assert_called_once()
    
    @patch('sys.argv', ['tt.py', '1', '2'])
    @patch('tt.cmd_start')
    def test_main_shortcut_syntax(self, mock_start):
        """Test main with shortcut syntax (direct numbers)."""
        tt.main()
        mock_start.assert_called_once_with(['1', '2'])


if __name__ == "__main__":
    print("Run tests with: pytest test_tt.py -v")
    print("Run with coverage: pytest test_tt.py -v --cov=tt --cov-report=html")

