import arxiv
import json
import os
from typing import List
import requests
from mcp.server.fastmcp import FastMCP
import io
import PyPDF2
from typing import Union

PAPER_DIR = "papers"

# Initialize FastMCP server
mcp = FastMCP("research")

@mcp.tool()
def search_papers(topic: str, max_results: int = 5) -> List[str]:
    """
    Search for papers on arXiv based on a topic and store their information.
    
    Args:
        topic: The topic to search for
        max_results: Maximum number of results to retrieve (default: 5)
        
    Returns:
        List of paper IDs found in the search
    """
    
    # Use arxiv to find the papers 
    client = arxiv.Client()

    # Search for the most relevant articles matching the queried topic
    search = arxiv.Search(
        query = topic,
        max_results = max_results,
        sort_by = arxiv.SortCriterion.Relevance
    )

    papers = client.results(search)
    
    # Create directory for this topic
    path = os.path.join(PAPER_DIR, topic.lower().replace(" ", "_"))
    os.makedirs(path, exist_ok=True)
    
    file_path = os.path.join(path, "papers_info.json")

    # Try to load existing papers info
    try:
        with open(file_path, "r") as json_file:
            papers_info = json.load(json_file)
    except (FileNotFoundError, json.JSONDecodeError):
        papers_info = {}

    # Process each paper and add to papers_info  
    paper_ids = []
    for paper in papers:
        paper_ids.append(paper.get_short_id())
        paper_info = {
            'title': paper.title,
            'authors': [author.name for author in paper.authors],
            'summary': paper.summary,
            'pdf_url': paper.pdf_url,
            'published': str(paper.published.date())
        }
        papers_info[paper.get_short_id()] = paper_info
    
    # Save updated papers_info to json file
    with open(file_path, "w") as json_file:
        json.dump(papers_info, json_file, indent=2)
    
    print(f"Results are saved in: {file_path}")
    
    return paper_ids

@mcp.tool()
def extract_info(paper_id: str) -> str:
    """
    Search for information about a specific paper across all topic directories.
    
    Args:
        paper_id: The ID of the paper to look for
        
    Returns:
        JSON string with paper information if found, error message if not found
    """
 
    for item in os.listdir(PAPER_DIR):
        item_path = os.path.join(PAPER_DIR, item)
        if os.path.isdir(item_path):
            file_path = os.path.join(item_path, "papers_info.json")
            if os.path.isfile(file_path):
                try:
                    with open(file_path, "r") as json_file:
                        papers_info = json.load(json_file)
                        if paper_id in papers_info:
                            return json.dumps(papers_info[paper_id], indent=2)
                except (FileNotFoundError, json.JSONDecodeError) as e:
                    print(f"Error reading {file_path}: {str(e)}")
                    continue
    
    return f"There's no saved information related to paper {paper_id}."



@mcp.resource("papers://folders")
def get_available_folders() -> str:
    """
    List all available topic folders in the papers directory.
    
    This resource provides a simple list of all available topic folders.
    """
    folders = []
    
    # Get all topic directories
    if os.path.exists(PAPER_DIR):
        for topic_dir in os.listdir(PAPER_DIR):
            topic_path = os.path.join(PAPER_DIR, topic_dir)
            if os.path.isdir(topic_path):
                papers_file = os.path.join(topic_path, "papers_info.json")
                if os.path.exists(papers_file):
                    folders.append(topic_dir)
    
    # Create a simple markdown list
    content = "# Available Topics\n\n"
    if folders:
        for folder in folders:
            content += f"- {folder}\n"
        content += f"\nUse @{folder} to access papers in that topic.\n"
    else:
        content += "No topics found.\n"
    
    return content

@mcp.resource("papers://{topic}")
def get_topic_papers(topic: str) -> str:
    """
    Get detailed information about papers on a specific topic.
    
    Args:
        topic: The research topic to retrieve papers for
    """
    topic_dir = topic.lower().replace(" ", "_")
    papers_file = os.path.join(PAPER_DIR, topic_dir, "papers_info.json")
    
    if not os.path.exists(papers_file):
        return f"# No papers found for topic: {topic}\n\nTry searching for papers on this topic first."
    
    try:
        with open(papers_file, 'r') as f:
            papers_data = json.load(f)
        
        # Create markdown content with paper details
        content = f"# Papers on {topic.replace('_', ' ').title()}\n\n"
        content += f"Total papers: {len(papers_data)}\n\n"
        
        for paper_id, paper_info in papers_data.items():
            content += f"## {paper_info['title']}\n"
            content += f"- **Paper ID**: {paper_id}\n"
            content += f"- **Authors**: {', '.join(paper_info['authors'])}\n"
            content += f"- **Published**: {paper_info['published']}\n"
            content += f"- **PDF URL**: [{paper_info['pdf_url']}]({paper_info['pdf_url']})\n\n"
            content += f"### Summary\n{paper_info['summary'][:500]}...\n\n"
            content += "---\n\n"
        
        return content
    except json.JSONDecodeError:
        return f"# Error reading papers data for {topic}\n\nThe papers data file is corrupted."

@mcp.prompt()
def generate_search_prompt(topic: str, num_papers: int = 5) -> str:
    """Generate a prompt for Claude to find and discuss academic papers on a specific topic."""
    return f"""Search for {num_papers} academic papers about '{topic}' using the search_papers tool. 

Follow these instructions:
1. First, search for papers using search_papers(topic='{topic}', max_results={num_papers})
2. For each paper found, extract and organize the following information:
   - Paper title
   - Authors
   - Publication date
   - Brief summary of the key findings
   - Main contributions or innovations
   - Methodologies used
   - Relevance to the topic '{topic}'

3. Provide a comprehensive summary that includes:
   - Overview of the current state of research in '{topic}'
   - Common themes and trends across the papers
   - Key research gaps or areas for future investigation
   - Most impactful or influential papers in this area

4. Organize your findings in a clear, structured format with headings and bullet points for easy readability.

Please present both detailed information about each paper and a high-level synthesis of the research landscape in {topic}."""

@mcp.tool()
def hybrid_search(query: str, top_k: int = 5) -> dict:
    """
    Perform a hybrid search (semantic and lexical) for JSTOR content.

    Args:
        query: The search query.
        top_k: Number of results to return.

    Returns:
        Search results as JSON.
    """
    headers = {"Content-Type": "application/json"}
    payload = {"query": query, "limit": top_k}

    cookies = {"UUID": "jeet09"}

    response = requests.post("https://search-vector-service.apps.prod.cirrostratus.org/hybridsearch", json=payload, headers=headers, cookies=cookies)
    response.raise_for_status()
    return response.json()

@mcp.tool()
def semantic_search(query: str, top_k: int = 5) -> dict:
    """
    Perform a semantic search for JSTOR content.

    Args:
        query: The search query.
        top_k: Number of results to return.

    Returns:
        Search results as JSON.
    """
    headers = {"Content-Type": "application/json"}
    payload = {"query": query, "limit": top_k}

    cookies = {"UUID": "jeet09"}

    response = requests.post("https://search-vector-service.apps.prod.cirrostratus.org/semanticsearch", json=payload, headers=headers, cookies=cookies)
    response.raise_for_status()
    return response.json()

@mcp.tool()
def lexical_search(query: str, top_k: int = 5) -> dict:
    """
    Perform a semantic search for JSTOR content.

    Args:
        query: The search query.
        top_k: Number of results to return.

    Returns:
        Search results as JSON.
    """
    headers = {"Content-Type": "application/json"}
    payload = {"query": query, "limit": top_k}

    cookies = {"UUID": "jeet09"}

    response = requests.post("https://search-vector-service.apps.prod.cirrostratus.org/lexicalsearch", json=payload, headers=headers, cookies=cookies)
    response.raise_for_status()
    return response.json()

@mcp.tool()
def jstor_basic_search(query: str, top_k: int = 5) -> dict:
    """
    Perform a basic search for JSTOR content.

    Args:
        query: The search query.
        top_k: Number of results to return.

    Returns:
        Search results as JSON.
    """
    headers = {"Content-Type": "application/json"}
    payload = {"query": query, "limit": top_k}

    cookies = {"UUID": "jeet09"}

    response = requests.post("https://search3.apps.prod.cirrostratus.org/v3.0/jstor/basic", json=payload, headers=headers, cookies=cookies)
    response.raise_for_status()
    return response.json()

@mcp.tool()
def jstor_group_search(query: str, top_k: int = 5) -> dict:
    """
    Perform a group search for JSTOR content. Group the basic search result into different layout based on the content type.

    Args:
        query: The search query.
        top_k: Number of results to return.

    Returns:
        Search results as JSON.
    """
    headers = {"Content-Type": "application/json"}
    payload = {"query": query, "limit": top_k}

    cookies = {"UUID": "jeet09"}

    response = requests.post("https://search3.apps.prod.cirrostratus.org/v3.0/jstor/grouped", json=payload, headers=headers, cookies=cookies)
    response.raise_for_status()
    return response.json()

@mcp.tool()
def get_item_metadata(item_id: str) -> dict:
    """
    Fetch metadata about an item from Cedar delivery service.
    """
    url = f"http://cedar-delivery-service?iid={item_id}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

@mcp.tool()
def search_from_document(file_bytes: bytes, file_type: str) -> dict:
    """
    Extract text from a PDF or text file (provided as raw bytes) and perform a semantic search.

    Args:
        file_bytes: The content of the uploaded file as bytes.
        file_type: Type of file, either 'pdf' or 'txt'.

    Returns:
        Search results as a dictionary.
    """
    text = ""

    if file_type.lower() == "pdf":
        # Read PDF from bytes
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + " "
    elif file_type.lower() == "txt":
        # Decode text from bytes
        text = file_bytes.decode("utf-8")
    else:
        raise ValueError("Unsupported file type. Please provide 'pdf' or 'txt'.")

    # Use extracted text as a query
    return hybrid_search(query=text, top_k=5)

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')