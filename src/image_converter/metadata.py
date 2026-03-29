"""Metadata extraction and injection handlers.

Provides operation handlers for metadata flags (view, export, strip, copy, set, update, etc.).
"""

import json
import os
from pathlib import Path
from PIL import Image

import piexif
from rich.console import Console

console = Console()

# ---------------------------------------------------------
# Mapping and Type Definitions
# ---------------------------------------------------------

def build_reverse_exif_map() -> dict:
    """Invert piexif.TAGS to a human-readable dictionary with types and IFDs.

    Returns:
        dict: A dictionary mapping human-readable EXIF tag names to a dict
              containing their IFD (e.g., "0th", "Exif"), ID (int), and type.
    """
    reverse_map = {}
    # piexif.TAGS contains "Image", which maps to "0th" in the actual dicts
    ifd_mapping = {
        "Image": "0th",
        "Exif": "Exif",
        "GPS": "GPS",
        "Interop": "Interop",
        "0th": "0th",
        "1st": "1st"
    }

    for piexif_ifd_name, tags in piexif.TAGS.items():
        ifd_name = ifd_mapping.get(piexif_ifd_name, piexif_ifd_name)
        for tag_id, tag_info in tags.items():
            tag_name = tag_info["name"]
            tag_type = tag_info.get("type")
            # Prefer 0th for overlaps (like ImageWidth/ImageLength)
            if tag_name not in reverse_map or (ifd_name == "0th" and reverse_map[tag_name]["ifd"] != "0th"):
                reverse_map[tag_name] = {"ifd": ifd_name, "id": tag_id, "type": tag_type}
    return reverse_map

REVERSE_EXIF_MAP = build_reverse_exif_map()

def _get_type_name(type_id: int) -> str:
    """Convert piexif type ID to a readable string."""
    return {
        piexif.TYPES.Byte: "Byte",
        piexif.TYPES.Ascii: "Ascii",
        piexif.TYPES.Short: "Short",
        piexif.TYPES.Long: "Long",
        piexif.TYPES.Rational: "Rational",
        piexif.TYPES.Undefined: "Undefined",
        piexif.TYPES.SLong: "SLong",
        piexif.TYPES.SRational: "SRational",
    }.get(type_id, "Unknown")

def cast_exif_value(tag_name: str, value: str):
    """Securely convert user string inputs into EXIF-compatible types based on REVERSE_EXIF_MAP.

    Args:
        tag_name (str): The EXIF tag name (e.g., "XResolution").
        value (str): The string value to convert.

    Returns:
        The cast value compatible with piexif, or raises ValueError.
    """
    if value == "None" or value is None:
        return None

    tag_info = REVERSE_EXIF_MAP.get(tag_name)
    if not tag_info:
        raise ValueError(f"Unknown EXIF tag: '{tag_name}'")

    t = tag_info["type"]
    try:
        if t == piexif.TYPES.Ascii:
            return value.encode("utf-8")
        elif t in (piexif.TYPES.Short, piexif.TYPES.Long, piexif.TYPES.SLong, piexif.TYPES.Byte):
            return int(value)
        elif t in (piexif.TYPES.Rational, piexif.TYPES.SRational):
            if "/" in value:
                num, den = value.split("/")
                return (int(num), int(den))
            else:
                return (int(value), 1)
        elif t == piexif.TYPES.Undefined:
            return value.encode("utf-8")
        else:
            return value.encode("utf-8")
    except Exception as e:
        type_str = _get_type_name(t)
        raise ValueError(f"Failed to cast '{value}' for tag '{tag_name}' (expected type: {type_str}). Error: {e}")

# ---------------------------------------------------------
# Data Abstraction & Parsing
# ---------------------------------------------------------

def load_exif_as_flat_dict(exif_bytes: bytes) -> dict:
    """Load raw EXIF bytes and convert to a flat, human-readable dictionary."""
    if not exif_bytes or exif_bytes == b"Exif\x00\x00":
        return {}

    try:
        exif_dict = piexif.load(exif_bytes)
    except Exception:
        return {}

    flat_dict = {}
    for ifd_name, tags in exif_dict.items():
        if ifd_name == "thumbnail":
            continue
        for tag_id, value in tags.items():
            tag_name = piexif.TAGS[ifd_name].get(tag_id, {}).get("name", f"Unknown_{ifd_name}_{tag_id}")
            # Try to decode bytes for Ascii types
            if isinstance(value, bytes):
                try:
                    # Clean up null terminators
                    val_str = value.decode("utf-8").rstrip("\x00")
                    flat_dict[tag_name] = val_str
                except Exception:
                    # Keep raw bytes repr or ignore if too complex for JSON
                    flat_dict[tag_name] = str(value)
            elif isinstance(value, tuple) and len(value) == 2 and isinstance(value[0], int) and isinstance(value[1], int):
                # Format rational
                flat_dict[tag_name] = f"{value[0]}/{value[1]}"
            else:
                flat_dict[tag_name] = value

    return flat_dict

def dict_to_exif_bytes(flat_dict: dict, base_exif_dict: dict = None) -> bytes:
    """Convert a flat human-readable dictionary to EXIF bytes using piexif."""
    exif_dict = base_exif_dict if base_exif_dict else {"0th": {}, "Exif": {}, "GPS": {}, "Interop": {}, "1st": {}, "thumbnail": None}

    for key, value in flat_dict.items():
        if value is None or value == "None":
            # Remove key if it exists
            tag_info = REVERSE_EXIF_MAP.get(key)
            if tag_info:
                if tag_info["ifd"] in exif_dict and tag_info["id"] in exif_dict[tag_info["ifd"]]:
                    del exif_dict[tag_info["ifd"]][tag_info["id"]]
            continue

        try:
            tag_info = REVERSE_EXIF_MAP.get(key)
            if not tag_info:
                console.print(f"[yellow]Warning: Unknown EXIF tag '{key}', skipping.[/]")
                continue

            cast_val = cast_exif_value(key, value)

            # Use appropriate IFD name fallback to match piexif dict format
            ifd_name = tag_info["ifd"]
            if ifd_name not in exif_dict:
                exif_dict[ifd_name] = {}
            exif_dict[ifd_name][tag_info["id"]] = cast_val
        except ValueError as e:
            console.print(f"[red]Error parsing tag '{key}': {e}[/]")
            # Skip invalid tags rather than crashing

    try:
        return piexif.dump(exif_dict)
    except Exception as e:
        console.print(f"[red]Error building EXIF bytes: {e}[/]")
        return b""

def parse_metadata_input(values: list[str]) -> dict:
    """Parse CLI input list into a flat dictionary.

    Handles:
    - JSON file path: ["tags.json"]
    - Inline JSON: ['{"Artist": "Jane Doe"}']
    - Key=Value pairs: ["Artist=Jane Doe", "Copyright=2026"]
    """
    if not values:
        return {}

    # Check 1: File
    if len(values) == 1 and values[0].lower().endswith(".json"):
        try:
            with open(values[0], "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            console.print(f"[red]Error reading JSON file: {e}[/]")
            return {}

    # Check 2: Inline JSON
    if len(values) == 1 and values[0].startswith("{"):
        try:
            return json.loads(values[0])
        except Exception as e:
            console.print(f"[red]Error parsing inline JSON: {e}[/]")
            return {}

    # Check 3: Key=Value pairs
    result = {}
    for val in values:
        if "=" in val:
            k, v = val.split("=", 1)
            result[k.strip()] = v.strip()
        else:
            console.print(f"[red]Invalid metadata input format: '{val}'. Expected Key=Value, JSON string, or .json file.[/]")
    return result

# ---------------------------------------------------------
# Handlers
# ---------------------------------------------------------

def handle_view_metadata(image: Image.Image, image_name: str, values: list, args) -> Image.Image:
    """Print the existing metadata to the console."""
    console.print(f"  [bright_yellow]›[/] [yellow]Viewing metadata for {image_name}...[/]")

    info = image.info
    exif_bytes = info.get("exif", b"")

    flat_exif = load_exif_as_flat_dict(exif_bytes)

    if not flat_exif:
        console.print("      [dim white]No EXIF metadata found.[/]")
    else:
        for k, v in flat_exif.items():
            console.print(f"      [cyan]{k}[/]: [white]{v}[/]")

    return image

def handle_export_metadata(image: Image.Image, image_name: str, values: list, args) -> Image.Image:
    """Export the image's existing metadata to be collected into a JSON file."""
    console.print(f"  [bright_yellow]›[/] [yellow]Exporting metadata for {image_name}...[/]")

    info = image.info
    exif_bytes = info.get("exif", b"")
    flat_exif = load_exif_as_flat_dict(exif_bytes)

    # We store the flat dict in a global/args structure to dump after all images are processed
    if not hasattr(args, "metadata_manifest"):
        args.metadata_manifest = {}

    args.metadata_manifest[image_name] = flat_exif

    # Store the requested file path in args if one was provided
    if values and values[0]:
        args.export_metadata_path = values[0]

    return image

def handle_strip_metadata(image: Image.Image, image_name: str, values: list, args) -> Image.Image:
    """Remove privacy metadata but preserve critical structural data (ICC, DPI, Orientation)."""
    console.print(f"  [bright_yellow]›[/] [yellow]Stripping metadata for {image_name}...[/]")

    # Preserve must-haves
    preserve_keys = ["icc_profile", "dpi", "transparency", "loop", "duration"]
    new_info = {k: image.info[k] for k in preserve_keys if k in image.info}

    # Preserve Orientation from EXIF if it exists
    exif_bytes = image.info.get("exif", b"")
    if exif_bytes and exif_bytes != b"Exif\x00\x00":
        try:
            exif_dict = piexif.load(exif_bytes)
            orientation = exif_dict.get("0th", {}).get(piexif.ImageIFD.Orientation)
            if orientation is not None:
                new_exif = {"0th": {piexif.ImageIFD.Orientation: orientation}, "Exif": {}, "GPS": {}, "Interop": {}, "1st": {}, "thumbnail": None}
                new_info["exif"] = piexif.dump(new_exif)
        except Exception:
            pass

    # Modify the image info in place or create a copy to prevent side effects on the original dictionary
    image.info = new_info
    return image

def handle_copy_metadata(image: Image.Image, image_name: str, values: list, args) -> Image.Image:
    """Extract metadata from a specified source image and apply it to the current image."""
    source_path = values[0] if values else None
    if not source_path:
        console.print("  [bright_red]✗[/] [red]Source file path required for --copy-metadata.[/]")
        return image

    console.print(f"  [bright_yellow]›[/] [yellow]Copying metadata from '{source_path}'...[/]")

    # Cache the source EXIF in args to prevent reloading it for every image in a batch
    if not hasattr(args, "cached_source_exif"):
        try:
            with Image.open(source_path) as src_img:
                args.cached_source_exif = src_img.info.get("exif", b"")
        except Exception as e:
            console.print(f"  [bright_red]✗[/] [red]Failed to open source image '{source_path}': {e}[/]")
            args.cached_source_exif = b""

    if args.cached_source_exif:
        image.info["exif"] = args.cached_source_exif

    return image

def handle_set_metadata(image: Image.Image, image_name: str, values: list, args) -> Image.Image:
    """Overwrite the image's metadata completely with the provided input."""
    console.print(f"  [bright_yellow]›[/] [yellow]Setting metadata for {image_name}...[/]")

    input_dict = parse_metadata_input(values)
    if not input_dict:
        return image

    # Complete overwrite: Start with a blank EXIF dict
    new_exif_bytes = dict_to_exif_bytes(input_dict)
    if new_exif_bytes:
        image.info["exif"] = new_exif_bytes

    return image

def handle_update_metadata(image: Image.Image, image_name: str, values: list, args) -> Image.Image:
    """Merge the provided input with the image's existing metadata."""
    console.print(f"  [bright_yellow]›[/] [yellow]Updating metadata for {image_name}...[/]")

    input_dict = parse_metadata_input(values)
    if not input_dict:
        return image

    existing_exif_bytes = image.info.get("exif", b"")
    base_exif_dict = None
    if existing_exif_bytes and existing_exif_bytes != b"Exif\x00\x00":
        try:
            base_exif_dict = piexif.load(existing_exif_bytes)
        except Exception:
            pass

    new_exif_bytes = dict_to_exif_bytes(input_dict, base_exif_dict)
    if new_exif_bytes:
        image.info["exif"] = new_exif_bytes

    return image

def handle_author(image: Image.Image, image_name: str, values: list, args) -> Image.Image:
    """Quick-access flag to set the Author/Artist tag."""
    author_name = values[0] if values else ""
    console.print(f"  [bright_yellow]›[/] [yellow]Setting Author to '{author_name}'...[/]")

    # We create a list of strings "Artist=..." and reuse update logic
    if not hasattr(args, "_author_handled_once"):
        args._author_handled_once = True
    return handle_update_metadata(image, image_name, [f"Artist={author_name}"], args)

def handle_copyright(image: Image.Image, image_name: str, values: list, args) -> Image.Image:
    """Quick-access flag to set the Copyright tag."""
    copyright_text = values[0] if values else ""
    console.print(f"  [bright_yellow]›[/] [yellow]Setting Copyright to '{copyright_text}'...[/]")

    return handle_update_metadata(image, image_name, [f"Copyright={copyright_text}"], args)
