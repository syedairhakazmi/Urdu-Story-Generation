"""
Urdu Stories Preprocessor
Cleans and normalizes Urdu text files by:
- Removing HTML/ads
- Removing URLs and English titles
- Removing other language characters (keeping only Urdu and punctuation)
- Normalizing Unicode
- Standardizing punctuation
"""

import os
import re
import unicodedata
from pathlib import Path

class UrduTextPreprocessor:
    def __init__(self, input_dir='urdu_stories_text', output_dir='urdu_stories_cleaned'):
        self.input_dir = input_dir
        self.output_dir = output_dir
        
        # Urdu Unicode ranges
        self.urdu_ranges = [
            (0x0600, 0x06FF),  # Arabic/Urdu main block
            (0x0750, 0x077F),  # Arabic Supplement
            (0xFB50, 0xFDFF),  # Arabic Presentation Forms-A
            (0xFE70, 0xFEFF),  # Arabic Presentation Forms-B
        ]
        
        # Common Urdu punctuation and symbols to keep
        self.keep_punctuation = set([
            '۔', '،', '؛', '؟', '!', ':', ';', 
            '.', ',', '?', '!', '-', '–', '—',
            '"', '"', '"', "'", "'", '\'',
            '(', ')', '[', ']', '{', '}',
            '/', '\\', '|',
            '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
            '۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹',
            '\n', ' ', '\t'
        ])
        
    def is_urdu_char(self, char):
        """Check if character is in Urdu Unicode range"""
        code = ord(char)
        for start, end in self.urdu_ranges:
            if start <= code <= end:
                return True
        return False
    
    def normalize_unicode(self, text):
        """Normalize Unicode characters to their canonical form"""
        # NFD normalization - decomposes characters
        text = unicodedata.normalize('NFD', text)
        # NFC normalization - recomposes to standard form
        text = unicodedata.normalize('NFC', text)
        return text
    
    def remove_metadata_header(self, text):
        """Remove the metadata header (Title, URL, etc.)"""
        # Remove everything before the first ===== line
        parts = text.split('=' * 50, 1)
        if len(parts) > 1:
            return parts[1].strip()
        return text.strip()
    
    def remove_english_and_non_urdu(self, text):
        """Remove English characters and keep only Urdu + allowed punctuation"""
        cleaned_chars = []
        
        for char in text:
            # Keep if it's Urdu or allowed punctuation
            if self.is_urdu_char(char) or char in self.keep_punctuation:
                cleaned_chars.append(char)
            # Replace other characters with space
            elif char.isspace():
                cleaned_chars.append(' ')
        
        return ''.join(cleaned_chars)
    
    def standardize_punctuation(self, text):
        """Standardize punctuation marks"""
        # Replace multiple dots with Urdu full stop
        text = re.sub(r'\.{2,}', '۔', text)
        
        # Replace English punctuation with Urdu equivalents
        replacements = {
            '?': '؟',
            ';': '؛',
            ',': '،',
        }
        
        for eng, urdu in replacements.items():
            text = text.replace(eng, urdu)
        
        # Standardize quotes
        text = re.sub(r'[""]', '"', text)
        text = re.sub(r"['']", "'", text)
        
        # Ensure Urdu full stop at end if missing
        text = text.strip()
        if text and not text.endswith('۔'):
            if text[-1] not in ['؟', '!', '؛']:
                text += '۔'
        
        return text
    
    def remove_extra_whitespace(self, text):
        """Remove excessive whitespace while preserving paragraph structure"""
        # Replace multiple spaces with single space
        text = re.sub(r' +', ' ', text)
        
        # Replace multiple newlines with double newline (paragraph break)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove spaces at start/end of lines
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        # Remove empty lines
        lines = [line for line in text.split('\n') if line.strip()]
        text = '\n\n'.join(lines)
        
        return text.strip()
    
    def remove_common_noise(self, text):
        """Remove common noise patterns"""
        # Remove URLs
        text = re.sub(r'https?://\S+', '', text)
        text = re.sub(r'www\.\S+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove HTML tags (if any remain)
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove common ad-related phrases
        noise_patterns = [
            r'اشتہار',
            r'advertisement',
            r'google',
            r'facebook',
            r'twitter',
            r'instagram',
            r'youtube',
            r'جاری ہے',
            r'\(جاری ہے\)',
        ]
        
        for pattern in noise_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        return text
    
    def remove_isolated_english_words(self, text):
        """Remove standalone English words that might have been missed"""
        # Remove words that are purely English letters
        text = re.sub(r'\b[a-zA-Z]+\b', ' ', text)
        return text
    
    def clean_text(self, text):
        """Apply all cleaning steps"""
        # Step 1: Remove metadata header
        text = self.remove_metadata_header(text)
        
        # Step 2: Normalize Unicode
        text = self.normalize_unicode(text)
        
        # Step 3: Remove common noise
        text = self.remove_common_noise(text)
        
        # Step 4: Remove English and non-Urdu characters
        text = self.remove_english_and_non_urdu(text)
        
        # Step 5: Remove isolated English words (cleanup)
        text = self.remove_isolated_english_words(text)
        
        # Step 6: Standardize punctuation
        text = self.standardize_punctuation(text)
        
        # Step 7: Remove extra whitespace
        text = self.remove_extra_whitespace(text)
        
        return text
    
    def process_file(self, input_path, output_path):
        """Process a single file"""
        try:
            # Read original file
            with open(input_path, 'r', encoding='utf-8') as f:
                original_text = f.read()
            
            # Clean the text
            cleaned_text = self.clean_text(original_text)
            
            # Save cleaned text
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_text)
            
            return True, len(original_text), len(cleaned_text)
            
        except Exception as e:
            print(f"✗ Error processing {input_path}: {e}")
            return False, 0, 0
    
    def process_directory(self):
        """Process all files in the input directory"""
        print("=" * 80)
        print("URDU TEXT PREPROCESSOR")
        print("=" * 80)
        print(f"Input directory: {self.input_dir}")
        print(f"Output directory: {self.output_dir}")
        print("=" * 80 + "\n")
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Get all text files
        input_path = Path(self.input_dir)
        if not input_path.exists():
            print(f"✗ Error: Input directory '{self.input_dir}' not found!")
            print(f"  Make sure the directory exists in: {os.getcwd()}")
            return
        
        text_files = list(input_path.glob('*.txt'))
        
        if not text_files:
            print(f"✗ No .txt files found in {self.input_dir}")
            return
        
        print(f"Found {len(text_files)} files to process\n")
        
        # Process each file
        total_original_size = 0
        total_cleaned_size = 0
        success_count = 0
        
        for i, input_file in enumerate(text_files, 1):
            filename = input_file.name
            output_file = Path(self.output_dir) / filename
            
            print(f"[{i}/{len(text_files)}] Processing: {filename}")
            
            success, orig_size, clean_size = self.process_file(input_file, output_file)
            
            if success:
                success_count += 1
                total_original_size += orig_size
                total_cleaned_size += clean_size
                reduction = ((orig_size - clean_size) / orig_size * 100) if orig_size > 0 else 0
                print(f"  ✓ Cleaned: {orig_size} → {clean_size} chars ({reduction:.1f}% reduction)")
            else:
                print(f"  ✗ Failed")
        
        # Print summary
        print("\n" + "=" * 80)
        print("PREPROCESSING COMPLETE")
        print("=" * 80)
        print(f"Files processed: {success_count}/{len(text_files)}")
        print(f"Total original size: {total_original_size:,} characters")
        print(f"Total cleaned size: {total_cleaned_size:,} characters")
        
        if total_original_size > 0:
            overall_reduction = ((total_original_size - total_cleaned_size) / total_original_size * 100)
            print(f"Overall reduction: {overall_reduction:.1f}%")
        
        print(f"\nCleaned files saved to: {os.path.join(os.getcwd(), self.output_dir)}")
        print("=" * 80)
    
    def create_single_corpus(self, corpus_filename='urdu_corpus.txt'):
        """Combine all cleaned files into a single corpus file"""
        print("\nCreating single corpus file...")
        
        cleaned_path = Path(self.output_dir)
        if not cleaned_path.exists():
            print(f"✗ Output directory not found: {self.output_dir}")
            return
        
        text_files = sorted(cleaned_path.glob('*.txt'))
        
        if not text_files:
            print(f"✗ No cleaned files found in {self.output_dir}")
            return
        
        corpus_path = os.path.join(os.getcwd(), corpus_filename)
        
        with open(corpus_path, 'w', encoding='utf-8') as corpus:
            for i, text_file in enumerate(text_files, 1):
                with open(text_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                
                if content:
                    corpus.write(content)
                    corpus.write('\n\n')  # Separate stories with blank line
        
        print(f"✓ Corpus created: {corpus_path}")
        print(f"  Combined {len(text_files)} stories")
        
        # Get corpus size
        corpus_size = os.path.getsize(corpus_path)
        print(f"  Size: {corpus_size:,} bytes")


def main():
    """Main function"""
    print("\n" + "=" * 80)
    print("🧹 URDU STORIES PREPROCESSING")
    print("=" * 80)
    
    # Check if input directory exists
    input_dir = 'urdu_stories_text'
    if not os.path.exists(input_dir):
        print(f"\n✗ Error: Directory '{input_dir}' not found!")
        print(f"  Current directory: {os.getcwd()}")
        print(f"\nPlease make sure the '{input_dir}' folder is in the current directory.")
        return
    
    # Create preprocessor
    preprocessor = UrduTextPreprocessor(
        input_dir='urdu_stories_text',
        output_dir='urdu_stories_cleaned'
    )
    
    # Process all files
    preprocessor.process_directory()
    
    # Create single corpus file
    preprocessor.create_single_corpus('urdu_corpus.txt')
    
    print("\n✅ All done!")


if __name__ == "__main__":
    main()