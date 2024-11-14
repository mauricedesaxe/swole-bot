import requests
import os
from urllib.parse import urlparse
from studies import urls
from openai_helpers import make_openai_call
from scrape_tracker import ScrapeTracker

def download_urls():
    os.makedirs("data", exist_ok=True)
    domain_failures = set()
    tracker = ScrapeTracker()
    
    for url in urls:
        if urlparse(url).netloc in domain_failures:
            print(f"Skipping {url} due to previous failure.")
            continue
            
        # Check if URL was already successfully scraped
        was_scraped, file_path = tracker.get_url(url)
        if was_scraped and file_path and os.path.exists(file_path):
            print(f"Skipping {url} - already scraped to {file_path}")
            continue
            
        try:
            file_path = download_as_markdown(url, domain_failures)
            if file_path:
                tracker.add_url(url, success=True, file_path=file_path)
                print(f"Successfully scraped {url} to {file_path}")
            else:
                tracker.add_url(url, success=False, error_message="Content not related to topics")
                print(f"Content not related to topics: {url}")
        except Exception as e:
            error_msg = str(e)
            print(f"Error scraping {url}: {error_msg}")
            tracker.add_url(url, success=False, error_message=error_msg)
            domain_failures.add(urlparse(url).netloc)

def download_as_markdown(url, domain_failures):
    headers = {
        'Authorization': f'Bearer {os.getenv("JINA_API_KEY")}'
    }

    try:
        response = requests.get(f'https://r.jina.ai/{url}', headers=headers)
        response.raise_for_status()
        
        markdown_content = response.text
        content_preview = markdown_content[:1000]
        
        response = make_openai_call(
            messages=[
                {"role": "user", "content": f"Does the following excerpt from an academic paper seem related to the topics of testosterone, TRT, weightlifting, sports medicine, weight loss, or fitness in any way? Answer with 'yes' or 'no'. Excerpt: \n\n{content_preview}"}
            ],
            max_tokens=5
        )

        is_related = response.choices[0].message.content.strip().lower()

        if "yes" not in is_related:
            print(f"Content not related to the topics. Skipping {url}.")
            return None

        title = None
        for line in markdown_content.split('\n'):
            if line.startswith('Title:'):
                title = line.replace('Title:', '').strip()
                break

        if title and not title.lower().startswith(('just a moment', 'verifying')):
            filename = "".join(c if c.isalnum() or c in ('-', '_') else '_' 
                             for c in title.lower()).strip('_')
            filename = filename[:100]
        else:
            filename = urlparse(url).path.split('/')[-1] or 'index'
        
        filename = f"{filename}.md"
        md_path = f"data/{filename}"
        counter = 1
        
        while os.path.exists(md_path):
            md_path = f"data/{filename[:-3]}_{counter}.md"
            counter += 1
        
        with open(md_path, 'w', encoding='utf-8') as file:
            file.write(markdown_content)
        
        return md_path

    except Exception as e:
        print(f"Error downloading {url}: {e}")
        domain_failures.add(urlparse(url).netloc)
        raise

if __name__ == "__main__":
    download_urls()
