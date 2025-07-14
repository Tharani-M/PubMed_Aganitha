import typer
from typing import Optional
import logging
from get_papers_list.pubmed_fetcher.client import PubMedClient
from get_papers_list.pubmed_fetcher.processor import PaperProcessor

# Create Typer app instance
app = typer.Typer(help="Fetch PubMed papers with pharma/biotech affiliations")

@app.command()
def main(
    query: str = typer.Argument(..., help="PubMed search query"),
    output_file: Optional[str] = typer.Option(
        None, "--file", "-f", help="Output CSV file path"
    ),
    max_results: int = typer.Option(
        100, "--max", "-m", help="Maximum number of results"
    ),
    debug: bool = typer.Option(
        False, "--debug", "-d", help="Enable debug mode"
    )
):
    """Main command function"""
    setup_logging(debug)
    logger = logging.getLogger(__name__)
    
    try:
        client = PubMedClient()
        pmids = client.search(query, max_results)
        papers = client.fetch_papers(pmids)
        pharma_papers = PaperProcessor.filter_pharma_papers(papers)
        PaperProcessor.to_csv(pharma_papers, output_file)
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise typer.Exit(1)

def setup_logging(debug: bool):
    """Configure logging"""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s",
        level=level
    )

# This makes the file executable directly
if __name__ == "__main__":
    app()