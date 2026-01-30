"""
Unit tests for GRAVITYbot core functionality.

Run with: pytest test/test_core.py -v
"""
import datetime
import os
import sys
from pathlib import Path

import pandas as pd
import pytest
import pytz

# Add project paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '_src')))


# ---------------------
# prompts.py tests
# ---------------------

class TestFormatData:
    """Tests for prompts.format_data()"""
    
    def test_format_dataframe(self):
        """DataFrame is converted to JSON records string."""
        import prompts
        
        df = pd.DataFrame({
            'comment': ['Hello', 'World'],
            'url': ['http://a.com', 'http://b.com']
        })
        
        result = prompts.format_data(df)
        
        assert result.startswith('[\n')
        assert result.endswith('\n]')
        assert 'Hello' in result
        assert 'World' in result
    
    def test_format_non_dataframe_passthrough(self):
        """Non-DataFrame values pass through unchanged."""
        import prompts
        
        assert prompts.format_data("already a string") == "already a string"
        assert prompts.format_data(123) == 123
        assert prompts.format_data(None) is None
    
    def test_format_empty_dataframe(self):
        """Empty DataFrame produces valid JSON array."""
        import prompts
        
        df = pd.DataFrame(columns=['a', 'b'])
        result = prompts.format_data(df)
        
        assert result == '[\n \n]'


class TestAlogPromptUrls:
    """Tests for alog_prompt URL generation."""
    
    def test_lho_url(self):
        """LHO lab produces LHO URL."""
        import prompts
        
        df = pd.DataFrame({'comment': ['test']})
        user_prompt, sys_prompt = prompts.alog_prompt(df, df, "LHO")
        
        assert 'ligo-wa.caltech.edu' in sys_prompt
        assert 'ligo-la.caltech.edu' not in sys_prompt
    
    def test_llo_url(self):
        """LLO lab produces LLO URL."""
        import prompts
        
        df = pd.DataFrame({'comment': ['test']})
        user_prompt, sys_prompt = prompts.alog_prompt(df, df, "LLO")
        
        assert 'ligo-la.caltech.edu' in sys_prompt


# ---------------------
# Date range tests
# ---------------------

class TestTalkDateRanges:
    """Tests for talk_summary date range calculation."""
    
    def test_date_ranges_from_data(self):
        """Date ranges derived from DataFrame timestamps."""
        from talk_summary import get_date_ranges
        
        # Create DataFrame with known timestamps
        df = pd.DataFrame({
            'timestamp': pd.to_datetime([
                '2025-01-15 12:00:00+00:00',
                '2025-01-20 12:00:00+00:00',
            ])
        })
        
        ranges = get_date_ranges(df)
        
        # Latest is Jan 20, so current period ends there
        assert ranges['current_end'] == '2025-01-20'
    
    def test_date_ranges_without_data(self):
        """Date ranges use current date when no DataFrame provided."""
        from talk_summary import get_date_ranges
        
        ranges = get_date_ranges(None)
        
        # Should have all four keys
        assert 'prior_start' in ranges
        assert 'prior_end' in ranges
        assert 'current_start' in ranges
        assert 'current_end' in ranges


class TestAlogDateRanges:
    """Tests for alog_summary date range calculation."""
    
    def test_period_calculation(self):
        """Periods are calculated correctly from reference date."""
        from alog_summary import get_date_ranges, PERIOD_DAYS, GAP_DAYS
        
        ref_date = datetime.datetime(2025, 1, 27, tzinfo=pytz.UTC)
        ranges = get_date_ranges(ref_date)
        
        # Current period: 5 days ending on ref_date
        assert ranges['current_period_end'] == '2025-01-27'
        assert ranges['current_period_start'] == '2025-01-23'
        
        # Prior period: 5 days with 1 day gap
        assert ranges['prior_period_end'] == '2025-01-22'
        assert ranges['prior_period_start'] == '2025-01-18'


# ---------------------
# CSV parsing tests
# ---------------------

class TestAlogCsvParsing:
    """Tests for alog_summary CSV parsing."""
    
    def test_parse_valid_csv(self, tmp_path):
        """Valid CSV is parsed and split by lab."""
        from alog_summary import parse_alog_csv
        
        csv_content = """entry_title,entry_url,rss_url,entry_date,text,tags,report_id,author_email
Test Entry,http://example.com,https://alog.ligo-wa.caltech.edu/aLOG/rss-feed.php,"Mon, 20 Jan 2025 12:00:00 +0000",Test text,,12345,test@test.com
"""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(csv_content, encoding="utf-8")
        
        result = parse_alog_csv(csv_file)
        
        assert 'LHO' in result
        assert 'LLO' in result
        assert len(result['LHO']) == 1
        assert len(result['LLO']) == 0
    
    def test_skip_embedded_headers(self, tmp_path):
        """Embedded header rows are skipped."""
        from alog_summary import parse_alog_csv
        
        csv_content = """entry_title,entry_url,rss_url,entry_date,text,tags,report_id,author_email
Test Entry,http://example.com,https://alog.ligo-wa.caltech.edu/aLOG/rss-feed.php,"Mon, 20 Jan 2025 12:00:00 +0000",Test text,,12345,test@test.com
entry_title,entry_url,rss_url,entry_date,text,tags,report_id,author_email
Another Entry,http://example.com,https://alog.ligo-wa.caltech.edu/aLOG/rss-feed.php,"Tue, 21 Jan 2025 12:00:00 +0000",More text,,12346,test@test.com
"""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(csv_content, encoding="utf-8")
        
        result = parse_alog_csv(csv_file)
        
        # Should have 2 entries, not 3 (header row skipped)
        assert len(result['LHO']) == 2


# ---------------------
# alog_feed tests
# ---------------------

class TestAlogFeedParsing:
    """Tests for alog_feed entry parsing."""
    
    def test_is_recent_within_window(self):
        """Entry within lookback window is marked recent."""
        from alog_feed import _is_recent
        
        # Entry from "now"
        now = datetime.datetime.now(datetime.timezone.utc)
        entry_date = now.strftime("%a, %d %b %Y %H:%M:%S %z")
        
        result = _is_recent(entry_date, datetime.timedelta(weeks=2))
        
        assert result is True
    
    def test_is_recent_outside_window(self):
        """Entry outside lookback window is not marked recent."""
        from alog_feed import _is_recent
        
        # Entry from 30 days ago
        old_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=30)
        entry_date = old_date.strftime("%a, %d %b %Y %H:%M:%S %z")
        
        result = _is_recent(entry_date, datetime.timedelta(weeks=2))
        
        assert result is False
    
    def test_is_recent_invalid_date(self):
        """Invalid date returns False."""
        from alog_feed import _is_recent
        
        result = _is_recent("not a date", datetime.timedelta(weeks=2))
        
        assert result is False


# ---------------------
# Run with pytest
# ---------------------

if __name__ == "__main__":
    pytest.main([__file__, "-v"])