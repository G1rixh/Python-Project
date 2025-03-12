# main.py
import argparse
import csv
import logging
import re
import requests
from typing import List, Dict, Optional

BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
FETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

def fetch_pubmed_ids(query: str) -> List[str]:
    params = {
        "db": "pubmed",
        "term": query,
        "retmode": "json",
        "retmax": 100
    }
    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()
    return response.json().get("esearchresult", {}).get("idlist", [])

def fetch_paper_details(pubmed_ids: List[str]) -> List[Dict]:
    params = {
        "db": "pubmed",
        "id": ",".join(pubmed_ids),
        "retmode": "json"
    }
    response = requests.get(FETCH_URL, params=params)
    response.raise_for_status()
    return response.json().get("result", {})

def extract_paper_data(paper: Dict) -> Dict:
    authors = paper.get("authors", [])

    non_academic_authors = [author["name"] for author in authors if not re.search(r"university|institute|college|lab", author.get("affiliation", ""), re.IGNORECASE)]
    company_affiliations = [author.get("affiliation", "") for author in authors if re.search(r"pharma|biotech", author.get("affiliation", ""), re.IGNORECASE)]

    return {
        "PubmedID": paper.get("uid", ""),
        "Title": paper.get("title", ""),
        "Publication Date": paper.get("pubdate", ""),
        "Non-academic Author(s)": ", ".join(non_academic_authors),
        "Company Affiliation(s)": ", ".join(company_affiliations),
        "Corresponding Author Email": paper.get("elocationid", "")
    }

def save_to_csv(data: List[Dict], filename: Optional[str] = None) -> None:
    fieldnames = ["PubmedID", "Title", "Publication Date", "Non-academic Author(s)", "Company Affiliation(s)", "Corresponding Author Email"]
    if filename:
        with open(filename, mode="w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
    else:
        writer = csv.DictWriter(print, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            print(row)

def main():
    parser = argparse.ArgumentParser(description="Fetch PubMed papers and export to CSV.")
    parser.add_argument("query", help="PubMed search query")
    parser.add_argument("-f", "--file", help="Output CSV filename", default=None)
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    try:
        pubmed_ids = fetch_pubmed_ids(args.query)
        logging.debug(f"Fetched PubMed IDs: {pubmed_ids}")

        paper_details = fetch_paper_details(pubmed_ids)

        extracted_data = [extract_paper_data(paper_details[pid]) for pid in pubmed_ids if pid in paper_details]

        save_to_csv(extracted_data, args.file)

    except Exception as e:
        logging.error(f"Error occurred: {e}")

if __name__ == "__main__":
    main()