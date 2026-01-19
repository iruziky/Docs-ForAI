import os
import sys
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse
import argparse
import time

def clean_url(url):
    """Remove fragments and query parameters for consistency."""
    parsed = urlparse(url)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, parsed.query, ""))

def get_filename(url, base_url):
    """Generate a safe filename from the URL."""
    path = urlparse(url).path
    if path.endswith('/'):
        path += 'index.html'
    
    if path.startswith('/'):
        path = path[1:]
        
    safe_name = path.replace('/', '_').replace('\\', '_')
    
    if not safe_name:
        safe_name = "index"
        
    if not safe_name.endswith('.txt') and not safe_name.endswith('.md'):
        safe_name += '.md'
        
    return safe_name

def extract_content(soup):
    """Extract main content and remove unnecessary elements."""
    for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'noscript', 'iframe', 'svg']):
        tag.decompose()
        
    content_root = soup.find('main')
    if not content_root:
        content_root = soup.find('article')
    if not content_root:
        content_root = soup.find('div', role='main')
    
    if not content_root:
        content_root = soup.body
        
    if not content_root:
        return ""
        
    for h in content_root.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        level = int(h.name[1])
        h.string = f"\n{'#' * level} {h.get_text().strip()}\n"
        
    for a in content_root.find_all('a', href=True):
        text = a.get_text().strip()
        href = a['href']
        if text:
            a.string = f"[{text}]({href})"
            
    for pre in content_root.find_all('pre'):
        code = pre.get_text()
        pre.string = f"\n```\n{code}\n```\n"

    return content_root.get_text(separator='\n\n', strip=True)

def scrape(base_url, output_dir, make_subdir=True, start_url=None):
    """Perform recursive scraping of a base URL."""
    if make_subdir:
        parsed_base = urlparse(base_url)
        source_name = parsed_base.netloc.replace('.', '_')
        final_output_dir = os.path.join(output_dir, source_name)
    else:
        final_output_dir = output_dir
    
    if not os.path.exists(final_output_dir):
        os.makedirs(final_output_dir)
        
    initial_url = clean_url(base_url)
    queue = [initial_url]
    
    if start_url:
        # If start_url is an absolute URL, use it directly.
        # If it's just a slug (like 'getting-started'), join it with base_url.
        if start_url.startswith(('http://', 'https://')):
            start_page = clean_url(start_url)
        else:
            base_dir = initial_url if initial_url.endswith('/') else initial_url + '/'
            start_page = clean_url(urljoin(base_dir, start_url))
        
        if start_page not in queue:
            queue.append(start_page)
            print(f"Added specific start URL: {start_page}")

    visited = set()
    total_downloaded = 0
    
    print(f"Starting scraper at: {base_url}")
    print(f"URLs in queue: {len(queue)}")
    print(f"Saving to: {final_output_dir}")
    
    while queue:
        current_url = queue.pop(0)
        
        if current_url in visited:
            continue
            
        try:
            print(f"Processing: {current_url}")
            response = requests.get(current_url, timeout=10)
            
            # Handle redirects: use the final URL for resolving links
            final_url = clean_url(response.url)
            if final_url != current_url:
                print(f"Redirected to: {final_url}")
                if final_url not in visited:
                    visited.add(final_url)

            if response.status_code != 200:
                print(f"Error {response.status_code} accessing {current_url}")
                visited.add(current_url)
                continue
                
            content_type = response.headers.get('Content-Type', '')
            if 'text/html' not in content_type:
                print(f"Ignoring non-HTML type: {content_type}")
                visited.add(current_url)
                continue

            visited.add(current_url)
            total_downloaded += 1
            
            soup = BeautifulSoup(response.content, 'html.parser')
            text_content = extract_content(soup)
            
            filename = get_filename(current_url, base_url)
            filepath = os.path.join(final_output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"URL: {current_url}\n")
                f.write(f"Final URL: {final_url}\n\n")
                f.write(text_content)
                
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                # Use final_url (response.url) to resolve relative links correctly
                full_link = urljoin(final_url, href)
                cleaned_link = clean_url(full_link)
                
                if (cleaned_link.startswith(base_url) and 
                    cleaned_link not in visited and 
                    cleaned_link not in queue):
                    queue.append(cleaned_link)
                    
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Error processing {current_url}: {e}")
            
    print(f"\nDone! Total pages downloaded: {total_downloaded}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Recursive Documentation Scraper")
    parser.add_argument("url", help="Base URL to start scraping")
    parser.add_argument("--start-url", help="URL to start scraping from (if different from base)")
    parser.add_argument("--output", default="docs_input", help="Output directory")
    
    args = parser.parse_args()
    
    scrape(args.url, args.output, start_url=args.start_url)
