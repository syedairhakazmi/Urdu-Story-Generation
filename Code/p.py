"""
Special Tokens Injector for Urdu Stories
Adds special tokens using unused Unicode private use area characters:
- <EOS> - End of Sentence (after ۔ ؟ ! etc.)
- <EOP> - End of Paragraph (double newlines)
- <EOT> - End of Text/Story (end of file)
"""

import os
import re
from pathlib import Path

class SpecialTokenInjector:
    def __init__(self, input_dir='urdu_stories_cleaned', output_dir='urdu_stories_tokenized'):
        self.input_dir = input_dir
        self.output_dir = output_dir
        
        # Use Unicode Private Use Area (U+E000 to U+F8FF)
        # These are guaranteed to not conflict with any standard characters
        self.SPECIAL_TOKENS = {
            'EOS': '\uE000',  # U+E000 - End of Sentence
            'EOP': '\uE001',  # U+E001 - End of Paragraph
            'EOT': '\uE002',  # U+E002 - End of Text/Story
        }
        
        # Sentence-ending punctuation in Urdu
        self.sentence_endings = ['۔', '؟', '!']
        
        self.stats = {
            'files_processed': 0,
            'total_sentences': 0,
            'total_paragraphs': 0,
            'total_stories': 0,
        }
    
    def add_sentence_markers(self, text):
        """Add <EOS> after sentence-ending punctuation"""
        count = 0
        
        for punct in self.sentence_endings:
            # Add EOS after each sentence-ending punctuation
            pattern = f'{re.escape(punct)}'
            replacement = f'{punct}{self.SPECIAL_TOKENS["EOS"]}'
            
            # Count occurrences
            count += text.count(punct)
            
            # Replace
            text = text.replace(punct, replacement)
        
        return text, count
    
    def add_paragraph_markers(self, text):
        """Add <EOP> at paragraph breaks (double newlines)"""
        # Split by double newlines
        paragraphs = text.split('\n\n')
        
        # Add EOP to end of each paragraph (except last)
        marked_paragraphs = []
        for i, para in enumerate(paragraphs):
            para = para.strip()
            if para:
                if i < len(paragraphs) - 1:
                    # Add EOP to all paragraphs except last
                    marked_paragraphs.append(para + self.SPECIAL_TOKENS['EOP'])
                else:
                    # Last paragraph doesn't get EOP (will get EOT instead)
                    marked_paragraphs.append(para)
        
        # Join with double newlines
        text = '\n\n'.join(marked_paragraphs)
        
        return text, len(marked_paragraphs) - 1  # Don't count last paragraph
    
    def add_story_marker(self, text):
        """Add <EOT> at the end of the story"""
        text = text.strip()
        if not text.endswith(self.SPECIAL_TOKENS['EOT']):
            text += self.SPECIAL_TOKENS['EOT']
        return text
    
    def process_text(self, text):
        """Add all special tokens to text"""
        # Step 1: Add sentence markers
        text, sentence_count = self.add_sentence_markers(text)
        self.stats['total_sentences'] += sentence_count
        
        # Step 2: Add paragraph markers
        text, paragraph_count = self.add_paragraph_markers(text)
        self.stats['total_paragraphs'] += paragraph_count
        
        # Step 3: Add story end marker
        text = self.add_story_marker(text)
        self.stats['total_stories'] += 1
        
        return text
    
    def process_file(self, input_path, output_path):
        """Process a single file"""
        try:
            # Read file
            with open(input_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # Add special tokens
            marked_text = self.process_text(text)
            
            # Save
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(marked_text)
            
            return True
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return False
    
    def process_directory(self):
        """Process all files in directory"""
        print("=" * 80)
        print("SPECIAL TOKEN INJECTOR")
        print("=" * 80)
        print(f"Input:  {self.input_dir}")
        print(f"Output: {self.output_dir}")
        print()
        print("Special Tokens:")
        for name, char in self.SPECIAL_TOKENS.items():
            print(f"  <{name}> = U+{ord(char):04X} ({repr(char)})")
        print("=" * 80 + "\n")
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Get input files
        input_path = Path(self.input_dir)
        if not input_path.exists():
            print(f"✗ Error: Directory '{self.input_dir}' not found!")
            return
        
        text_files = sorted(input_path.glob('*.txt'))
        
        if not text_files:
            print(f"✗ No .txt files found in {self.input_dir}")
            return
        
        print(f"Found {len(text_files)} files\n")
        
        # Process files
        for i, input_file in enumerate(text_files, 1):
            filename = input_file.name
            output_file = Path(self.output_dir) / filename
            
            print(f"[{i:3d}/{len(text_files)}] {filename}")
            
            if self.process_file(input_file, output_file):
                self.stats['files_processed'] += 1
                print(f"          ✓ Tokens added")
        
        # Print summary
        self._print_summary()
    
    def _print_summary(self):
        """Print processing summary"""
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Files processed:     {self.stats['files_processed']}")
        print(f"Total sentences:     {self.stats['total_sentences']:,}")
        print(f"Total paragraphs:    {self.stats['total_paragraphs']:,}")
        print(f"Total stories:       {self.stats['total_stories']}")
        print()
        
        avg_sentences = self.stats['total_sentences'] / self.stats['files_processed'] if self.stats['files_processed'] > 0 else 0
        avg_paragraphs = self.stats['total_paragraphs'] / self.stats['files_processed'] if self.stats['files_processed'] > 0 else 0
        
        print(f"Avg sentences/story: {avg_sentences:.1f}")
        print(f"Avg paragraphs/story: {avg_paragraphs:.1f}")
        print()
        print(f"Output directory: {os.path.join(os.getcwd(), self.output_dir)}")
        print("=" * 80)
    
    def create_corpus_with_tokens(self, corpus_filename='urdu_corpus_with_tokens.txt'):
        """Create single corpus file with all special tokens"""
        print("\n📚 Creating corpus with special tokens...")
        
        output_path = Path(self.output_dir)
        if not output_path.exists():
            print(f"✗ Directory not found: {self.output_dir}")
            return
        
        text_files = sorted(output_path.glob('*.txt'))
        
        if not text_files:
            print(f"✗ No files found")
            return
        
        corpus_path = os.path.join(os.getcwd(), corpus_filename)
        
        with open(corpus_path, 'w', encoding='utf-8') as corpus:
            for text_file in text_files:
                with open(text_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                
                if content:
                    corpus.write(content)
                    corpus.write('\n\n')  # Separate stories
        
        corpus_size = os.path.getsize(corpus_path)
        print(f"✓ Corpus created: {corpus_path}")
        print(f"  Stories: {len(text_files)}")
        print(f"  Size: {corpus_size:,} bytes")
    
    def export_token_mapping(self, filename='special_tokens.txt'):
        """Export token mapping for reference"""
        filepath = os.path.join(os.getcwd(), filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("Special Token Mapping for Urdu Tokenizer\n")
            f.write("=" * 50 + "\n\n")
            
            f.write("Token Definitions:\n")
            f.write("-" * 50 + "\n")
            for name, char in self.SPECIAL_TOKENS.items():
                f.write(f"<{name}>:\n")
                f.write(f"  Unicode: U+{ord(char):04X}\n")
                f.write(f"  Character: {repr(char)}\n")
                f.write(f"  Decimal: {ord(char)}\n")
                f.write(f"  Hex: {hex(ord(char))}\n")
                f.write("\n")
            
            f.write("\nUsage:\n")
            f.write("-" * 50 + "\n")
            f.write("<EOS> - End of Sentence\n")
            f.write("  Added after: ۔ ؟ !\n")
            f.write("  Example: یہ ایک جملہ ہے۔<EOS>\n\n")
            
            f.write("<EOP> - End of Paragraph\n")
            f.write("  Added after paragraph breaks\n")
            f.write("  Example: پیراگراف ختم۔<EOS><EOP>\n\n")
            
            f.write("<EOT> - End of Text/Story\n")
            f.write("  Added at end of each story\n")
            f.write("  Example: کہانی ختم۔<EOS><EOT>\n\n")
            
            f.write("\nFor Tokenizer Implementation:\n")
            f.write("-" * 50 + "\n")
            f.write("Python code to use these tokens:\n\n")
            f.write("SPECIAL_TOKENS = {\n")
            for name, char in self.SPECIAL_TOKENS.items():
                f.write(f"    '{name}': '\\u{ord(char):04x}',  # U+{ord(char):04X}\n")
            f.write("}\n\n")
            
            f.write("# Or as integer IDs:\n")
            f.write("SPECIAL_TOKEN_IDS = {\n")
            for name, char in self.SPECIAL_TOKENS.items():
                f.write(f"    '{name}': {ord(char)},  # {hex(ord(char))}\n")
            f.write("}\n")
        
        print(f"\n📄 Token mapping saved: {filepath}")
    
    def show_example(self):
        """Show example of how tokens look"""
        print("\n" + "=" * 80)
        print("EXAMPLE OUTPUT")
        print("=" * 80)
        
        example_text = """ایک دفعہ کا ذکر ہے کہ ایک لڑکا تھا۔ اس کا نام احمد تھا۔

وہ روز سکول جاتا تھا۔ وہ بہت محنتی تھا؟ ہاں، بالکل۔

کہانی ختم ہوئی۔"""
        
        marked = self.process_text(example_text)
        
        print("\nOriginal:")
        print("-" * 80)
        print(example_text)
        
        print("\n\nWith Special Tokens:")
        print("-" * 80)
        print(marked)
        
        print("\n\nVisible Representation:")
        print("-" * 80)
        # Show tokens as <EOS>, <EOP>, <EOT> for readability
        visible = marked
        for name, char in self.SPECIAL_TOKENS.items():
            visible = visible.replace(char, f'<{name}>')
        print(visible)
        
        print("\n" + "=" * 80)


def main():
    """Main function"""
    print("\n" + "=" * 80)
    print("🏷️  SPECIAL TOKEN INJECTION")
    print("=" * 80)
    
    # Check input directory
    input_dir = 'urdu_stories_cleaned'
    if not os.path.exists(input_dir):
        print(f"\n✗ Error: Directory '{input_dir}' not found!")
        print(f"  Please run preprocessing first to create cleaned files.")
        print(f"  Current directory: {os.getcwd()}")
        return
    
    # Create injector
    injector = SpecialTokenInjector(
        input_dir='urdu_stories_cleaned',
        output_dir='urdu_stories_tokenized'
    )
    
    # Show example first
    injector.show_example()
    
    # Process all files
    injector.process_directory()
    
    # Create corpus
    injector.create_corpus_with_tokens('urdu_corpus_with_tokens.txt')
    
    # Export token mapping
    injector.export_token_mapping('special_tokens.txt')
    
    print("\n✅ Special token injection complete!")
    print("\nNext steps:")
    print("  1. Use urdu_corpus_with_tokens.txt for training")
    print("  2. Reference special_tokens.txt for tokenizer implementation")
    print("  3. Individual files are in urdu_stories_tokenized/")


if __name__ == "__main__":
    main()
