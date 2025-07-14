import csv
from typing import List, Optional
from .models import Paper

class PaperProcessor:
    @staticmethod
    def filter_pharma_papers(papers: List[Paper]) -> List[Paper]:
        return [paper for paper in papers if paper.company_affiliations]

    @staticmethod
    def to_csv(papers: List[Paper], output_file: Optional[str] = None):
        """Enhanced CSV output with proper data handling"""
        fieldnames = [
            "PubmedID",
            "Title",
            "Publication Date",
            "Non-academic Author(s)",
            "Company Affiliation(s)",
            "Corresponding Author Email"
        ]

        rows = []
        for paper in papers:
            # Handle missing/empty values
            pub_date = paper.publication_date.strftime("%Y-%m-%d") if paper.publication_date else "N/A"
            non_academic = "; ".join(paper.non_academic_authors) if paper.non_academic_authors else "N/A"
            companies = "; ".join(paper.company_affiliations) if paper.company_affiliations else "N/A"
            email = paper.corresponding_author_email or "N/A"

            rows.append({
                "PubmedID": paper.pubmed_id,
                "Title": paper.title.strip() if paper.title else "N/A",
                "Publication Date": pub_date,
                "Non-academic Author(s)": non_academic,
                "Company Affiliation(s)": companies,
                "Corresponding Author Email": email
            })

        if output_file:
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
        else:
            import sys
            writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)