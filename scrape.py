import requests
import os
from urllib.parse import urlparse
import time
from studies import urls
from openai_helpers import make_openai_call

def download_urls():
    os.makedirs("data", exist_ok=True)
    domain_failures = set()
    
    for url in urls:
        if urlparse(url).netloc in domain_failures:
            print(f"Skipping {url} due to previous failure.")
            continue
        download_as_markdown(url, domain_failures)

def download_as_markdown(url, domain_failures):
    headers = {
        'Authorization': f'Bearer {os.getenv("JINA_API_KEY")}'
    }

    try:
        response = requests.get(f'https://r.jina.ai/{url}', headers=headers)
        response.raise_for_status()
        
        # Extract title from markdown content
        markdown_content = response.text
        title = None

        # Take only the first 1000 characters for the relevance check
        content_preview = markdown_content[:1000]
        
        # Call OpenAI to check if the content is related to the topic
        response = make_openai_call(
            messages=[
                {"role": "user", "content": f"Does the following excerpt from an academic paper seem related to the topics of testosterone, TRT, weightlifting, sports medicine, weight loss, or fitness in any way? Answer with 'yes' or 'no'. Excerpt: \n\n{content_preview}"}
            ],
            max_tokens=5
        )

        # Extract the response
        is_related = response.choices[0].message.content.strip().lower()

        if "yes" not in is_related:
            print(f"Content not related to the topics. Stopping download for {url}.")
            return
        
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
        print(f"Error downloading {url}: {e}.")
        domain_failures.add(urlparse(url).netloc)

if __name__ == "__main__":
    download_urls()
