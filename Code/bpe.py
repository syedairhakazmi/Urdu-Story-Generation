"""
Classic BPE (Byte Pair Encoding) Tokenizer - From Scratch
Based on: "Neural Machine Translation of Rare Words with Subword Units" (Sennrich et al., 2016)

Algorithm:
1. Start with character vocabulary
2. Find most frequent bigram (pair of adjacent tokens)
3. Merge that bigram into a single token
4. Add to vocabulary and store the merge rule
5. Repeat until vocabulary size = 250

This reduces vocabulary size while preserving subword semantics.
"""

import os
import re
import json
import pickle
from collections import defaultdict, Counter

class BPETokenizer:
    def __init__(self, vocab_size=250):
        """
        Initialize BPE tokenizer
        
        vocab_size: Target vocabulary size (default 250)
        """
        self.vocab_size = vocab_size
        self.vocab = set()  # Set of all tokens
        self.merges = {}    # Dictionary: (token1, token2) -> merged_token
        self.word_freqs = {}  # Word frequencies from corpus
        
        # Special tokens
        self.special_tokens = ['<PAD>', '<UNK>', '<BOS>', '<EOS>', '<EOP>', '<EOT>']
        
    def get_vocab_from_corpus(self, corpus_file):
        """
        Step 1: Read corpus and get word frequencies
        """
        print("=" * 80)
        print("STEP 1: Reading corpus and building word frequency dictionary")
        print("=" * 80)
        
        with open(corpus_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        print(f"Corpus size: {len(text):,} characters")
        
        # Split into words
        # Replace invisible special tokens with visible markers
        text = text.replace('\ue000', ' <EOS> ')
        text = text.replace('\ue001', ' <EOP> ')
        text = text.replace('\ue002', ' <EOT> ')
        
        # Tokenize into words
        words = re.findall(r'<[A-Z]+>|\S+', text)
        
        print(f"Total words: {len(words):,}")
        
        # Count word frequencies
        word_counts = Counter(words)
        print(f"Unique words: {len(word_counts):,}")
        
        # Convert to character-level representation
        # Add space between characters and mark word end with </w>
        self.word_freqs = {}
        for word, freq in word_counts.items():
            # Split into characters: "hello" -> "h e l l o </w>"
            char_word = ' '.join(list(word)) + ' </w>'
            self.word_freqs[char_word] = freq
        
        print(f"\nExample word representations:")
        for i, (word, freq) in enumerate(list(self.word_freqs.items())[:5]):
            print(f"  {word[:50]}... (freq: {freq})")
        
        return self.word_freqs
    
    def get_pairs(self):
        """
        Step 2: Get all bigrams (adjacent token pairs) with their frequencies
        
        Returns: Counter of (token1, token2) -> frequency
        """
        pairs = defaultdict(int)
        
        for word, freq in self.word_freqs.items():
            symbols = word.split()
            
            # Get all adjacent pairs
            for i in range(len(symbols) - 1):
                pair = (symbols[i], symbols[i + 1])
                pairs[pair] += freq
        
        return pairs
    
    def merge_vocab(self, pair):
        """
        Step 3: Merge the most frequent pair in all words
        
        pair: (token1, token2) to merge
        """
        # Create merged token (no space)
        merged = ''.join(pair)
        
        # Update all words
        new_word_freqs = {}
        
        # Pattern to find and replace the pair
        bigram = ' '.join(pair)
        replacement = merged
        
        for word, freq in self.word_freqs.items():
            # Replace all occurrences of the pair with merged token
            new_word = word.replace(bigram, replacement)
            new_word_freqs[new_word] = freq
        
        self.word_freqs = new_word_freqs
        
        return merged
    
    def train(self, corpus_file):
        """
        Main BPE training algorithm
        """
        print("\n" + "=" * 80)
        print("BPE TOKENIZER TRAINING - CLASSIC ALGORITHM")
        print("=" * 80)
        print(f"Target vocabulary size: {self.vocab_size}")
        print("=" * 80 + "\n")
        
        # Step 1: Get word frequencies from corpus
        self.get_vocab_from_corpus(corpus_file)
        
        # Initialize vocabulary with all characters
        print("\n" + "=" * 80)
        print("STEP 2: Initializing base vocabulary with characters")
        print("=" * 80)
        
        # Add special tokens
        for token in self.special_tokens:
            self.vocab.add(token)
        
        # Add all individual characters from words
        for word in self.word_freqs.keys():
            for char in word.split():
                self.vocab.add(char)
        
        print(f"Initial vocabulary size: {len(self.vocab)}")
        print(f"Special tokens: {self.special_tokens}")
        print(f"Sample characters: {list(self.vocab)[:20]}")
        
        # Calculate how many merges we need
        num_merges = self.vocab_size - len(self.vocab)
        
        print(f"\nNeed {num_merges} merge operations to reach {self.vocab_size} tokens")
        
        # Step 2-4: Iteratively find and merge most frequent pairs
        print("\n" + "=" * 80)
        print(f"STEP 3: Performing {num_merges} BPE merge operations")
        print("=" * 80)
        
        for i in range(num_merges):
            # Get all bigram frequencies
            pairs = self.get_pairs()
            
            if not pairs:
                print(f"\nNo more pairs to merge. Stopping at {len(self.vocab)} tokens.")
                break
            
            # Find most frequent pair
            best_pair = max(pairs, key=pairs.get)
            best_freq = pairs[best_pair]
            
            # Merge the pair
            merged_token = self.merge_vocab(best_pair)
            
            # Store the merge rule
            self.merges[best_pair] = merged_token
            
            # Add merged token to vocabulary
            self.vocab.add(merged_token)
            
            # Print progress
            if (i + 1) % 10 == 0 or i < 10:
                print(f"Merge {i+1:3d}/{num_merges}: ('{best_pair[0]}', '{best_pair[1]}') -> '{merged_token}' [freq: {best_freq:,}]")
        
        print("\n" + "=" * 80)
        print("TRAINING COMPLETE!")
        print("=" * 80)
        print(f"Final vocabulary size: {len(self.vocab)}")
        print(f"Total merge operations: {len(self.merges)}")
        print("=" * 80)
        
        return self.vocab, self.merges
    
    def encode(self, text):
        """
        Encode text using learned BPE merges
        
        Steps:
        1. Split text into words
        2. Split each word into characters
        3. Apply merge operations in order
        4. Return list of tokens
        """
        # Replace invisible tokens
        text = text.replace('\ue000', ' <EOS> ')
        text = text.replace('\ue001', ' <EOP> ')
        text = text.replace('\ue002', ' <EOT> ')
        
        # Split into words
        words = re.findall(r'<[A-Z]+>|\S+', text)
        
        encoded_words = []
        
        for word in words:
            # Handle special tokens
            if word in self.special_tokens:
                encoded_words.append(word)
                continue
            
            # Split into characters and add word boundary
            tokens = list(word) + ['</w>']
            
            # Apply merge operations in order they were learned
            for pair, merged in self.merges.items():
                i = 0
                while i < len(tokens) - 1:
                    # Check if current pair matches
                    if (tokens[i], tokens[i + 1]) == pair:
                        # Merge them
                        tokens = tokens[:i] + [merged] + tokens[i + 2:]
                    else:
                        i += 1
            
            encoded_words.extend(tokens)
        
        return encoded_words
    
    def decode(self, tokens):
        """
        Decode list of tokens back to text
        
        Simply join tokens and clean up word boundaries
        """
        # Join tokens
        text = ''.join(tokens)
        
        # Replace word boundaries with spaces
        text = text.replace('</w>', ' ')
        
        # Clean up special tokens
        text = text.replace('<EOS>', '')
        text = text.replace('<EOP>', '\n\n')
        text = text.replace('<EOT>', '')
        
        return text.strip()
    
    def token_to_id(self, tokens):
        """
        Convert tokens to integer IDs
        """
        # Create token to ID mapping
        vocab_list = sorted(list(self.vocab))
        token2id = {token: i for i, token in enumerate(vocab_list)}
        
        # Convert tokens to IDs
        ids = []
        for token in tokens:
            if token in token2id:
                ids.append(token2id[token])
            else:
                # Unknown token
                ids.append(token2id['<UNK>'])
        
        return ids
    
    def id_to_token(self, ids):
        """
        Convert integer IDs back to tokens
        """
        # Create ID to token mapping
        vocab_list = sorted(list(self.vocab))
        id2token = {i: token for i, token in enumerate(vocab_list)}
        
        # Convert IDs to tokens
        tokens = []
        for id in ids:
            if id in id2token:
                tokens.append(id2token[id])
            else:
                tokens.append('<UNK>')
        
        return tokens
    
    def save(self, filepath='bpe_tokenizer_v250.pkl'):
        """
        Save tokenizer (vocab and merge rules)
        """
        data = {
            'vocab': list(self.vocab),
            'merges': self.merges,
            'vocab_size': self.vocab_size,
            'special_tokens': self.special_tokens,
        }
        
        # Save as pickle
        with open(filepath, 'wb') as f:
            pickle.dump(data, f)
        
        print(f"\n💾 Tokenizer saved to: {filepath}")
        
        # Save merges as text file for inspection
        merges_file = filepath.replace('.pkl', '_merges.txt')
        with open(merges_file, 'w', encoding='utf-8') as f:
            f.write("# BPE Merge Operations\n")
            f.write("# Format: token1 token2 -> merged_token\n")
            f.write("=" * 60 + "\n\n")
            
            for i, (pair, merged) in enumerate(self.merges.items(), 1):
                f.write(f"{i:3d}. '{pair[0]}' + '{pair[1]}' -> '{merged}'\n")
        
        print(f"💾 Merge rules saved to: {merges_file}")
        
        # Save vocabulary as text file
        vocab_file = filepath.replace('.pkl', '_vocab.txt')
        with open(vocab_file, 'w', encoding='utf-8') as f:
            f.write("# BPE Tokenizer Vocabulary\n")
            f.write(f"# Size: {len(self.vocab)}\n")
            f.write("=" * 60 + "\n\n")
            
            vocab_list = sorted(list(self.vocab))
            for i, token in enumerate(vocab_list):
                f.write(f"{i:3d}. {token}\n")
        
        print(f"💾 Vocabulary saved to: {vocab_file}")
    
    def load(self, filepath='bpe_tokenizer_v250.pkl'):
        """
        Load tokenizer from file
        """
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
        
        self.vocab = set(data['vocab'])
        self.merges = data['merges']
        self.vocab_size = data['vocab_size']
        self.special_tokens = data['special_tokens']
        
        print(f"✓ Tokenizer loaded from: {filepath}")
        print(f"  Vocabulary size: {len(self.vocab)}")
        print(f"  Merge operations: {len(self.merges)}")


def test_tokenizer(tokenizer):
    """
    Test the trained tokenizer
    """
    print("\n" + "=" * 80)
    print("TESTING BPE TOKENIZER")
    print("=" * 80)
    
    test_sentences = [
        "ایک دن کی بات ہے۔",
        "وہ سکول جاتا تھا۔",
        "کہانی ختم ہوئی۔",
        "ایک لڑکا بہت محنتی تھا۔",
    ]
    
    for i, sentence in enumerate(test_sentences, 1):
        print(f"\n{'─'*80}")
        print(f"Test {i}: {sentence}")
        print(f"{'─'*80}")
        
        # Encode to tokens
        tokens = tokenizer.encode(sentence)
        print(f"Tokens ({len(tokens)}): {tokens}")
        
        # Encode to IDs
        ids = tokenizer.token_to_id(tokens)
        print(f"IDs: {ids}")
        
        # Decode back
        decoded_tokens = tokenizer.id_to_token(ids)
        decoded_text = tokenizer.decode(decoded_tokens)
        
        print(f"Decoded: {decoded_text}")
        
        # Check match
        match = "✓ MATCH" if decoded_text.strip() == sentence.strip() else "✗ MISMATCH"
        print(f"Status: {match}")
    
    print("\n" + "=" * 80)


def show_merge_examples(tokenizer, num_examples=20):
    """
    Show examples of merge operations
    """
    print("\n" + "=" * 80)
    print("MERGE OPERATIONS EXAMPLES")
    print("=" * 80)
    
    print(f"\nShowing first {num_examples} merge operations:\n")
    
    for i, (pair, merged) in enumerate(list(tokenizer.merges.items())[:num_examples], 1):
        print(f"{i:2d}. ('{pair[0]}', '{pair[1]}') → '{merged}'")
    
    print(f"\n... and {len(tokenizer.merges) - num_examples} more merges")
    print("=" * 80)


def main():
    """
    Main training function
    """
    print("\n" + "=" * 80)
    print("CLASSIC BPE TOKENIZER - FROM SCRATCH")
    print("No pre-built libraries!")
    print("=" * 80)
    
    # Check corpus
    corpus_file = 'urdu_corpus_with_tokens.txt'
    
    if not os.path.exists(corpus_file):
        print(f"\n✗ Error: Corpus file not found: {corpus_file}")
        print("  Run add_special_tokens.py first!")
        return
    
    # Create and train tokenizer
    tokenizer = BPETokenizer(vocab_size=250)
    vocab, merges = tokenizer.train(corpus_file)
    
    # Show merge examples
    show_merge_examples(tokenizer, num_examples=30)
    
    # Show vocabulary statistics
    print("\n" + "=" * 80)
    print("VOCABULARY STATISTICS")
    print("=" * 80)
    
    # Count token types
    special_count = len(tokenizer.special_tokens)
    char_tokens = [t for t in vocab if len(t) == 1 or t == '</w>']
    subword_tokens = [t for t in vocab if t not in tokenizer.special_tokens and t not in char_tokens]
    
    print(f"Total vocabulary: {len(vocab)}")
    print(f"  Special tokens: {special_count}")
    print(f"  Character tokens: {len(char_tokens)}")
    print(f"  Subword tokens: {len(subword_tokens)}")
    
    print(f"\nSample subword tokens:")
    for i, token in enumerate(sorted(subword_tokens)[:20], 1):
        print(f"  {i:2d}. '{token}'")
    
    print("=" * 80)
    
    # Test tokenizer
    test_tokenizer(tokenizer)
    
    # Save tokenizer
    tokenizer.save('bpe_tokenizer_v250.pkl')
    
    print("\n" + "=" * 80)
    print("✅ TRAINING COMPLETE!")
    print("=" * 80)
    print("\nFiles created:")
    print("  1. bpe_tokenizer_v250.pkl         - Tokenizer model")
    print("  2. bpe_tokenizer_v250_merges.txt  - Merge operations")
    print("  3. bpe_tokenizer_v250_vocab.txt   - Vocabulary list")
    print("\nUsage:")
    print("  tokenizer = BPETokenizer()")
    print("  tokenizer.load('bpe_tokenizer_v250.pkl')")
    print("  tokens = tokenizer.encode('ایک جملہ')")
    print("  ids = tokenizer.token_to_id(tokens)")
    print("=" * 80)


if __name__ == "__main__":
    main()