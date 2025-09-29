"""
Comprehensive Test Suite for Chat Message Filter
Tests all functionality including positive, negative, and boundary cases.
Minimum 15 test cases as required by the project.
"""

import pytest
import json
import os
import tempfile
from chat_filter import ChatMessageFilter, FilterLevel


class TestChatMessageFilter:
    """Test class for ChatMessageFilter functionality"""
    
    @pytest.fixture
    def temp_curse_words_file(self):
        """Create a temporary curse words file for testing"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            test_words = {
                "curse": ["blyat", "suka", "enangnikiga", "qanju", "iflos"]
            }
            json.dump(test_words, f, ensure_ascii=False)
            temp_file = f.name
        
        yield temp_file
        
        # Cleanup
        if os.path.exists(temp_file):
            os.unlink(temp_file)
    
    @pytest.fixture
    def filter_instance(self, temp_curse_words_file):
        """Create a filter instance with test data"""
        return ChatMessageFilter(temp_curse_words_file)
    
    # POSITIVE TESTS (correct input → correct output)
    
    @pytest.mark.positive
    def test_initialization_with_valid_file(self, temp_curse_words_file):
        """Test successful initialization with valid curse words file"""
        filter_obj = ChatMessageFilter(temp_curse_words_file)
        assert len(filter_obj.curse_words) == 5
        assert "blyat" in filter_obj.curse_words
        assert filter_obj.filter_level == FilterLevel.MODERATE
    
    @pytest.mark.positive
    def test_add_curse_word_success(self, filter_instance):
        """Test successfully adding a new curse word"""
        initial_count = len(filter_instance.curse_words)
        result = filter_instance.add_curse_word("yomon_soz")
        
        assert result is True
        assert len(filter_instance.curse_words) == initial_count + 1
        assert "yomon_soz" in filter_instance.curse_words
    
    @pytest.mark.positive
    def test_remove_curse_word_success(self, filter_instance):
        """Test successfully removing a curse word"""
        initial_count = len(filter_instance.curse_words)
        result = filter_instance.remove_curse_word("blyat")
        
        assert result is True
        assert len(filter_instance.curse_words) == initial_count - 1
        assert "blyat" not in filter_instance.curse_words
    
    @pytest.mark.positive
    def test_set_replacement_char_valid(self, filter_instance):
        """Test setting valid replacement character"""
        filter_instance.set_replacement_char("#")
        assert filter_instance.replacement_char == "#"
    
    @pytest.mark.positive
    def test_detect_inappropriate_words_clean_message(self, filter_instance):
        """Test detecting inappropriate words in clean message"""
        result = filter_instance.detect_inappropriate_words("Salom yaxshimisan qalesan?")
        assert result == []
    
    @pytest.mark.positive
    def test_detect_inappropriate_words_dirty_message(self, filter_instance):
        """Test detecting inappropriate words in dirty message"""
        result = filter_instance.detect_inappropriate_words("Salom suka qalesan blyat")
        assert "suka" in result
        assert "blyat" in result
        assert len(result) == 2
    
    @pytest.mark.positive
    def test_filter_message_clean(self, filter_instance):
        """Test filtering clean message"""
        original = "Assalomu alaykum! Bugun ajoyib kun."
        filtered = filter_instance.filter_message(original)
        assert filtered == original
    
    @pytest.mark.positive
    def test_filter_message_with_curse_words(self, filter_instance):
        """Test filtering message with curse words"""
        original = "Salom suka blyat qalesan!"
        filtered = filter_instance.filter_message(original)
        assert "****" in filtered
        assert "*****" in filtered
        assert "Salom" in filtered
    
    @pytest.mark.positive
    def test_is_message_clean_true(self, filter_instance):
        """Test clean message detection"""
        assert filter_instance.is_message_clean("Salom dunyo!")
        assert filter_instance.is_message_clean("Привет мир")
    
    @pytest.mark.positive
    def test_is_message_clean_false(self, filter_instance):
        """Test dirty message detection"""
        assert not filter_instance.is_message_clean("Sen blyat sen!")
        assert not filter_instance.is_message_clean("Bu suka gap!")
    
    @pytest.mark.positive
    def test_get_statistics(self, filter_instance):
        """Test getting filter statistics"""
        filter_instance.filter_message("Salom dunyo!")
        filter_instance.filter_message("Sen blyat suka sen!")
        
        stats = filter_instance.get_statistics()
        
        assert stats['total_messages_processed'] == 2
        assert stats['total_words_filtered'] == 2
        assert stats['curse_words_count'] == len(filter_instance.curse_words)
    
    @pytest.mark.positive
    def test_batch_filter_messages(self, filter_instance):
        """Test filtering multiple messages at once"""
        messages = [
            "Salom dunyo!",
            "Sen blyat suka sen!",
            "Bugun ajoyib kun"
        ]
        
        filtered_messages = filter_instance.batch_filter_messages(messages)
        
        assert len(filtered_messages) == len(messages)
        assert filtered_messages[0] == messages[0]
        assert "****" in filtered_messages[1] or "*****" in filtered_messages[1]
    
    # NEGATIVE TESTS (invalid input → error handling)
    
    @pytest.mark.negative
    def test_add_curse_word_invalid_input(self, filter_instance):
        """Test adding invalid curse words"""
        with pytest.raises(ValueError):
            filter_instance.add_curse_word("")
        
        with pytest.raises(ValueError):
            filter_instance.add_curse_word(None)
    
    @pytest.mark.negative
    def test_set_replacement_char_invalid(self, filter_instance):
        """Test setting invalid replacement character"""
        with pytest.raises(ValueError):
            filter_instance.set_replacement_char("")
        
        with pytest.raises(ValueError):
            filter_instance.set_replacement_char("**")
    
    @pytest.mark.negative
    def test_set_filter_level_invalid(self, filter_instance):
        """Test setting invalid filter level"""
        with pytest.raises(ValueError):
            filter_instance.set_filter_level("invalid")
    
    @pytest.mark.negative
    def test_filter_message_invalid_input(self, filter_instance):
        """Test filtering with invalid input"""
        with pytest.raises(ValueError):
            filter_instance.filter_message("")
        
        with pytest.raises(ValueError):
            filter_instance.filter_message(None)
    
    @pytest.mark.negative
    def test_batch_filter_messages_invalid_input(self, filter_instance):
        """Test batch filtering with invalid input"""
        with pytest.raises(ValueError):
            filter_instance.batch_filter_messages("not a list")
    
    # BOUNDARY TESTS (edge cases and limits)
    
    @pytest.mark.boundary
    def test_detect_inappropriate_words_empty_message(self, filter_instance):
        """Test detecting inappropriate words in empty message"""
        result = filter_instance.detect_inappropriate_words("")
        assert result == []
        
        result = filter_instance.detect_inappropriate_words(None)
        assert result == []
    
    @pytest.mark.boundary
    def test_filter_message_too_long(self, filter_instance):
        """Test filtering message that's too long"""
        long_message = "a" * (filter_instance.max_message_length + 1)
        with pytest.raises(ValueError):
            filter_instance.filter_message(long_message)
    
    @pytest.mark.boundary
    def test_case_insensitive_filtering(self, filter_instance):
        """Test that filtering is case-insensitive"""
        messages = [
            "BLYAT bu gap",
            "blyat bu gap",
            "BlYaT bU gAp"
        ]
        
        for message in messages:
            filtered = filter_instance.filter_message(message)
            assert "****" in filtered or "*****" in filtered
    
    @pytest.mark.boundary
    def test_punctuation_and_special_characters(self, filter_instance):
        """Test filtering with punctuation and special characters"""
        message = "Nima blyat!!! Bu suka gap, rostmi?"
        filtered = filter_instance.filter_message(message)
        
        assert "*****!!!" in filtered
        assert "****" in filtered
        assert "Nima" in filtered
        assert "rostmi?" in filtered
    
    @pytest.mark.positive
    def test_filter_level_enum(self):
        """Test FilterLevel enum functionality"""
        assert FilterLevel.STRICT.value == "strict"
        assert FilterLevel.MODERATE.value == "moderate" 
        assert FilterLevel.LENIENT.value == "lenient"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])