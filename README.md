# GoodData MCP Server Example

This repository demonstrates a Model Context Protocol (MCP) server that exposes GoodData Cloud analytics and modeling operations as LLM-friendly tools for interactive analytics, data engineering, and AI workflows.

---

## Quick Reference & Requirements

### System Requirements
- **Python**: 3.8+
- **Node.js**: 16+ (for MCP Inspector)
- **GoodData Cloud** account and API token

### Required Files
- `.env` (copy from `.env.template` and fill in all variables)
- `requirements.txt` (install with pip)
- `server.py` (main MCP server)
- `visualization_converter.py` (AI → visualization object conversion)
- `ldm_quality_check.py` (LDM validation and quality checks)

### Environment Variables (must be set in `.env`)
- `GOODDATA_HOST`
- `GOODDATA_TOKEN`
- `GOODDATA_WORKSPACE`
- `GOODDATA_DATA_SOURCE`  # (required for DB sample queries and field sampling)

---

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

### Environment Variables

The following environment variables must be set (e.g., in your `.env`):
- `GOODDATA_HOST`
- `GOODDATA_TOKEN`
- `GOODDATA_WORKSPACE`
- `GOODDATA_DATA_SOURCE`  # (NEW: required for DB sample queries)

### Key Updates (after latest pull)
- **Imports:**
  - `visualization_converter.py` is now used for converting AI output to visualization objects.
  - `ldm_quality_check.py` is used for LDM validation.
- **Visualization Creation:**
  - `create_visualization` now uses `gd.compute.ai_chat_stream` and the `convert` function.
  - Returns a direct edit URL for the created visualization.
- **Dashboard Placement:**
  - `add_visualization_to_dashboard` returns a direct dashboard URL.
- **Sample Data:**
  - Uses `ScanSqlRequest` to fetch field samples from the data source (requires `GOODDATA_DATA_SOURCE`).
- **LDM Patch:**
  - `patch_ldm` signature is now `patch_ldm(object_id, title=None, description=None)`.
- **Metric Usage:**
  - Uses dependency graph APIs to find where metrics are used or referenced.

---

## How to Find Absolute Paths for MCP Server Configuration

To configure the MCP server in LibreChat (or similar), you need to provide absolute paths to the `/uv` command (for running the server) and to your `server.py` file. Here is how you can find them:

### 1. Find the path to `uv` (microvenv runner)
Run:
```bash
which uv
```
This will output something like `/Users/youruser/.local/bin/uv`. Use this as the `command` in your YAML config.

### 2. Find the path to your `server.py`
Run:
```bash
realpath server.py
```
Or if not installed, use:
```bash
pwd
```
then append `/server.py` to your current directory.

### Example MCP Server YAML Block
```yaml
mcpServers:
   gooddata:
     type: stdio
     command: /Users/janpansky/.local/bin/uv
     args:
      - run
      - --with 
      - mcp 
      - mcp 
      - run 
      - /Users/janpansky/Documents/mpc-gooddata/server.py
     timeout: 30000  
```

---

## Running LibreChat (UI) via Docker

To use the MCP server with the LibreChat UI, you must run LibreChat in Docker.

**Steps:**

1. **Clone the LibreChat repository:**
   ```sh
   git clone https://github.com/danny-avila/LibreChat.git
   cd LibreChat
   ```
2. **Start LibreChat using Docker Compose:**
   ```sh
   docker compose --profile=all up
   ```
   This will build and run all necessary services (UI, backend, database, etc).

3. **Access LibreChat UI:**
   - Open your browser and go to [http://localhost:3080](http://localhost:3080) (default port).
   - Configure your MCP server in the settings or via the `librechat.example.yaml` as shown above.

**Note:**
- Ensure Docker is installed and running on your machine.
- For more details, see the [LibreChat documentation](https://github.com/danny-avila/LibreChat).

---

## Additional Notes
- If you encounter errors about missing fields or types, check that your environment variables are set and that you are using the correct, updated tool signatures.
- For any new features or bugfixes, see the latest commit messages and the `visualization_converter.py` and `ldm_quality_check.py` modules for details.

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

## Extending
- Add more tools in `server.py` using the `@mcp.tool()` decorator.
- See the [GoodData Python SDK docs](https://pypi.org/project/gooddata-sdk/) for more API options.
- See the [MCP Python SDK docs](https://github.com/modelcontextprotocol/python-sdk) for more MCP features.

## Running LibreChat (UI) via Docker

LibreChat is an open-source chat interface that can be used to interact with your MCP server. The recommended way to run LibreChat is via Docker Compose, which sets up all dependencies automatically (UI, backend, database, etc).

### Quick Start (Recommended)

1. **Clone LibreChat:**
   ```sh
   git clone https://github.com/danny-avila/LibreChat.git
   cd LibreChat
   ```
2. **Start LibreChat using Docker Compose:**
   ```sh
   docker compose --profile=all up
   ```
   This builds and runs all necessary services. See [LibreChat documentation](https://github.com/danny-avila/LibreChat) for details.

3. **Access LibreChat UI:**
   - Open your browser at [http://localhost:3080](http://localhost:3080)
   - Configure your MCP server in the settings or via the `librechat.yaml` as shown above.

**Advanced/manual setup:** If you want to run LibreChat without Docker (for development), see the official LibreChat documentation for Node.js, MongoDB, and build instructions.

---

## Notes
- **Security:** Never commit your API token or secrets to Git!

- **Production:** The Inspector is for development only. In production, call MCP tools via HTTP or from LLM clients.

---

Happy hacking!
