"""
Chat Message Filter Module
A comprehensive text filtering system that detects and censors inappropriate content.
"""

import json
import re
from typing import List, Dict, Set, Optional, Tuple
from enum import Enum
import logging

class FilterLevel(Enum):
    """Enumeration for different filtering levels"""
    STRICT = "strict"
    MODERATE = "moderate"
    LENIENT = "lenient"

class ChatMessageFilter:
    """
    A comprehensive chat message filtering system that detects and censors
    offensive words, handles variations, and provides detailed filtering reports.
    """
    
    def __init__(self, curse_words_file: str = "curse_words.json", 
                 filter_level: FilterLevel = FilterLevel.MODERATE):
        """
        Initialize the chat filter with curse words and settings.
        
        Args:
            curse_words_file: Path to JSON file containing curse words
            filter_level: Strictness level for filtering
        """
        self.filter_level = filter_level
        self.curse_words: Set[str] = set()
        self.replacement_char = "*"
        self.max_message_length = 1000
        self.min_message_length = 1
        
        # Statistics tracking
        self.total_messages_processed = 0
        self.total_words_filtered = 0
        
        try:
            self._load_curse_words(curse_words_file)
        except Exception as e:
            logging.warning(f"Failed to load curse words file: {e}")
            # DO NOT load default words - keep empty if file fails
            print(f"⚠️  Warning: No curse words loaded. Filter will not block anything.")
    
    def _load_curse_words(self, file_path: str) -> None:
        """Load curse words from JSON file - handles multiple formats"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                
                # Handle different JSON formats
                if isinstance(data, list):
                    # Format: ["word1", "word2", ...]
                    self.curse_words = set(str(word).lower().strip() for word in data if word)
                elif isinstance(data, dict):
                    # Format: {"words": [...]} or {"curse": [...]} or {"word1": "value", ...}
                    # Try common keys first
                    for key in ['words', 'curse', 'curse_words', 'bad_words', 'profanity']:
                        if key in data and isinstance(data[key], list):
                            self.curse_words = set(str(word).lower().strip() for word in data[key] if word)
                            break
                    else:
                        # If no common key found, use dictionary keys as words
                        self.curse_words = set(str(key).lower().strip() for key in data.keys() if key)
                else:
                    raise ValueError("Invalid JSON format - must be list or dict")
                
                if len(self.curse_words) == 0:
                    raise ValueError("No curse words found in file")
                
                print(f"✅ Loaded {len(self.curse_words)} curse words from {file_path}")
                print(f"   First few words: {sorted(list(self.curse_words))[:5]}...")  # Show first 5
                
        except FileNotFoundError:
            raise FileNotFoundError(f"Curse words file not found: {file_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format in curse words file: {e}")
        except Exception as e:
            raise Exception(f"Error loading curse words: {e}")
    
    def _load_default_words(self) -> None:
        """Load a default set of curse words if file loading fails"""
        # REMOVED - No default words will be loaded
        # User must provide their own curse_words.json
        pass
    
    def add_curse_word(self, word: str) -> bool:
        """
        Add a new curse word to the filter.
        
        Args:
            word: The word to add
            
        Returns:
            True if word was added, False if already exists
        """
        if not word or not isinstance(word, str):
            raise ValueError("Word must be a non-empty string")
        
        word_lower = word.lower().strip()
        if word_lower in self.curse_words:
            return False
        
        self.curse_words.add(word_lower)
        return True
    
    def remove_curse_word(self, word: str) -> bool:
        """
        Remove a curse word from the filter.
        
        Args:
            word: The word to remove
            
        Returns:
            True if word was removed, False if not found
        """
        if not word or not isinstance(word, str):
            return False
        
        word_lower = word.lower().strip()
        if word_lower in self.curse_words:
            self.curse_words.remove(word_lower)
            return True
        return False
    
    def set_replacement_char(self, char: str) -> None:
        """Set the character used for replacement"""
        if len(char) != 1:
            raise ValueError("Replacement character must be exactly one character")
        self.replacement_char = char
    
    def set_filter_level(self, level: FilterLevel) -> None:
        """Set the filtering strictness level"""
        if not isinstance(level, FilterLevel):
            raise ValueError("Level must be a FilterLevel enum")
        self.filter_level = level
    
    def _normalize_word(self, word: str) -> str:
        """Normalize word by removing special characters and digits"""
        # Remove special characters but keep letters
        normalized = re.sub(r'[^a-zA-Z]', '', word.lower())
        return normalized
    
    def _detect_variations(self, word: str) -> bool:
        """
        Detect common variations of curse words (leet speak, character substitution)
        """
        # Common character substitutions
        substitutions = {
            'y': 'u', '1': 'i', '3': 'e', '4': 'a', '5': 's', 
            '7': 't', '@': 'a', '$': 's', '!': 'i'
        }
        
        # Replace common substitutions
        normalized = word.lower()
        for digit, letter in substitutions.items():
            normalized = normalized.replace(digit, letter)
        
        # Remove special characters
        normalized = self._normalize_word(normalized)
        
        return normalized in self.curse_words
    
    def _should_filter_word(self, word: str) -> bool:
        """Determine if a word should be filtered based on current settings"""
        if not word:
            return False
        
        word_clean = self._normalize_word(word)
        
        # Direct match
        if word_clean in self.curse_words:
            return True
        
        # Check variations based on filter level
        if self.filter_level in [FilterLevel.STRICT, FilterLevel.MODERATE]:
            return self._detect_variations(word)
        
        return False
    
    def detect_inappropriate_words(self, message: str) -> List[str]:
        """
        Detect all inappropriate words in a message.
        
        Args:
            message: The message to check
            
        Returns:
            List of inappropriate words found
        """
        if not message or not isinstance(message, str):
            return []
        
        words = re.findall(r'\b\w+\b', message)
        inappropriate_words = []
        
        print(f"🔍 DEBUG: Checking message words: {words}")
        print(f"🔍 DEBUG: Against curse words: {self.curse_words}")
        
        for word in words:
            print(f"   Checking '{word}' -> normalized: '{self._normalize_word(word)}' -> in list: {self._should_filter_word(word)}")
            if self._should_filter_word(word):
                inappropriate_words.append(word)
        
        print(f"🔍 DEBUG: Found inappropriate: {inappropriate_words}")
        return inappropriate_words
    
    def filter_message(self, message: str, preserve_length: bool = True) -> str:
        """
        Filter inappropriate words from a message.
        
        Args:
            message: The message to filter
            preserve_length: Whether to preserve original word length
            
        Returns:
            Filtered message
        """
        if not message or not isinstance(message, str):
            raise ValueError("Message must be a non-empty string")
        
        if len(message) > self.max_message_length:
            raise ValueError(f"Message too long (max {self.max_message_length} characters)")
        
        if len(message) < self.min_message_length:
            raise ValueError(f"Message too short (min {self.min_message_length} character)")
        
        self.total_messages_processed += 1
        filtered_count = 0
        
        def replace_word(match):
            nonlocal filtered_count
            word = match.group()
            if self._should_filter_word(word):
                filtered_count += 1
                if preserve_length:
                    return self.replacement_char * len(word)
                else:
                    return self.replacement_char * 3
            return word
        
        # Use regex to find and replace words
        filtered_message = re.sub(r'\b\w+\b', replace_word, message)
        self.total_words_filtered += filtered_count
        
        return filtered_message
    
    def get_filter_report(self, message: str) -> Dict:
        """
        Generate a detailed report about filtering applied to a message.
        
        Args:
            message: The message to analyze
            
        Returns:
            Dictionary containing filtering statistics
        """
        if not message or not isinstance(message, str):
            return {
                'original_message': '',
                'filtered_message': '',
                'inappropriate_words': [],
                'total_words': 0,
                'filtered_words_count': 0,
                'is_clean': True,
                'filter_level': self.filter_level.value
            }
        
        inappropriate_words = self.detect_inappropriate_words(message)
        filtered_message = self.filter_message(message)
        total_words = len(re.findall(r'\b\w+\b', message))
        
        return {
            'original_message': message,
            'filtered_message': filtered_message,
            'inappropriate_words': inappropriate_words,
            'total_words': total_words,
            'filtered_words_count': len(inappropriate_words),
            'is_clean': len(inappropriate_words) == 0,
            'filter_level': self.filter_level.value,
            'message_length': len(message)
        }
    
    def is_message_clean(self, message: str) -> bool:
        """
        Check if a message is clean (contains no inappropriate words).
        
        Args:
            message: The message to check
            
        Returns:
            True if message is clean, False otherwise
        """
        return len(self.detect_inappropriate_words(message)) == 0
    
    def get_statistics(self) -> Dict:
        """Get filtering statistics"""
        return {
            'total_messages_processed': self.total_messages_processed,
            'total_words_filtered': self.total_words_filtered,
            'curse_words_count': len(self.curse_words),
            'filter_level': self.filter_level.value,
            'replacement_character': self.replacement_char
        }
    
    def reset_statistics(self) -> None:
        """Reset filtering statistics"""
        self.total_messages_processed = 0
        self.total_words_filtered = 0
    
    def export_curse_words(self, file_path: str) -> None:
        """Export current curse words to a JSON file"""
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(sorted(list(self.curse_words)), file, indent=2)
        except Exception as e:
            raise IOError(f"Failed to export curse words: {e}")
    
    def batch_filter_messages(self, messages: List[str]) -> List[str]:
        """
        Filter multiple messages at once.
        
        Args:
            messages: List of messages to filter
            
        Returns:
            List of filtered messages
        """
        if not isinstance(messages, list):
            raise ValueError("Messages must be a list")
        
        return [self.filter_message(msg) if isinstance(msg, str) else "" 
                for msg in messages]
    
    def get_word_severity(self, word: str) -> str:
        """
        Get the severity level of a word (placeholder for future enhancement).
        
        Args:
            word: The word to check
            
        Returns:
            Severity level as string
        """
        if self._should_filter_word(word):
            return "offensive"
        return "clean"


def create_sample_curse_words_file(filename: str = "curse_words.json") -> None:
    """Create a sample curse words JSON file for testing"""
    # DO NOT create default English words
    # User must provide their own curse_words.json
    print("⚠️  Please create your own curse_words.json file")
    print("   Example format: [\"word1\", \"word2\", \"word3\"]")


if __name__ == "__main__":
    # Example usage
    create_sample_curse_words_file()
    
    filter_system = ChatMessageFilter()
    
    test_messages = [
        "salom",
        "xayr",
        "blyat"
    ]
    
    for message in test_messages:
        report = filter_system.get_filter_report(message)
        print(f"Original: {report['original_message']}")
        print(f"Filtered: {report['filtered_message']}")
        print(f"Clean: {report['is_clean']}")
        print("-" * 50)