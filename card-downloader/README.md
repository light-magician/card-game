# downloading card data

2 there are 2 separate scripts for card metadata and card images

```bash
python3 -m venv .venv # create an isolated interpreter
source .venv/bin/activate # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python3 download_metadata.py # metadata
python3 download_images.py # images
```

card_metadata.json is zipped

```bash
# turn cardinfo.json.zst → cardinfo.json
zstd -d cardinfo.json.zst
# turn cardinfo.json → cardinfo.json.zst using max compression
zstd -19 cardinfo.json -o cardinfo.json.zst
```
