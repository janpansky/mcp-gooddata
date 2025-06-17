import logging
import os
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
import yaml
from gooddata_sdk import GoodDataSdk
from ldm_quality_check import has_no_description, obfuscated_title_check, semantic_similarity_check

# Load environment variables from .env file
load_dotenv()

# Initialize the MCP server
mcp = FastMCP("Demo")

# Initialize GoodData SDK using environment variables for host and token
GD_HOST = os.environ.get("GOODDATA_HOST")
GD_TOKEN = os.environ.get("GOODDATA_TOKEN")
GD_WORKSPACE = os.environ.get("GOODDATA_WORKSPACE")
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
                    missing_descriptions_attributes.append(attr.title)
                obfuscated_title_result =  obfuscated_title_check(attr)
                if obfuscated_title_result.is_obfuscated:
                    obfuscated_title_attributes.append((attr.title, obfuscated_title_result.reason))
            for fact in ds.facts:
                if has_no_description(fact):
                    missing_descriptions_facts.append(fact.title)
                obfuscated_title_result =  obfuscated_title_check(fact)
                if obfuscated_title_result.is_obfuscated:
                    obfuscated_title_facts.append((fact.title, obfuscated_title_result.reason))
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
                            "field_description": getattr(attr, "description", None)
                        }
                        break
        # Sample data (placeholder: GoodData SDK does not support direct DB sampling)
        sample_data = []
        # TODO: Integrate with DB or use GoodData API to fetch sample data if possible
        result = {"field_meta": field_meta, "sample_data": sample_data}
        return yaml.safe_dump(result, sort_keys=False, allow_unicode=True)
    except Exception as e:
        return yaml.safe_dump({"error": str(e)}, sort_keys=False, allow_unicode=True)

@mcp.tool(
    name="patch_ldm",
    description="Patch (update) the title and/or description of a dataset or attribute in the Logical Data Model (LDM). Persists changes."
)
def patch_ldm(object_type: str, object_id: str, title: str = None, description: str = None) -> dict:
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
            for attr in getattr(ds, "attributes", []):
                if attr.id == object_id:
                    if title:
                        attr.title = title
                    if description:
                        attr.description = description
                    updated = True
                for attr in getattr(ds, "attributes", []):
                    if attr.id == field_id:
                        attr.title = new_title
                        attr.description = new_description
                        updated = True
        if updated:
            gd.catalog_workspace_content.put_declarative_ldm(workspace_id=GD_WORKSPACE, ldm=declarative_ldm.ldm)
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
        metrics = getattr(declarative_analytics.analytics, "metrics", [])
        dashboards = getattr(declarative_analytics.analytics, "analytical_dashboards", [])
        insights = getattr(declarative_analytics.analytics, "visualization_objects", [])

        # 1. Find MAQL for the metric (try id and local_identifier)
        maql = None
        description = None
        local_identifier = None
        found_metric = None
        for m in metrics:
            if m.id == metric_id or getattr(m, "local_identifier", None) == metric_id:
                # Try top-level maql, then content['maql']
                maql = getattr(m, "maql", None)
                if not maql:
                    maql = getattr(m, "content", {}).get("maql")
                # Try top-level description, then content['description']
                description = getattr(m, "description", None)
                if not description:
                    description = getattr(m, "content", {}).get("description")
                local_identifier = getattr(m, "local_identifier", None)
                found_metric = m
                break

        # 1b. If not found, try to find in referenced insights
        debug_info = {}
        if maql is None:
            # Collect all insight ids from usage
            referenced_insight_ids = set()
            for dashboard in dashboards:
                content = getattr(dashboard, "content", {})
                layout = content.get("layout", {})
                sections = layout.get("sections", [])
                for section in sections:
                    for item in section.get("items", []):
                        widget = item.get("widget", {})
                        insight = widget.get("insight", {})
                        if insight:
                            iid = insight.get("identifier", {}).get("id")
                            if iid:
                                referenced_insight_ids.add(iid)
            # Search these insights for a measure with matching id/local_identifier
            for insight in insights:
                if getattr(insight, "id", None) in referenced_insight_ids:
                    content = getattr(insight, "content", {})
                    measures = content.get("measures", [])
                    for measure in measures:
                        # Try id, localIdentifier, and definition
                        if (
                            measure.get("id") == metric_id or
                            measure.get("localIdentifier") == metric_id or
                            measure.get("definition", {}).get("metric", {}).get("id") == metric_id
                        ):
                            maql = measure.get("definition", {}).get("metric", {}).get("expression")
                            if not maql:
                                maql = measure.get("maql")
                            local_identifier = measure.get("localIdentifier")
                            debug_info["found_in_insight"] = insight.id
                            break
                    if maql:
                        break
            if maql is None:
                debug_info["all_metric_ids"] = [getattr(m, "id", None) for m in metrics]
                debug_info["all_metric_local_identifiers"] = [getattr(m, "local_identifier", None) for m in metrics]

        # 2. Find usage in dashboards/insights
        usage = []
        for dashboard in dashboards:
            dashboard_title = getattr(dashboard, "title", None)
            dashboard_id = getattr(dashboard, "id", None)
            content = getattr(dashboard, "content", {})
            layout = content.get("layout", {})
            sections = layout.get("sections", [])
            for section in sections:
                for item in section.get("items", []):
                    widget = item.get("widget", {})
                    # 1. Insight widgets
                    insight = widget.get("insight", {})
                    if insight:
                        usage.append({
                            "dashboard_id": dashboard_id,
                            "dashboard_title": dashboard_title,
                            "widget_title": widget.get("title"),
                            "insight_id": insight.get("identifier", {}).get("id"),
                        })
                    # 2. Drills from measure
                    for drill in widget.get("drills", []):
                        origin = drill.get("origin", {})
                        measure = origin.get("measure", {})
                        if measure and (
                            measure.get("localIdentifier") == local_identifier or
                            measure.get("localIdentifier") == metric_id
                        ):
                            usage.append({
                                "dashboard_id": dashboard_id,
                                "dashboard_title": dashboard_title,
                                "widget_title": widget.get("title"),
                                "drill_type": drill.get("type"),
                                "drill_origin_measure": measure.get("localIdentifier"),
                            })

        explanation = f"MAQL: {maql}\n(Translation to plain English not implemented)"

        result = {
            "metric_id": metric_id,
            "maql": maql,
            "description": description,
            "explanation": explanation,
            "usage": usage[:10],  # limit to 10 usages for brevity
        }
        if debug_info:
            result["debug_info"] = debug_info
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

# Reset logging settings that MCP made because we want to use our own logging configuration configured in the bootstrap script
logging.basicConfig(force=True, handlers=[], level=logging.NOTSET)
