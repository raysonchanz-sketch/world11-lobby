import json
with open('assets/levels/world1-1.json') as f:
    data = json.load(f)

te = data['tilesetEditing']
for layer in te[0]['layers']:
    if 'tiles' in layer:
        tiles = layer['tiles']
        xs = []
        ys = []
        for key, val in tiles.items():
            xs.append(val['x'])
            ys.append(val['y'])
        print(f'Layer {layer.get("layerId")} ({layer.get("name")}): x={min(xs)}-{max(xs)}, y={min(ys)}-{max(ys)}')