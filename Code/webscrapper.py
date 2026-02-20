"""
Urdu Stories Auto-Scraper - IMPROVED CONTENT EXTRACTION
Fixed to handle different HTML structures across all pages
"""

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError as e:
    print("=" * 80)
    print("MISSING DEPENDENCIES!")
    print("=" * 80)
    print("\nPlease install required packages:")
    print("\n  pip install selenium webdriver-manager")
    print("\nThen run this script again.")
    print("=" * 80)
    exit(1)

import json
import time
import csv
import os
import random
import re

class UrduStoryAutoScraper:
    def __init__(self, base_url="https://www.urdupoint.com/kids/section/stories.html", headless=False):
        self.base_url = base_url
        self.stories = []
        self.headless = headless
        self.driver = None
        
    def init_driver(self):
        """Initialize Chrome driver"""
        print("Initializing browser...")
        
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-gpu')
        
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        prefs = {
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_settings.popups": 0,
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        try:
            print("Downloading/updating ChromeDriver...")
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            print("✓ Browser initialized successfully!")
            
        except Exception as e:
            print(f"\n✗ Error: {e}")
            raise
    
    def close_driver(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            print("✓ Browser closed")
    
    def extract_story_links(self, page_url):
        """Extract story links from a listing page"""
        print(f"\n📄 Loading: {page_url}")
        
        try:
            self.driver.get(page_url)
            
            wait = WebDriverWait(self.driver, 15)
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "sharp_box")))
            
            # Scroll to load images
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(random.uniform(1, 2))
            
            story_boxes = self.driver.find_elements(By.CLASS_NAME, "sharp_box")
            story_links = []
            
            for box in story_boxes:
                try:
                    url = box.get_attribute('href')
                    
                    title_ur = ""
                    title_en = ""
                    
                    try:
                        title_ur_elem = box.find_element(By.CLASS_NAME, "title_ur")
                        title_ur = title_ur_elem.text.strip()
                    except:
                        pass
                    
                    try:
                        title_en_elem = box.find_element(By.CLASS_NAME, "title_en")
                        title_en = title_en_elem.text.strip()
                    except:
                        pass
                    
                    img_url = ""
                    try:
                        img = box.find_element(By.TAG_NAME, "img")
                        img_url = img.get_attribute('src') or img.get_attribute('data-src') or ""
                    except:
                        pass
                    
                    if url and title_en:
                        story_links.append({
                            'url': url,
                            'title_urdu': title_ur,
                            'title_english': title_en,
                            'image_url': img_url
                        })
                except:
                    continue
            
            print(f"  ✓ Found {len(story_links)} stories")
            return story_links
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return []
    
    def extract_story_content(self, story_url):
        """Extract story content - improved to handle multiple HTML structures"""
        try:
            self.driver.get(story_url)
            time.sleep(random.uniform(2, 3))
            
            # Scroll to load all content
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            
            # IMPROVED EXTRACTION - handles multiple content structures
            script = """
                let content = '';
                
                // Method 1: Try txt_detail container (new format from page 13+)
                let txtDetail = document.querySelector('div.txt_detail.urdu');
                if (txtDetail) {
                    let clone = txtDetail.cloneNode(true);
                    
                    // Remove all unwanted elements
                    let unwanted = clone.querySelectorAll(
                        'div.txt_banner, ' +
                        '[id*="ad"], [id*="gpt"], [id*="teads"], ' +
                        '[class*="ad"], [class*="banner"], ' +
                        'script, style, iframe, noscript, ' +
                        '[data-id]'
                    );
                    unwanted.forEach(el => el.remove());
                    
                    let text = clone.innerText || clone.textContent;
                    if (text && text.length > 100) {
                        content = text.trim();
                    }
                }
                
                // Method 2: If not found, try right-aligned divs (old format)
                if (!content || content.length < 100) {
                    let divs = document.querySelectorAll('div[style*="text-align: right"], div[style*="text-align:right"]');
                    
                    divs.forEach(div => {
                        let clone = div.cloneNode(true);
                        
                        let unwanted = clone.querySelectorAll(
                            '[id*="ad"], [id*="gpt"], [id*="teads"], [class*="ad"], ' +
                            'script, style, iframe, noscript, [class*="banner"]'
                        );
                        unwanted.forEach(el => el.remove());
                        
                        let text = clone.innerText || clone.textContent;
                        if (text && text.length > 100) {
                            content += text.trim() + '\\n\\n';
                        }
                    });
                }
                
                // Method 3: Try to find by common classes
                if (!content || content.length < 100) {
                    let containers = document.querySelectorAll(
                        'div.urdu, div.rtl, div.story, div.content, article'
                    );
                    
                    containers.forEach(container => {
                        if (container.innerText && container.innerText.length > 200) {
                            let clone = container.cloneNode(true);
                            
                            let unwanted = clone.querySelectorAll(
                                '[id*="ad"], script, style, iframe'
                            );
                            unwanted.forEach(el => el.remove());
                            
                            let text = clone.innerText || clone.textContent;
                            if (text && text.length > content.length) {
                                content = text.trim();
                            }
                        }
                    });
                }
                
                return content.trim();
            """
            
            story_content = self.driver.execute_script(script)
            
            # Clean up content
            if story_content:
                lines = []
                for line in story_content.split('\n'):
                    line = line.strip()
                    # Skip empty lines and ad-related content
                    if line and not any(
                        keyword in line.lower() for keyword in [
                            'advertisement', 'اشتہار', 'google_ads', 'teads', 
                            'gpt-', 'googletag', 'فریق ثالث', 'جاری ہے'
                        ]
                    ):
                        lines.append(line)
                
                story_content = '\n'.join(lines)
            
            return story_content if story_content and len(story_content) > 100 else None
            
        except Exception as e:
            print(f"  ✗ Extraction error: {e}")
            return None
    
    def scrape_stories(self, max_stories=200):
        """Main scraping method"""
        print("\n" + "=" * 80)
        print("URDU STORIES AUTO-SCRAPER - IMPROVED VERSION")
        print("=" * 80)
        print(f"Target: {max_stories} stories")
        print("Total pages available: 173")
        print("Improved content extraction for all page formats")
        print("=" * 80 + "\n")
        
        self.init_driver()
        
        try:
            current_page_num = 0
            total_pages = 173
            failed_count = 0
            max_consecutive_fails = 5
            
            while len(self.stories) < max_stories and current_page_num < total_pages:
                print(f"\n{'─'*80}")
                print(f"📖 PAGE {current_page_num + 1} of {total_pages}")
                print(f"Progress: {len(self.stories)}/{max_stories} stories | Failed: {failed_count}")
                print(f"{'─'*80}")
                
                # Generate page URL
                if current_page_num == 0:
                    page_url = "https://www.urdupoint.com/kids/section/stories.html"
                else:
                    page_url = f"https://www.urdupoint.com/kids/section/stories-page{current_page_num}.html"
                
                # Get story links
                story_links = self.extract_story_links(page_url)
                
                if not story_links:
                    print("  ⚠ No stories found. Moving to next page...")
                    current_page_num += 1
                    continue
                
                # Process each story
                page_failed = 0
                for story_info in story_links:
                    if len(self.stories) >= max_stories:
                        break
                    
                    story_num = len(self.stories) + 1
                    print(f"\n[{story_num}/{max_stories}] 📝 {story_info['title_english']}")
                    
                    content = self.extract_story_content(story_info['url'])
                    
                    if content and len(content) > 100:
                        story_data = {
                            'id': story_num,
                            'title_urdu': story_info['title_urdu'],
                            'title_english': story_info['title_english'],
                            'url': story_info['url'],
                            'image_url': story_info['image_url'],
                            'content': content,
                            'content_length': len(content)
                        }
                        
                        self.stories.append(story_data)
                        print(f"  ✓ Saved! ({len(content)} chars)")
                        failed_count = 0  # Reset fail counter on success
                    else:
                        print(f"  ✗ Failed (no content extracted)")
                        failed_count += 1
                        page_failed += 1
                        
                        # If too many consecutive failures, might be a problem
                        if failed_count >= max_consecutive_fails:
                            print(f"\n  ⚠ Warning: {failed_count} consecutive failures!")
                    
                    # Delay between stories
                    time.sleep(random.uniform(2, 4))
                
                # Report page results
                print(f"\n  Page summary: {len(story_links) - page_failed}/{len(story_links)} stories extracted successfully")
                
                # Move to next page
                if len(self.stories) < max_stories:
                    current_page_num += 1
                    
                    if current_page_num < total_pages:
                        delay = random.uniform(3, 5)
                        print(f"\n⏳ Moving to page {current_page_num + 1} in {delay:.1f}s...")
                        time.sleep(delay)
        
        finally:
            self.close_driver()
        
        print("\n" + "=" * 80)
        print(f"✅ SCRAPING COMPLETE!")
        print("=" * 80)
        print(f"Total stories collected: {len(self.stories)}")
        print(f"Success rate: {len(self.stories)}/{max_stories} ({len(self.stories)*100//max_stories if max_stories > 0 else 0}%)")
        print("=" * 80 + "\n")
        
        return self.stories
    
    def save_to_json(self, filename='urdu_stories.json'):
        """Save to JSON"""
        filepath = os.path.join(os.getcwd(), filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.stories, f, ensure_ascii=False, indent=2)
        print(f"💾 JSON: {filepath}")
        return filepath
    
    def save_to_csv(self, filename='urdu_stories.csv'):
        """Save to CSV"""
        if not self.stories:
            return None
        
        filepath = os.path.join(os.getcwd(), filename)
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['id', 'title_urdu', 'title_english', 
                                                    'url', 'image_url', 'content_length', 'content'])
            writer.writeheader()
            writer.writerows(self.stories)
        
        print(f"💾 CSV: {filepath}")
        return filepath
    
    def save_individual_text_files(self, output_dir='urdu_stories_text'):
        """Save individual text files"""
        dirpath = os.path.join(os.getcwd(), output_dir)
        os.makedirs(dirpath, exist_ok=True)
        
        for story in self.stories:
            safe_title = "".join(c for c in story['title_english'] 
                               if c.isalnum() or c in (' ', '-', '_'))[:50]
            filename = f"{story['id']:03d}_{safe_title}.txt"
            filepath = os.path.join(dirpath, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"Title (Urdu): {story['title_urdu']}\n")
                f.write(f"Title (English): {story['title_english']}\n")
                f.write(f"URL: {story['url']}\n\n")
                f.write("=" * 80 + "\n\n")
                f.write(story['content'])
        
        print(f"💾 Text files: {dirpath}/")
        return dirpath


def main():
    """Main function"""
    print("\n" + "=" * 80)
    print("🚀 URDU STORIES SCRAPER - IMPROVED CONTENT EXTRACTION")
    print("=" * 80)
    print("Now handles both old and new HTML formats!")
    print("=" * 80)
    
    scraper = UrduStoryAutoScraper(headless=False)
    
    # Scrape 200 stories
    stories = scraper.scrape_stories(max_stories=200)
    
    if stories:
        print("\n📦 Saving data...")
        scraper.save_to_json('urdu_stories.json')
        scraper.save_to_csv('urdu_stories.csv')
        scraper.save_individual_text_files('urdu_stories_text')
        
        print("\n" + "=" * 80)
        print("🎉 SUCCESS!")
        print("=" * 80)
        print(f"✓ Collected {len(stories)} stories")
        print(f"✓ Files saved in: {os.getcwd()}")
        print("=" * 80)
    else:
        print("\n❌ No stories were collected")


if __name__ == "__main__":
    main()