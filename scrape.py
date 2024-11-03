import requests
import pdfkit
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
    "https://journals.lww.com/tnpj/citation/2004/12000/erectile_dysfunction_in_primary_care.6.aspx"
]

# Configure pdfkit to use wkhtmltopdf
config = pdfkit.configuration(wkhtmltopdf='/usr/local/bin/wkhtmltopdf')

def download_as_pdf(url):
    try:
        # Get a filename from the URL
        filename = urlparse(url).path.split('/')[-1]
        if not filename:
            filename = 'index'
            
        # Add .pdf extension if not present
        if not filename.endswith('.pdf'):
            filename = f"{filename}.pdf"
            
        # Handle duplicate filenames by adding a number
        base_filename = filename[:-4]  # Remove .pdf
        pdf_path = f"data/{filename}"
        counter = 1
        
        while os.path.exists(pdf_path):
            filename = f"{base_filename}_{counter}.pdf"
            pdf_path = f"data/{filename}"
            counter += 1
        
        # Convert webpage to PDF
        pdfkit.from_url(url, pdf_path, configuration=config)
        print(f"Successfully downloaded {url} to {pdf_path}")
        
    except Exception as e:
        print(f"Error downloading {url}: {str(e)}")

def download_urls():
    # Create data directory if it doesn't exist
    if not os.path.exists("data"):
        os.makedirs("data")
    
    # Process URLs concurrently with max 5 workers
    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(download_as_pdf, urls)

if __name__ == "__main__":
    download_urls()
