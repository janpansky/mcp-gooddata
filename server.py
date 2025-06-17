import logging
import os
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from gooddata_sdk import GoodDataSdk

# Load environment variables from .env file
load_dotenv()

# Initialize the MCP server
mcp = FastMCP("Demo")

# Initialize GoodData SDK using environment variables for host and token
GD_HOST = os.environ.get("GOODDATA_HOST")
GD_TOKEN = os.environ.get("GOODDATA_TOKEN")
gd = GoodDataSdk.create(host_=GD_HOST, token_=GD_TOKEN)

@mcp.tool()
def analyze_ldm(workspace_id: str) -> dict:
    """Analyze the declarative LDM for missing/well-defined descriptions."""
    try:
        declarative_ldm = gd.catalog_workspace_content.get_declarative_ldm(workspace_id=workspace_id)
        datasets = getattr(declarative_ldm.ldm, "datasets", [])
        missing = []
        well_defined = []
        for ds in datasets:
            ds_desc = getattr(ds, "description", None)
            # Dataset description check
            if not ds_desc or ds_desc.strip() == "" or ds_desc.strip() == ds.title.strip():
                missing.append({"type": "dataset", "id": ds.id, "title": ds.title, "desc": ds_desc})
            else:
                well_defined.append({"type": "dataset", "id": ds.id, "title": ds.title, "desc": ds_desc})
            # Attribute description check
            for attr in getattr(ds, "attributes", []):
                attr_desc = getattr(attr, "description", None)
                if not attr_desc or attr_desc.strip() == "" or attr_desc.strip() == attr.title.strip():
                    missing.append({"type": "attribute", "id": attr.id, "title": attr.title, "desc": attr_desc, "dataset": ds.id})
                else:
                    well_defined.append({"type": "attribute", "id": attr.id, "title": attr.title, "desc": attr_desc, "dataset": ds.id})
        return {
            "missing_descriptions_count": len(missing),
            "well_defined_descriptions_count": len(well_defined),
            "missing_examples": missing[:5],
            "well_defined_examples": well_defined[:5]
        }
    except Exception as e:
        return {"error": str(e)}

# Reset logging settings that MCP made because we want to use our own logging configuration configured in the bootstrap script
logging.basicConfig(force=True, handlers=[], level=logging.NOTSET)
