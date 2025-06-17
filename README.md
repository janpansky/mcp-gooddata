# GoodData MCP Server Example

This repository demonstrates how to build and run an MCP (Model Context Protocol) server that exposes GoodData Cloud operations as LLM-friendly tools.

## Features
- Example MCP tool: `analyze_ldm` for analyzing the Logical Data Model (LDM) of a GoodData workspace
- **More tools and scenarios are in progress!**
- Easily extensible for more GoodData scenarios
- Interactive development and testing with MCP Inspector

## Requirements
- Python 3.8+
- Node.js (for MCP Inspector)
- GoodData Cloud account and API token

## Setup

1. **Clone the repository:**
   ```sh
   git clone <your-repo-url>
   cd mcp-gooddata
   ```
2. **Create and activate a Python virtual environment:**
   ```sh
   python3 -m venv venv
   source venv/bin/activate
   ```
3. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
4. **Configure your GoodData credentials:**
   - Copy `.env.template` to `.env` and fill in your real credentials:
     ```sh
     cp .env.template .env
     # Edit .env and set your GOODDATA_HOST and GOODDATA_TOKEN
     ```
   - The server will automatically load these values from `.env` using [python-dotenv](https://pypi.org/project/python-dotenv/).

## Running the MCP Server with Inspector

1. **Start the server and Inspector:**
   ```sh
   mcp dev server.py
   ```
   This will launch the MCP Inspector UI at http://localhost:6274.

2. **Test your tools:**
   - Go to the Inspector UI in your browser.
   - Select the `analyze_ldm` tool, enter a `workspace_id`, and run it.

## Versioning with Git

1. **Initialize Git (if not already):**
   ```sh
   git init
   git add .
   git commit -m "Initial GoodData MCP server example"
   ```
2. **Push to your remote repository:**
   ```sh
   git remote add origin <your-repo-url>
   git push -u origin main
   ```

## Extending
- Add more tools in `server.py` using the `@mcp.tool()` decorator.
- See the [GoodData Python SDK docs](https://pypi.org/project/gooddata-sdk/) for more API options.
- See the [MCP Python SDK docs](https://github.com/modelcontextprotocol/python-sdk) for more MCP features.

## Setting up LibreChat

LibreChat is an open-source chat interface that can be used to interact with your MCP server. Here's how to set it up:

### Prerequisites
- Node.js v20.19.0+ (or ^22.12.0 or >= 23.0.0)
- Git
- MongoDB (Atlas or Community Server)

### Installation Steps

1. **Clone LibreChat:**
   ```sh
   git clone https://github.com/danny-avila/LibreChat.git
   cp .env.librechat LibreChat/.env
   cp librechat.example.yaml LibreChat/librechat.yaml
   cd LibreChat
   ```

2. **Create and configure environment:**
   ```sh
   nvm use 20.19.0
   ```

3. **Install dependencies and build:**
   ```sh
   npm ci
   npm run frontend
   ```

4. **Start LibreChat:**
   ```sh
   npm run backend
   ```
   
## Notes
- **Security:** Never commit your API token or secrets to Git!
- **Production:** The Inspector is for development only. In production, call MCP tools via HTTP or from LLM clients.

---

Happy hacking!
