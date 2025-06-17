import logging
import os
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
import yaml
from gooddata_sdk import GoodDataSdk, CatalogDependentEntitiesRequest, CatalogEntityIdentifier
from gooddata_api_client.model.scan_sql_request import ScanSqlRequest
from ldm_quality_check import has_no_description, obfuscated_title_check, semantic_similarity_check
from visualization_converter import convert
import uuid

# Load environment variables from .env file
load_dotenv()

# Initialize the MCP server
mcp = FastMCP("Demo")

# Initialize GoodData SDK using environment variables for host and token
GD_HOST = os.environ.get("GOODDATA_HOST")
GD_TOKEN = os.environ.get("GOODDATA_TOKEN")
GD_WORKSPACE = os.environ.get("GOODDATA_WORKSPACE")
GD_DATA_SOURCE = os.environ.get("GOODDATA_DATA_SOURCE")
gd = GoodDataSdk.create(host_=GD_HOST, token_=GD_TOKEN)

@mcp.tool(
    name="analyze_ldm",
    description="Analyze the declarative Logical Data Model (LDM) for missing or well-defined descriptions on attributes and facts. Returns counts and examples."
)
def analyze_ldm() -> dict:
    """Analyze the declarative LDM for missing/well-defined descriptions of attributes and facts."""
    try:
        declarative_ldm = gd.catalog_workspace_content.get_declarative_ldm(workspace_id=GD_WORKSPACE)
        datasets = getattr(declarative_ldm.ldm, "datasets", [])
        missing_descriptions_attributes = []
        missing_descriptions_facts = []
        obfuscated_title_attributes = []
        obfuscated_title_facts = []
        similar_attributes = []
        similar_facts = []
        for ds in datasets:
            similar_attributes = semantic_similarity_check(ds.attributes).semantically_similar_pairs
            similar_facts = semantic_similarity_check(ds.facts).semantically_similar_pairs
            for attr in ds.attributes:
                if has_no_description(attr):
                    missing_descriptions_attributes.append({"title": attr.title, "id": attr.id})
                obfuscated_title_result =  obfuscated_title_check(attr)
                if obfuscated_title_result.is_obfuscated:
                    obfuscated_title_attributes.append({"title": attr.title, "reason": obfuscated_title_result.reason, "id": attr.id})
            for fact in ds.facts:
                if has_no_description(fact):
                    missing_descriptions_facts.append({"title": fact.title, "id": fact.id})
                obfuscated_title_result =  obfuscated_title_check(fact)
                if obfuscated_title_result.is_obfuscated:
                    obfuscated_title_facts.append({"title": fact.title, "reason": obfuscated_title_result.reason, "id": fact.id})
        result = {
            "missing_descriptions_attributes": len(missing_descriptions_attributes),
            "missing_descriptions_facts ": len(missing_descriptions_facts),
            "missing_descriptions_attributes_examples": missing_descriptions_attributes[:5],
            "missing_descriptions_facts_examples": missing_descriptions_facts[:5],
            "obfuscated_title_attributes": len(obfuscated_title_attributes),
            "obfuscated_title_facts": len(obfuscated_title_facts),
            "obfuscated_title_attributes_examples": obfuscated_title_attributes[:5],
            "obfuscated_title_facts_examples": obfuscated_title_facts[:5],
            "similar_attributes": similar_attributes,
            "similar_facts": similar_facts,
        }
        return yaml.safe_dump(result, sort_keys=False, allow_unicode=True)
    except Exception as e:
        return yaml.safe_dump({"error": str(e)}, sort_keys=False, allow_unicode=True)

@mcp.tool(
    name="analyze_field",
    description="Analyze the specific field in the Logical Data Model (LDM)"
)
def analyze_field(dataset_id: str, field_id: str) -> dict:
    """Gather info about a specific field: DB name, dataset, title, description, and sample data."""
    try:
        # Fetch LDM info
        declarative_ldm = gd.catalog_workspace_content.get_declarative_ldm(workspace_id=GD_WORKSPACE)
        field_meta = None
        for ds in getattr(declarative_ldm.ldm, "datasets", []):
            if ds.id == dataset_id:
                for attr in getattr(ds, "attributes", []):
                    if attr.id == field_id:
                        field_meta = {
                            "dataset_id": ds.id,
                            "dataset_title": ds.title,
                            "field_id": attr.id,
                            "field_title": attr.title,
                            "field_description": getattr(attr, "description", None),
                            "source_column": getattr(attr, "source_column", None),
                            "source_table": ds.data_source_table_id.path[-1],
                        }
                        break
                        
        if not field_meta:
            raise Exception(f"Field {field_id} not found in LDM")
        # Sample data
        sql_request = ScanSqlRequest(
            sql=f"SELECT DISTINCT \"{field_meta['source_column']}\" FROM \"{field_meta['source_table']}\" ORDER BY RANDOM() LIMIT 10;",
        )
        result = gd.client.actions_api.scan_sql(GD_DATA_SOURCE, sql_request)
        sample_data = ", ".join([row[0] for row in result["data_preview"]])
        result = {"field_meta": field_meta, "sample_data": sample_data}
        return yaml.safe_dump(result, sort_keys=False, allow_unicode=True)
    except Exception as e:
        return yaml.safe_dump({"error": str(e)}, sort_keys=False, allow_unicode=True)

@mcp.tool(
    name="patch_ldm",
    description="Patch (update) the title and/or description of a dataset or attribute in the Logical Data Model (LDM). Persists changes."
)
def patch_ldm(object_id: str, title: str = None, description: str = None) -> dict:
    """Patch the title and/or description of a dataset or attribute in the LDM."""
    try:
        # Fetch current LDM
        declarative_ldm = gd.catalog_workspace_content.get_declarative_ldm(workspace_id=GD_WORKSPACE)
        updated = False
        for ds in getattr(declarative_ldm.ldm, "datasets", []):
            if ds.id == object_id:
                if title:
                    ds.title = title
                if description:
                    ds.description = description
                updated = True
                break
            for attr in getattr(ds, "attributes", []):
                if attr.id == object_id:
                    if title:
                        attr.title = title
                    if description:
                        attr.description = description
                    updated = True
                    break
        if updated:
            gd.catalog_workspace_content.put_declarative_ldm(workspace_id=GD_WORKSPACE, ldm=declarative_ldm)
            return {"status": "OK"}
        else:
            return {"error": "Field not found"}
    except Exception as e:
        return {"error": str(e)}

@mcp.tool(
    name="explain_metric",
    description="Explain how a given metric is computed, including its MAQL expression, description, and where it is used across dashboards and insights."
)
def explain_metric(metric_id: str) -> dict:
    """
    Explain how a given metric is computed and where it is used.
    Unfold nested metrics and translate MAQL (not implemented).
    """
    try:
        declarative_analytics = gd.catalog_workspace_content.get_declarative_analytics_model(workspace_id=GD_WORKSPACE)
        metrics = declarative_analytics.analytics.metrics

        # 1. Find MAQL for the metric (try id and local_identifier)
        maql = None
        description = None
        local_identifier = None
        found_metric = None
        for m in metrics:
            if m.id == metric_id or getattr(m, "local_identifier", None) == metric_id:
                maql = m.content.get("maql")
                description = m.description
                found_metric = m
                break

        result_dependencies = gd.catalog_workspace_content.get_dependent_entities_graph_from_entry_points(GD_WORKSPACE, CatalogDependentEntitiesRequest(identifiers=[CatalogEntityIdentifier(id=metric_id, type="metric")]))        
        used_in = [(i.title, i.type) for i in result_dependencies.graph.nodes]
        
        whole_graph = gd.catalog_workspace_content.get_dependent_entities_graph(GD_WORKSPACE)

        uses_ids = [(edge[0].id, edge[0].type) for edge in whole_graph.graph.edges if edge[1].id == metric_id and edge[1].type == "metric"]
        uses = [(i.title, i.type) for i in whole_graph.graph.nodes if (i.id, i.type) in uses_ids]
        # TODO: it would be helpful to fetch uses descriptions
        
        result = {
            "metric_id": metric_id,
            "maql": maql,
            "description": description,
            "usage_total_count": len(used_in),
            "usage_example": used_in[:10],  # limit to 10 usages for brevity
            "uses": uses,
            "uses_total_count": len(uses),
        }
        return yaml.safe_dump(result, sort_keys=False, allow_unicode=True)
    except Exception as e:
        return {"error": str(e)}

@mcp.tool(
    name="search",
    description="Search facts, metrics, attributes, date instances, visualizations or dashboards in the workspace."
)
def search(term: str, types: list[str] = []) -> dict:
    """
    Use the GoodData SDK to search for facts, metrics, attributes, date instances, visualizations or dashboards in the workspace.
    """
    try:
        return {
            "result": [{
                "id": result["id"],
                "title": result["title"],
                "description": result.get("description", None),
                "type": result["type"],
                "visualization_type": result.get("visualization_type", None),
                "match_score": result.get("score", 0.0),
            } for result in gd.compute.search_ai(workspace_id=GD_WORKSPACE, question=term, object_types=types).results]
        }
    except Exception as e:
        return {"error": str(e)}

@mcp.tool(
    name="create_visualization",
    description="Creates a visualization using a prompt and adds it directly to the GoodData workspace. Returns a confirmation and the new visualization's ID."
)
def create_visualization(prompt: str) -> dict:
    """
    Calls the GoodData AI compute engine to create a visualization and adds it to the workspace.
    Returns a confirmation message and the new visualization's ID.
    """
    try:
        result = gd.compute.ai_chat_stream(workspace_id=GD_WORKSPACE, question=prompt)
        visualization = [chunk for chunk in result if "createdVisualizations" in chunk]
        if len(visualization) == 0:
            return {"error": "No visualization object found in AI chat output."}
        visualization = visualization[0].get("createdVisualizations", {})
        visualization_converted = convert(visualization)
        if len(visualization_converted) == 0:
            return {"error": "Conversion failed."}
        declarative_workspace = gd.catalog_workspace.get_declarative_workspace(workspace_id=GD_WORKSPACE)
        if hasattr(declarative_workspace.analytics, "visualization_objects"):
            declarative_workspace.analytics.visualization_objects.append(visualization_converted)
        else:
            declarative_workspace.analytics.visualization_objects = [visualization_converted]
        gd.catalog_workspace.put_declarative_workspace(workspace_id=GD_WORKSPACE, workspace=declarative_workspace)
        
        return {
            "message": f"Visualization '{visualization_converted.get('title')}' added to workspace.",
            "id": visualization_converted.get("id"),
            "url": f"{GD_HOST}/analyze/#/{GD_WORKSPACE}/{visualization_converted['id']}/edit"
        }
    except Exception as e:
        return {"error": str(e)}

@mcp.tool(
    name="add_visualization_to_dashboard",
    description="Add a visualization to a dashboard. Requires the visualization_id and dashboard_id as inputs."
)
def add_visualization_to_dashboard(visualization_id: str, dashboard_id: str) -> str:
    """
    You must provide the visualization_id of an existing visualization (ask for it if not provided). This tool will then place it on the first dashboard. It does not generate or search for the visualization_id itself. Returns a YAML message confirming the visual has been placed in the dashboard.
    """
    try:
        declarative_workspace = gd.catalog_workspace.get_declarative_workspace(workspace_id=GD_WORKSPACE)
        dashboards = getattr(declarative_workspace.analytics, "analytical_dashboards", [])
        if not dashboards:
            return yaml.safe_dump({"error": "No dashboards found in workspace."}, sort_keys=False, allow_unicode=True)
        dashboard = next((d for d in dashboards if d.id == dashboard_id), None)
        if not dashboard:
            return yaml.safe_dump({"error": f"Dashboard {dashboard_id} not found in workspace."}, sort_keys=False, allow_unicode=True)
        layout = dashboard.content.get("layout", {})
        sections = layout.get("sections", [])

        # Use the first item in the first section as a template
        if sections and sections[0]["items"]:
            from copy import deepcopy
            template_item = deepcopy(sections[0]["items"][0])
            # Update only the fields needed for the new visualization
            widget = template_item["widget"]
            widget["insight"]["identifier"]["id"] = visualization_id
            widget["title"] = f"Visualization {visualization_id}"
            # Generate a new unique localIdentifier if present
            if "localIdentifier" in widget:
                widget["localIdentifier"] = str(uuid.uuid4())
            template_item["widget"] = widget
            # Prepend the new item
            sections[0]["items"] = [template_item] + sections[0]["items"]
        else:
            # Fallback: create a minimal valid item if no template exists
            new_item = {
                "size": {"xl": {"gridWidth": 12}},
                "type": "IDashboardLayoutItem",
                "widget": {
                    "type": "insight",
                    "insight": {"identifier": {"id": visualization_id, "type": "visualizationObject"}},
                    "title": f"Visualization {visualization_id}",
                    "localIdentifier": str(uuid.uuid4()),
                    "configuration": {
                        "description": {
                            "includeMetrics": False,
                            "source": "widget",
                            "visible": True
                        },
                        "hideTitle": False
                    },
                    "properties": {}
                }
            }
            sections.append({
                "items": [new_item],
                "type": "IDashboardLayoutSection"
            })
        layout["sections"] = sections
        dashboard.content["layout"] = layout
        gd.catalog_workspace.put_declarative_workspace(workspace_id=GD_WORKSPACE, workspace=declarative_workspace)
        result = {
            "message": f"Visualization {visualization_id} has been placed in the dashboard.",
            "visualization_id": visualization_id,
            "url": f"{GD_HOST}/dashboards/#/workspace/{GD_WORKSPACE}/dashboard/{dashboard_id}"
        }
        return yaml.safe_dump(result, sort_keys=False, allow_unicode=True)
    except Exception as e:
        return yaml.safe_dump({"error": str(e)}, sort_keys=False, allow_unicode=True)

# Reset logging settings that MCP made because we want to use our own logging configuration configured in the bootstrap script
logging.basicConfig(force=True, handlers=[], level=logging.NOTSET)
