from image_converter.metadata import cast_exif_value, parse_metadata_input

def test_benchmark_cast_exif_value(benchmark):
    """Benchmark casting strings to EXIF values."""
    benchmark(cast_exif_value, "XResolution", "72/1")

def test_benchmark_parse_metadata_input(benchmark):
    """Benchmark parsing Key=Value inputs."""
    benchmark(parse_metadata_input, ["Artist=Jane Doe", "Copyright=2026", "Make=Canon"])
