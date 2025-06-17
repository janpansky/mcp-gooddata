# GoodData MCP Server Example

This repository demonstrates a Model Context Protocol (MCP) server that exposes GoodData Cloud analytics and modeling operations as LLM-friendly tools for interactive analytics, data engineering, and AI workflows.

## Features
- **analyze_ldm**: Analyze the Logical Data Model (LDM) for missing or well-defined descriptions
- **patch_ldm**: Patch (update) the title and/or description of datasets or attributes in the LDM
- **explain_metric**: Explain how a metric is computed (MAQL, description, and usage in dashboards/insights)
- **create_visualization**: Create a visualization by sending a natural language prompt to GoodData AI compute
- **add_visualization_to_dashboard**: Add a visualization to the first dashboard by specifying only its visualization_id
- Secure environment variable handling
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
   - Copy `.env.template` to `.env` and fill in your `GOODDATA_HOST` and `GOODDATA_TOKEN` values:
     ```sh
     cp .env.template .env
     # Edit .env with your GoodData Cloud host and API token
     ```

## Usage

1. **Start the MCP server:**
   ```sh
   mcp dev server.py
   ```
2. **Open MCP Inspector:**
   - The startup message will provide a link and authentication token.
   - Open the Inspector UI in your browser and paste in the token if prompted.

3. **Available Tools**

| Tool Name      | Description                                                                 |
|---------------|-----------------------------------------------------------------------------|
| analyze_ldm    | Analyze the declarative Logical Data Model (LDM) for missing or well-defined descriptions on datasets and attributes. Returns counts and examples. |
| patch_ldm      | Patch (update) the title and/or description of a dataset or attribute in the Logical Data Model (LDM). Persists changes. |
| explain_metric | Explain how a given metric is computed, including its MAQL expression, description, and where it is used across dashboards and insights. |
| create_visualization | Create a visualization by sending a natural language prompt to GoodData AI compute. Returns a list of visualization objects (id, title, etc). Minimal input: only the prompt string. |
| add_visualization_to_dashboard | Add a visualization to the first dashboard by specifying only its visualization_id (as returned by create_visualization). Places the widget using the schema of existing dashboard items to avoid corruption. |

### Tool Details

#### analyze_ldm
- **Arguments:**
  - `workspace_id` (str): GoodData workspace ID
- **Returns:**
  - Counts and examples of missing/well-defined descriptions for datasets and attributes:
    ```json
    {
      "missing_descriptions_count": 3,
      "well_defined_descriptions_count": 7,
      "missing_examples": [...],
      "well_defined_examples": [...]
    }
    ```

#### patch_ldm
- **Arguments:**
  - `workspace_id` (str): GoodData workspace ID
  - `object_type` (str): "dataset" or "attribute"
  - `object_id` (str): ID of the dataset or attribute to patch
  - `title` (str, optional): New title
  - `description` (str, optional): New description
- **Returns:**
  - Success status and the updated object, or error message

#### explain_metric
- **Arguments:**
  - `workspace_id` (str): GoodData workspace ID
  - `metric_id` (str): Metric identifier (id or local_identifier)
- **Returns:**
  - MAQL expression, description, and usage locations (dashboards, widgets, insights):
    ```json
    {
      "metric_id": "of_orders",
      "maql": "SELECT COUNT({label/order_id})",
      "description": "Counts the number of orders.",
      "explanation": "MAQL: SELECT COUNT({label/order_id})\n(Translation to plain English not implemented)",
      "usage": [
        {"dashboard_id": "...", "dashboard_title": "...", "widget_title": "...", "insight_id": "..."}
      ]
    }
    ```

#### create_visualization
- **Arguments:**
  - `prompt` (str): Natural language prompt describing the visualization to create (e.g., "Show sales by region as a bar chart").
- **Returns:**
  - List of visualization objects with fields like id, title, description, type, visualization_type, and match_score.
- **Notes:**
  - Minimal interface: only the prompt string is required.
  - Results are returned as raw dicts from GoodData AI compute.

#### add_visualization_to_dashboard
- **Arguments:**
  - `visualization_id` (str): The id of the visualization to add (must be obtained from create_visualization).
- **Returns:**
  - YAML message confirming placement, or an error message.
- **Behavior:**
  - The tool clones the structure of existing dashboard widgets to ensure compatibility and prevent corruption.
  - The new visualization is placed at the top of the first dashboard section.
- **Usage Workflow:**
  1. Call `create_visualization` with a prompt.
  2. Copy the returned visualization_id.
  3. Call `add_visualization_to_dashboard` with that id.

---

## Troubleshooting Dashboard Widget Placement
- Widgets are now added by cloning the schema of existing dashboard items, including required fields (e.g., localIdentifier, configuration, dateDataSet, etc.).
- If you encounter dashboard corruption, check that your dashboard contains at least one valid section and item to use as a template.
- For advanced troubleshooting, inspect the dashboard JSON and ensure all required fields are present in the widget structure.

---

## Interactive Development with MCP Inspector
- Use the Inspector UI for rapid prototyping and debugging of your MCP tools.
- All tools are documented with explicit names and descriptions for LLM/AI workflows.
- Secure authentication is enabled by default; use the provided token to access Inspector.

## Extending
- Add new tools by defining Python functions and annotating them with `@mcp.tool(name=..., description=...)`.
- See `server.py` for examples and structure.

## License
MIT

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
