import json
with open('assets/levels/world1-1.json') as f:
    data = json.load(f)

print('=== tilesetEditing structure ===')
for i, item in enumerate(data['tilesetEditing']):
    print(f'  Item {i}: keys={list(item.keys())}')
    if 'layers' in item:
        for layer in item['layers']:
            print(f'    Layer: id={layer.get("layerId")}, name={layer.get("name")}, visible={layer.get("visible")}, locked={layer.get("locked")}, tiles={len(layer.get("tiles", {}))}')

print()
print('=== Sample tile data (Layer 5) ===')
layer5 = None
for item in data['tilesetEditing']:
    if 'layers' in item:
        for layer in item['layers']:
            if layer.get('layerId') == 5:
                layer5 = layer
                break

if layer5 and 'tiles' in layer5:
    tiles = layer5['tiles']
    print(f'Total tiles: {len(tiles)}')
    print()
    print('First 5 tiles:')
    for key, val in list(tiles.items())[:5]:
        print(f'  {key}: {val}')

print()
print('=== Sample tile data (Layer 1) ===')
layer1 = None
for item in data['tilesetEditing']:
    if 'layers' in item:
        for layer in item['layers']:
            if layer.get('layerId') == 1:
                layer1 = layer
                break

if layer1 and 'tiles' in layer1:
    tiles = layer1['tiles']
    print(f'Total tiles: {len(tiles)}')
    print('First 5 tiles:')
    for key, val in list(tiles.items())[:5]:
        print(f'  {key}: {val}')