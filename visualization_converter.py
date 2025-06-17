

def convert(content: dict) -> dict:
    if len(content["objects"]) == 0:
        return {}
    visualization = content["objects"][0]    
    title = visualization["title"]
    id = visualization["id"]
    visualization_type = visualization["visualizationType"]
    metrics = visualization["metrics"]
    dimensionality = visualization["dimensionality"]
    metrics = {'items': [{"measure": {"definition": {'measureDefinition': {'filters': [], 'item': {'identifier': {'id': metric["id"], 'type': 'metric'}}}}}} for metric in metrics], "localIdentifier": "measures"}
    # This will be different for different visualization types
    view = {'items': [{"attribute": {"definition": {'attributeDefinition': {'filters': [], 'item': {'identifier': {'id': attr["id"], 'type': 'attribute'}}}}}} for attr in list(dimensionality[0])], "localIdentifier": "view"}
    segment = {'items': [{"attribute": {"definition": {'attributeDefinition': {'filters': [], 'item': {'identifier': {'id': attr["id"], 'type': 'attribute'}}}}}} for attr in list(dimensionality[1])], "localIdentifier": "segment"}

    return {
        "content": {
            "visualizationUrl": f"local:{visualization_type.lower()}",
            "filters": [],
            "properties": {},
            "buckets": metrics + view + segment
        },
        "id": id,
        "title": title,
    }