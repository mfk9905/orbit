import math
from typing import List

class KeyboardEngine:
    """
    A minimal swipe-to-text engine that maps key sequences to words.
    In a real-world scenario, this would use a complex path-matching algorithm 
    (like dynamic time warping or neural networks) over a large dictionary.
    Here we use a simplified sequence matching.
    """
    def __init__(self):
        # A small sample dictionary for demonstration
        self.dictionary = [
            "merhaba", "selam", "evet", "hayır", "teşekkürler", "tamam",
            "hello", "world", "test", "orbit", "ofis", "çalışma"
        ]

    def _normalize_word(self, word: str) -> str:
        # Simplistic normalization (e.g., lowercase)
        return word.lower()

    def predict_word(self, key_sequence: List[str]) -> str:
        """
        Predicts a word given a sequence of touched keys during a swipe.
        key_sequence might look like ['m', 'e', 'r', 'h', 'a', 'b', 'a'] or 
        with extra noise keys ['m', 'e', 'r', 't', 'y', 'h', 'a', 'b', 'v', 'a'].
        """
        if not key_sequence:
            return ""

        # Remove consecutive duplicate keys
        clean_seq = []
        for k in key_sequence:
            if not clean_seq or clean_seq[-1] != k:
                clean_seq.append(k.lower())

        if not clean_seq:
            return ""

        seq_str = "".join(clean_seq)
        
        # Simple heuristic: Exact match first
        for word in self.dictionary:
            if word == seq_str:
                return word

        # Fuzzy match: Find dictionary words that start and end with the same letters,
        # and contain the letters of the word in order within the sequence.
        best_match = ""
        best_score = -1

        for word in self.dictionary:
            word = word.lower()
            if len(word) < 2 and len(clean_seq) < 2:
                continue
                
            if word[0] == clean_seq[0] and word[-1] == clean_seq[-1]:
                # Check subsequence
                seq_idx = 0
                match_count = 0
                for char in word:
                    # Find char in the remaining sequence
                    found_idx = seq_str.find(char, seq_idx)
                    if found_idx != -1:
                        match_count += 1
                        seq_idx = found_idx + 1
                
                # If we matched all characters in order
                if match_count == len(word):
                    # Score based on how closely the length matches the sequence length (less noise is better)
                    score = len(word) / len(clean_seq)
                    if score > best_score:
                        best_score = score
                        best_match = word

        # If no fuzzy match, return the raw sequence (for debugging or exact typing)
        return best_match if best_match else seq_str
