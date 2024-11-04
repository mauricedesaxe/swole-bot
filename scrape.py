import requests
import os
from urllib.parse import urlparse
import time
from studies import urls

def download_as_markdown(url, domain_failures):
    headers = {
        'Authorization': f'Bearer {os.getenv("JINA_API_KEY")}'
    }

    for attempt in range(3):
        try:
            response = requests.get(f'https://r.jina.ai/{url}', headers=headers)
            response.raise_for_status()
            
            # Extract title from markdown content
            markdown_content = response.text
            title = None
            
            # Try to find title in markdown content
            for line in markdown_content.split('\n'):
                if line.startswith('Title:'):
                    title = line.replace('Title:', '').strip()
                    break
            
            # Generate filename from title or URL if no title found
            if title and not title.lower().startswith(('just a moment', 'verifying')):
                # Convert title to filename-friendly format
                filename = "".join(c if c.isalnum() or c in ('-', '_') else '_' 
                                 for c in title.lower()).strip('_')
                # Limit filename length
                filename = filename[:100]
            else:
                # Fallback to URL-based filename
                filename = urlparse(url).path.split('/')[-1] or 'index'
            
            filename = f"{filename}.md"
            md_path = f"data/{filename}"
            counter = 1
            
            while os.path.exists(md_path):
                md_path = f"data/{filename[:-3]}_{counter}.md"
                counter += 1
            
            with open(md_path, 'w', encoding='utf-8') as file:
                file.write(markdown_content)
            
            print(f"Downloaded {url} to {md_path}")
            return

        except Exception as e:
            print(f"Error downloading {url}: {e}. Attempt {attempt + 1} of 3.")
            if attempt == 2:
                domain_failures.add(urlparse(url).netloc)
            time.sleep(2 * (attempt + 1))

def download_urls():
    os.makedirs("data", exist_ok=True)
    domain_failures = set()
    
    for url in urls:
        if urlparse(url).netloc in domain_failures:
            print(f"Skipping {url} due to previous failure.")
            continue
        download_as_markdown(url, domain_failures)

if __name__ == "__main__":
    download_urls()
