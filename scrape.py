import requests
import os
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor

# List of URLs to scrape
urls = [
    "https://www.hgha.com/testosterone-levels-in-men-by-age/",
    "https://my.clevelandclinic.org/health/articles/24101-testosterone",
    "https://www.medicalnewstoday.com/articles/323085",
    "https://www.endocrine.org/news-and-advocacy/news-room/2017/landmark-study-defines-normal-ranges-for-testosterone-levels",
    "https://www.urmc.rochester.edu/encyclopedia/content.aspx?contenttypeid=167&contentid=testosterone_total",
    "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4190174/",
    "https://www.ncbi.nlm.nih.gov/books/NBK532933/",
    "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7520594/",
    "https://www.merckmanuals.com/professional/genitourinary-disorders/male-reproductive-endocrinology-and-related-disorders/male-hypogonadism",
    "https://journals.lww.com/tnpj/Fulltext/2017/02000/Approaches_to_male_hypogonadism_in_primary_care.8.aspx",
    "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4336035/",
    "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3955331/",
    "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4546699/",
    "https://www.liebertpub.com/doi/10.1089/andro.2020.0010",
    "https://endocrinenews.endocrine.org/the-long-haul-treating-men-with-obesity-with-testosterone/",
    "https://www.uptodate.com/contents/7460",
    "https://www.webmd.com/a-to-z-guides/what-is-sex-hormone-binding-globulin",
    "https://www.healthline.com/health/low-shbg",
    "https://journals.lww.com/tnpj/fulltext/2024/08000/testosterone_replacement_therapy_for_hypogonadism_.6.aspx",
    "https://journals.lww.com/tnpj/abstract/2012/08000/testosterone_replacement_therapy_to_improve_health.11.aspx",
    "https://journals.lww.com/tnpj/citation/2024/08000/testosterone_replacement_therapy_for_hypogonadism_.7.aspx",
    "https://journals.lww.com/tnpj/fulltext/2017/02000/approaches_to_male_hypogonadism_in_primary_care.8.aspx",
    "https://journals.lww.com/tnpj/abstract/2016/08000/evaluation_and_treatment_of_male_hypogonadism_in.10.aspx",
    "https://journals.lww.com/tnpj/fulltext/2018/11000/diabetic_autonomic_neuropathy_resulting_in_sexual.7.aspx",
    "https://journals.lww.com/tnpj/fulltext/2020/05000/infertility_management_in_primary_care.11.aspx",
    "https://journals.lww.com/tnpj/fulltext/2010/12000/male_infertility__a_primer_for_nps.9.aspx",
    "https://journals.lww.com/tnpj/citation/2009/09000/testosterone_replacement_therapy__what_to_look.12.aspx",
    "https://journals.lww.com/tnpj/abstract/1991/09000/the_effect_of_drugs_on_male_sexual_function_and.9.aspx",
    "https://journals.lww.com/tnpj/abstract/2003/07000/is_bio_identical_hormone_therapy_fact_or_fairy.8.aspx",
    "https://journals.lww.com/tnpj/citation/2006/09000/erectile_dysfunction.9.aspx",
    "https://journals.lww.com/tnpj/citation/2014/05000/evaluation_of_a_scrotal_mass.3.aspx",
    "https://journals.lww.com/tnpj/citation/2004/12000/erectile_dysfunction_in_primary_care.6.aspx",
    "https://www.webmd.com/men/news/20230616/cm/testosterone-safe-for-most-older-men",
    "https://www.webmd.com/erectile-dysfunction/erectile-dysfunction",
    "https://www.webmd.com/men/xyosted-low-testosterone",
    "https://www.webmd.com/men/features/keep-testosterone-in-balance",
    "https://www.webmd.com/men/features/infertility",
    "https://www.webmd.com/men/features/testosterone-therapy-safety",
    "https://www.webmd.com/erectile-dysfunction/testosterone-replacement-therapy",
    "https://www.webmd.com/men/how-low-testosterone-can-affect-your-sex-drive",
    "https://www.webmd.com/men/what-low-testosterone-can-mean-your-health",
    "https://www.webmd.com/men/features/testosterone-therapy-pros-cons",
    "https://www.webmd.com/men/testosterone-replacement-therapy-is-it-right-for-you",
    "https://www.webmd.com/men/replacement-therapy",
    "https://www.liebertpub.com/doi/10.1089/andro.2022.0009",
    "https://www.liebertpub.com/doi/10.1089/andro.2022.0007",
    "https://www.liebertpub.com/doi/10.1089/andro.2021.0027",
    "https://www.liebertpub.com/doi/10.1089/andro.2020.0003",
    "https://www.liebertpub.com/doi/10.1089/andro.2021.0013",
    "https://www.liebertpub.com/doi/10.1089/andro.2021.0026",
    "https://www.liebertpub.com/doi/10.1089/andro.2021.0034",
    "https://www.liebertpub.com/doi/10.1089/andro.2021.0001",
    "https://www.liebertpub.com/doi/10.1089/andro.2021.0025",
    "https://www.liebertpub.com/doi/10.1089/andro.2022.0011",
    "https://www.liebertpub.com/doi/10.1089/andro.2020.0001",
    "https://www.liebertpub.com/doi/10.1089/andro.2022.0020",
    "https://www.liebertpub.com/doi/10.1089/andro.2021.0028",
    "https://www.liebertpub.com/doi/10.1089/andro.2020.0007",
    "https://www.liebertpub.com/doi/10.1089/andro.2021.0023",
    "https://www.liebertpub.com/doi/10.1089/andro.2021.0018",
    "https://www.liebertpub.com/doi/10.1089/andro.2020.0015",
    "https://www.liebertpub.com/doi/10.1089/andro.2020.0018",
    "https://www.liebertpub.com/doi/10.1089/andro.2020.0011",
    "https://www.liebertpub.com/doi/10.1089/andro.2020.0008",
    "https://www.liebertpub.com/doi/10.1089/andro.2021.0030",
    "https://www.liebertpub.com/doi/10.1089/andro.2021.0024",
    "https://www.liebertpub.com/doi/10.1089/andro.2020.0009",
    "https://www.liebertpub.com/doi/10.1089/andro.2021.0019",
    "https://www.liebertpub.com/doi/10.1089/andro.2020.0019",
    "https://www.liebertpub.com/doi/10.1089/andro.2022.0004",
    "https://www.liebertpub.com/doi/10.1089/andro.2021.0033",
    "https://www.liebertpub.com/doi/10.1089/andro.2020.0013",
    "https://www.liebertpub.com/doi/10.1089/andro.2020.0010",
    "https://www.liebertpub.com/doi/10.1089/andro.2022.0005",
    "https://www.liebertpub.com/doi/10.1089/andro.2021.0031",
    "https://www.liebertpub.com/doi/10.1089/andro.2020.0006",
    "https://www.liebertpub.com/doi/10.1089/andro.2021.0035",
    "https://www.liebertpub.com/doi/10.1089/andro.2021.0029",
    "https://www.liebertpub.com/doi/10.1089/andro.2020.0016",
    "https://www.liebertpub.com/doi/10.1089/andro.2021.0002",
    "https://www.liebertpub.com/doi/10.1089/andro.2022.0012",
    "https://www.liebertpub.com/doi/10.1089/andro.2021.0003",
    "https://www.liebertpub.com/doi/10.1089/andro.2022.0010",
    "https://www.liebertpub.com/doi/10.1089/andro.2021.0032",
    "https://www.liebertpub.com/doi/10.1089/andro.2020.0012",
    "https://www.liebertpub.com/doi/10.1089/andro.2022.0021",
    "https://www.liebertpub.com/doi/10.1089/andro.2022.29008.editorial",
    "https://www.liebertpub.com/doi/10.1089/andro.2021.0010",
    "https://www.liebertpub.com/doi/10.1089/andro.2022.29007.editorial",
    "https://www.liebertpub.com/doi/10.1089/andro.2021.0006",
    "https://www.liebertpub.com/doi/10.1089/andro.2021.0015",
    "https://www.liebertpub.com/doi/10.1089/andro.2021.0014",
    "https://www.liebertpub.com/doi/10.1089/andro.2022.0003"
]

from collections import defaultdict

# Function to filter duplicate URLs
def filter_duplicate_urls(url_list):
    return list(set(url_list))

# Filter the URLs to remove duplicates
urls = filter_duplicate_urls(urls)

def download_as_html(url, domain_failures):
    failure_count = 0  # Track consecutive failures
    max_failures = 3   # Maximum allowed failures for a domain
    domain = urlparse(url).netloc  # Extract the domain from the URL

    while failure_count < max_failures:
        try:
            # Get a filename from the URL
            filename = urlparse(url).path.split('/')[-1]
            if not filename:
                filename = 'index'
                
            # Add .html extension if not present
            if not filename.endswith('.html'):
                filename = f"{filename}.html"
                
            # Handle duplicate filenames by adding a number
            base_filename = filename[:-5]  # Remove .html
            html_path = f"data/{filename}"
            counter = 1
            
            while os.path.exists(html_path):
                filename = f"{base_filename}_{counter}.html"
                html_path = f"data/{filename}"
                counter += 1
            
            # Fetch the webpage content
            response = requests.get(url)
            response.raise_for_status()  # Raise an error for bad responses
            
            # Save the content as HTML
            with open(html_path, 'w', encoding='utf-8') as file:
                file.write(response.text)
            
            print(f"Successfully downloaded {url} to {html_path}")
            return  # Exit the function on success

        except Exception as e:
            failure_count += 1
            print(f"Error downloading {url}: {str(e)}. Attempt {failure_count} of {max_failures}.")
            if failure_count >= max_failures:
                print(f"Skipping domain {domain} after {max_failures} failed attempts.")
                domain_failures.add(domain)  # Mark the domain as failed
                return

def download_urls():
    # Create data directory if it doesn't exist
    if not os.path.exists("data"):
        os.makedirs("data")
    
    domain_failures = set()  # Track failed domains
    for url in urls:
        domain = urlparse(url).netloc
        if domain in domain_failures:
            print(f"Skipping {url} as its domain {domain} has failed previously.")
            continue
        download_as_html(url, domain_failures)

if __name__ == "__main__":
    download_urls()
