from datetime import date
from typing import List, Optional
from pydantic import BaseModel
from pydantic import BaseModel, field_validator

class Author(BaseModel):
    name: str
    affiliation: Optional[str] = None
    is_non_academic: bool = False
    email: Optional[str] = None

    @field_validator('affiliation')
    def clean_affiliation(cls, v):
        if v:
            return v.strip()
        else:
            return None

class Paper(BaseModel):
    pubmed_id: str
    title: str
    publication_date:Optional[date] = None
    authors: List[Author]
    # corresponding_author_email: Optional[str] = None
    
    @property
    def non_academic_authors(self) -> List[str]:
        return [f"{a.name} ({a.affiliation})" 
               if a.affiliation else a.name
               for a in self.authors
               if a.is_non_academic]

    @property
    def company_affiliations(self) -> List[str]:
        return list({author.affiliation for author in self.authors 
                   if author.is_non_academic and author.affiliation})
    
    @property
    def corresponding_author_email(self) -> Optional[str]:
        # Try to find email in authors first
        for author in self.authors:
            if author.email:
                return author.email
        return None