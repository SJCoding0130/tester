import os
import json
import yaml
from PIL import Image
import datetime
import traceback

# ===== CONFIG =====
SOURCE_DIR = os.path.join(os.getcwd(), "filtered_assets")
OUTPUT_BASE = os.path.join(os.getcwd(), "result")
LOG_FILE = "reconstruct_log.txt"

# ===== LOGGER =====
def log(msg):
    print(msg)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{datetime.datetime.now()}: {msg}\n")


# ===== UNITY YAML LOADER =====
class UnityLoader(yaml.SafeLoader):
    pass


def unity_multi_constructor(loader, tag_suffix, node):
    if isinstance(node, yaml.MappingNode):
        return loader.construct_mapping(node)
    elif isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node)
    else:
        return loader.construct_scalar(node)


UnityLoader.add_multi_constructor('', unity_multi_constructor)


# ===== SMART cellIndexList parser =====
def parse_cell_index_list(data, asset_path=None, texture_name=None):
    if isinstance(data, list):
        return [int(x) for x in data]
    
    if isinstance(data, int):
        data = str(data)

    if isinstance(data, str):
        values = []
        for i in range(0, len(data), 8):
            chunk = data[i:i + 8]
            if len(chunk) < 8:
                continue
            value = int.from_bytes(bytes.fromhex(chunk), byteorder="little")
            values.append(value)
        return values

    # 👇 NEW: detailed error
    raise ValueError(
        f"Unsupported cellIndexList format in file '{asset_path}', "
        f"texture '{texture_name}': type={type(data)}, value={data}"
    )


# ===== MAIN PROCESS =====
def process_asset(asset_path, atlas_path):
    base_name = os.path.splitext(os.path.basename(atlas_path))[0]
    output_dir = os.path.join(OUTPUT_BASE, base_name)
    os.makedirs(output_dir, exist_ok=True)

    atlas = Image.open(atlas_path)
    atlas_w, atlas_h = atlas.size

    with open(asset_path, "r", encoding="utf-8") as f:
        data = yaml.load(f, Loader=UnityLoader)

    if isinstance(data, list):
        data = data[0]

    atlas_def = data.get("MonoBehaviour") or data.get("m_Structure") or data.get("Structure")

    if not atlas_def:
        log(f" Could not parse structure in {asset_path}")
        return

    cell_size = atlas_def["cellSize"]
    padding = atlas_def["padding"]
    transparent_index = atlas_def.get("transparentIndex", 0)

    inner_size = cell_size - 2 * padding
    atlas_cols = atlas_w // cell_size

    log(f"Processing {asset_path} with atlas {atlas_path}")

    for textureData in atlas_def["textureDataList"]:
        name = textureData["name"]
        tex_w = textureData["width"]
        tex_h = textureData["height"]

        try:
          cellIndexList = parse_cell_index_list(
              textureData["cellIndexList"],
              asset_path=asset_path,
              texture_name=name
          )
        except Exception as e:
            log(f"ERROR while parsing cellIndexList in {asset_path}, texture '{name}'")
            log(str(e))
            continue  # or use `raise` if you want it to stop execution

        canvas_w = ((tex_w + inner_size - 1) // inner_size) * inner_size
        canvas_h = ((tex_h + inner_size - 1) // inner_size) * inner_size

        out_img = Image.new("RGBA", (tex_w, tex_h), (0, 0, 0, 0))

        cells_per_row = canvas_w // inner_size

        for i, cellIndex in enumerate(cellIndexList):
            if cellIndex == transparent_index:
                continue

            dest_x = (i % cells_per_row) * inner_size
            dest_y = canvas_h - inner_size * (1 + (i // cells_per_row)) - (canvas_h - tex_h)

            src_col = cellIndex % atlas_cols
            src_row = cellIndex // atlas_cols

            src_x = src_col * cell_size + padding
            src_y = atlas_h - cell_size * (1 + src_row) + padding

            cell = atlas.crop((src_x, src_y, src_x + inner_size, src_y + inner_size))
            out_img.paste(cell, (dest_x, dest_y), cell)

        out_path = os.path.join(output_dir, f"{name}.png")
        out_img.save(out_path)
        log(f"Saved {out_path}")


if __name__ == "__main__":
    try:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write("=== Reconstruction started ===\n")

        if not os.path.exists(SOURCE_DIR):
            log(f" Source folder not found: {SOURCE_DIR}")
            exit(1)

        assets = [f for f in os.listdir(SOURCE_DIR) if f.endswith(".asset")]

        if not assets:
            log("No .asset files found.")
            #exit(0)

        for asset_file in assets:
            asset_path = os.path.join(SOURCE_DIR, asset_file)
            base = os.path.splitext(asset_path)[0]

            atlas0 = base + "_Atlas0.png"
            atlas_plain = base + ".png"

            if os.path.exists(atlas0):
                atlas_path = atlas0
            elif os.path.exists(atlas_plain):
                atlas_path = atlas_plain
            else:
                log(f" No atlas PNG found for {asset_file}")
                continue

            process_asset(asset_path, atlas_path)

        # === FORCE INCLUDE PNG (no processing) ===
        extra_png = os.path.join(SOURCE_DIR, "bg_title_newyear2017.png")

        if os.path.exists(extra_png):
            out_dir = os.path.join(OUTPUT_BASE, "extra")
            os.makedirs(out_dir, exist_ok=True)

            out_path = os.path.join(out_dir, "bg_title_newyear2017.png")

            with open(extra_png, "rb") as src, open(out_path, "wb") as dst:
                dst.write(src.read())

            log(f"Copied extra PNG without processing: {out_path}")
        else:
            log("Extra PNG not found: bg_title_newyear2017.png")
        log("=== All done ===")

    except Exception:
        traceback.print_exc()
        exit(1)
