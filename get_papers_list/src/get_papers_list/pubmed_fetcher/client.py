from .models import Paper, Author
from typing import Optional, List
from tqdm import tqdm
from lxml import etree
import requests
from datetime import datetime

class PubMedClient:
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

    def __init__(self,email:Optional[str]="your_email@example.com", api_key:Optional[str] = None):
        self.email = email
        self.api_key = api_key
        self.session = requests.Session()
    
    def search(self,query, max_results = 100) -> List[str]:
        # It searches the PubMed and return list of PMIDs
        params = {
            "db" : "pubmed",
            "term" : query,
            "retmax" : max_results,
            "retmode" : "json"
                }
        if self.email:
            params["email"] = self.email
        if self.api_key:
            params["api_key"] = self.api_key
        
        url = f"{self.BASE_URL}esearch.fcgi"
        response = self.session.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        return data.get("esearchresult", {}).get("idlist", [])
    
    def fetch_papers(self,pmid_list: List[str]) -> List[Paper]:
        # Fetch paper details for given PMIDs

        papers = []
        url = f"{self.BASE_URL}efetch.fcgi"

        # Process in batches to avoid URL lenggth limits
        batch_size = 100
        for i in tqdm(range(0, len(pmid_list), batch_size), desc="Fetching papers"):
            batch = pmid_list[i:i + batch_size]
            params = {
                "db" : "pubmed",
                "id" : ",".join(batch),
                "retmode" : "xml"
            }
            if self.email:
                params["email"] = self.email
            if self.api_key:
                params["api_key"] = self.api_key
    
            response = self.session.get(url, params=params)
            response.raise_for_status()

            root = etree.fromstring(response.content)
            papers.extend(self._parse_papers(root))

        return papers
    def _parse_papers(self, root: etree.Element) -> List[Paper]:
        papers = []
        for article in root.xpath("//PubmedArticle"):
            try:
                paper = self._parse_paper(article)
                papers.append(paper)
            except Exception as e:
                continue
        return papers
    
    def _parse_paper(self, article: etree.Element) -> Paper:
        # Extract basic paper info
        pmid = article.findtext(".//PMID")
        title = article.findtext(".//ArticleTitle") or "No title available"
        
        # Parse publication date
        pub_date = article.find(".//PubDate")
        year = pub_date.findtext("Year")
        month = pub_date.findtext("Month") or "1"
        day = pub_date.findtext("Day") or "1"
        publication_date = datetime.strptime(f"{year}-{month}-{day}", "%Y-%m-%d").date()
        
        # Parse authors
        authors = []
        corresponding_email = None
        for author in article.xpath(".//Author"):
            last_name = author.findtext("LastName")
            fore_name = author.findtext("ForeName")
            if not last_name:
                continue
                
            name = f"{fore_name} {last_name}" if fore_name else last_name
            affiliation = author.findtext("AffiliationInfo/Affiliation")
            
            # Check if author is from pharma/biotech
            is_non_academic = self._is_non_academic_affiliation(affiliation) if affiliation else False
            
            # Check for email (some are in affiliation)
            email = self._extract_email(affiliation) if affiliation else None
            
            # Check if this is corresponding author
            if author.get("ValidYN", "Y") == "Y" and email:
                corresponding_email = email
                
            authors.append(Author(
                name=name,
                affiliation=affiliation,
                is_non_academic=is_non_academic,
                email=email
            ))
        
        return Paper(
            pubmed_id=pmid,
            title=title,
            publication_date=publication_date,
            authors=authors,
            corresponding_author_email=corresponding_email
        )
    
    def _is_non_academic_affiliation(self, affiliation: str) -> bool:
        # Determine if affiliation is from pharma/biotech company
        if not affiliation:
            return False
            
        # Academic indicators
        academic_keywords = [
            "university", "college", "school", "institute", 
            "hospital", "clinic", "academy", "lab", "laboratory"
        ]
        
        # Pharma/biotech indicators
        company_keywords = [
            "pharma", "biotech", "inc", "ltd", "llc", "corporation",
            "company", "co.", "research and development", "r&d"
        ]
        
        # Check for company keywords and absence of academic keywords
        affiliation_lower = affiliation.lower()
        has_company = any(keyword in affiliation_lower for keyword in company_keywords)
        has_academic = any(keyword in affiliation_lower for keyword in academic_keywords)
        
        return has_company and not has_academic
    
    def _extract_email(self, text: Optional[str]) -> Optional[str]:
        # Extract email address from text
        if not text:
            return None
            
        import re
        email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        match = re.search(email_pattern, text)
        return match.group(0) if match else None       