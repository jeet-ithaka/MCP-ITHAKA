# MCP Research Chatbot

A research assistant chatbot built using Model Context Protocol (MCP) that helps users search, retrieve, and analyze academic papers and research content.

## Features

- **ArXiv Paper Search**: Search for academic papers on ArXiv by topic
- **Paper Summaries**: View detailed information about papers including titles, authors, publication dates, and summaries
- **JSTOR Integration**: Perform semantic, lexical, and hybrid searches of JSTOR content
- **Document Analysis**: Extract text from PDFs and perform semantic searches based on document content
- **Interactive Chat Interface**: Natural language interface for all research queries
- **Extensible Tool System**: Built on Model Context Protocol (MCP) for easy extension with new tools and data sources

## Getting Started

### Prerequisites

- Python 3.8+
- Anthropic API key (for Claude access)
- Node.js (for filesystem MCP server)

### Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd mcp-project
   ```

2. Set up a virtual environment and install dependencies:
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -e .
   ```

3. Create a `.env` file with your Anthropic API key:
   ```
   api_key=your_anthropic_api_key_here
   ```

### Configuration

The project uses a `server_config.json` file to configure MCP servers:

- **filesystem**: Provides file system access using the MCP filesystem server
- **research**: Custom server for academic paper search and analysis
- **fetch**: Web data retrieval for accessing online content

## Usage

1. Start the chatbot:
   ```
   python mcp_chatbot.py
   ```

2. Available commands:
   - Search for papers: Enter any research query
   - List available topics: `@folders`
   - View papers by topic: `@<topic_name>`
   - List available prompts: `/prompts`
   - Execute a specific prompt: `/prompt <prompt_name> <arg1=value1> <arg2=value2>`
   - Exit the application: `quit`

### Example Queries

- "Find me recent papers about machine learning"
- "Search JSTOR for research on climate change impacts"
- "Compare the methodologies used in these three papers"
- "Summarize the key findings from papers about quantum computing"
- "@machine_learning" (view papers in the machine learning topic)

## Architecture

This project is built on the Model Context Protocol (MCP), which enables AI applications to access external tools, resources, and prompts. The architecture includes:

- **MCP Host**: The chatbot application that connects to MCP servers
- **MCP Clients**: Components that maintain connections to different MCP servers
- **MCP Servers**: Programs that provide context and functionality to the chatbot
  - Custom research server (`server.py`)
  - Filesystem server for local file access
  - Fetch server for web access

## Development

### Adding New Tools

To add new research tools to the system, modify `server.py` and add new tool functions using the `@mcp.tool()` decorator:

```python
@mcp.tool()
def my_new_tool(param1: str, param2: int = 10) -> dict:
    """
    Tool description for Claude.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
    """
    # Tool implementation
    return {"result": "Success"}
```

### Adding New Resources

To add new data resources, use the `@mcp.resource()` decorator:

```python
@mcp.resource("my-resource://{param}")
def get_my_resource(param: str) -> str:
    """Resource description"""
    # Resource implementation
    return f"Resource content for {param}"
```

## License

[Your license information]

## Acknowledgments

- [Anthropic](https://www.anthropic.com/) for Claude AI
- [Model Context Protocol](https://github.com/anthropics/MCP) for the tool integration framework
- [ArXiv API](https://arxiv.org/help/api) for academic paper access
- [JSTOR](https://www.jstor.org/) for academic content search capabilities