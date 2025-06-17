import random

def convert(content: dict) -> dict:
    if len(content.get("objects", [])) == 0:
        return {}
    visualization = content["objects"][0]    
    title = visualization["title"]
    id = visualization["id"] + "_" + str(random.randint(10000000, 99999999))
    visualization_type = visualization["visualizationType"]
    metrics = visualization["metrics"]
    dimensionality = visualization["dimensionality"]
    metrics = [{'items': [{"measure": {"localIdentifier": str(random.randint(10000000, 99999999)), "definition": {'measureDefinition': {'filters': [], 'item': {'identifier': {'id': metric["id"], 'type': 'metric'}}}}, "title": metric["title"]}} for metric in metrics], "localIdentifier": "measures"}]
    # This will be different for different visualization types
    view = []
    stack = []
        
    if len(dimensionality) == 1:
        view = [{'items': [{"attribute": {"localIdentifier": str(random.randint(10000000, 99999999)), "displayForm": {'identifier': {'id': dimensionality[0]["id"], 'type': 'label'}}}}], "localIdentifier": "view"}]
    elif len(dimensionality) == 2:
        view = [{'items': [{"attribute": {"localIdentifier": str(random.randint(10000000, 99999999)), "displayForm": {'identifier': {'id': dimensionality[0]["id"], 'type': 'label'}}}}], "localIdentifier": "view"}]
        stack = [{'items': [{"attribute": {"localIdentifier": str(random.randint(10000000, 99999999)), "displayForm": {'identifier': {'id': dimensionality[1]["id"], 'type': 'label'}}}}], "localIdentifier": "stack"}]
    else:
        view = []
        stack = []
    
    return {
        "content": {
            "visualizationUrl": f"local:{visualization_type.lower()}",
            "filters": [],
            "properties": {},
            "buckets": metrics + view + stack,
            "version": "2"
        },
        "id": id,
        "title": title,
    }