# Docling Configuration Evaluator

A comprehensive testing framework for evaluating different [Docling](https://github.com/DS4SD/docling) configurations to find optimal settings for PDF document conversion, with a focus on table extraction, image processing, and OCR capabilities.

## Overview

This repository provides two main tools:

1. **`docling_test.py`** - A flexible document converter with extensive configuration options
2. **`run_configurations.py`** - An automated test runner that evaluates multiple configurations

The framework helps you identify the best Docling settings for your specific PDF documents by systematically testing different combinations of:
- Table cell matching strategies
- OCR engines and settings
- Image extraction modes
- AI-powered image descriptions
- Page thumbnail generation

## Features

- 🔄 **Automated Configuration Testing** - Run 11 pre-configured test scenarios automatically
- 📊 **Table Extraction Optimization** - Compare cell matching vs. structure prediction approaches
- 🖼️ **Image Processing** - Extract figures, generate thumbnails, and create AI descriptions
- 🔍 **OCR Support** - Test multiple OCR engines (Auto, EasyOCR, RapidOCR, Tesseract, macOS Vision)
- 📝 **Multiple Output Formats** - Generate Markdown, JSON, and extracted images
- 📈 **Detailed Reporting** - Automatic generation of comparison reports
- ⚡ **Progress Tracking** - Real-time progress updates with time estimates

## Installation

### Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) package manager (recommended) or pip

### Setup

1. Clone this repository:
```bash
git clone <repository-url>
cd docling_config_evals
```

2. Install dependencies using uv:
```bash
uv sync
```

Or using pip:
```bash
pip install docling docling-core
```

### Optional OCR Dependencies

For OCR functionality, install additional packages:

```bash
# EasyOCR
pip install easyocr

# RapidOCR
pip install rapidocr-onnxruntime

# Tesseract (requires system installation)
# macOS: brew install tesseract
# Ubuntu: apt-get install tesseract-ocr
pip install pytesseract
```

## Usage

### Quick Start: Automated Configuration Testing

Run all 11 pre-configured tests on your PDF:

```bash
python run_configurations.py your_document.pdf
```

With custom output directory:

```bash
python run_configurations.py your_document.pdf ./my_results
```

This will:
1. Run 11 different configuration scenarios
2. Generate output files for each configuration
3. Create a comprehensive comparison report
4. Show progress and time estimates

### Single Document Conversion

Convert a single document with specific settings:

```bash
# Basic conversion
python docling_test.py document.pdf

# With image extraction
python docling_test.py document.pdf --generate-picture-images --image-mode referenced

# With OCR enabled
python docling_test.py document.pdf --enable-ocr --ocr-engine easyocr

# With AI image descriptions
python docling_test.py document.pdf --generate-picture-images --picture-description --image-mode referenced

# Convert from URL
python docling_test.py https://arxiv.org/pdf/2408.09869
```

## Configuration Options

### Table Processing

- `--table-cell-matching [true|false]` - Enable/disable PDF cell mapping
  - `true`: Maps table structure back to PDF cells (default)
  - `false`: Uses structure prediction from ML models (may fix merged column issues)

### OCR Settings

- `--enable-ocr` - Enable OCR for text extraction from images
- `--ocr-engine [auto|easyocr|rapidocr|tesseract|mac]` - Choose OCR engine
  - `auto`: Automatic engine selection (default)
  - `easyocr`: EasyOCR engine (good quality, slower)
  - `rapidocr`: RapidOCR engine (fast, good quality)
  - `tesseract`: Tesseract OCR (requires system installation)
  - `mac`: macOS Vision framework (macOS only)
- `--enable-remote-services` - Enable remote OCR services

### Image Processing

- `--generate-picture-images` - Extract figure/picture images from PDF
- `--generate-page-images` - Generate full-page thumbnails
- `--images-scale [float]` - Resolution scale for images (default: 2.0, higher = better quality)
- `--image-mode [placeholder|embedded|referenced]` - Image export mode
  - `placeholder`: HTML comments only
  - `embedded`: Base64-encoded images in markdown
  - `referenced`: Separate image files with references

### AI Image Descriptions

- `--picture-description` - Enable AI-powered image descriptions using VLM
- `--picture-description-prompt [text]` - Custom prompt for image descriptions

### Output Options

- `--output-dir [path]` - Output directory (default: ./output)
- `--no-print` - Skip printing markdown to stdout
- `--config-name [name]` - Append name to output files for tracking

## Pre-configured Test Scenarios

The `run_configurations.py` script includes 11 carefully designed test scenarios:

| Configuration | Description | Purpose |
|--------------|-------------|---------|
| `baseline` | Default settings with image extraction | Baseline for comparison |
| `no_cell_matching` | Disable cell matching | Fix merged column issues |
| `ocr_auto` | OCR with auto engine selection | Extract text from images |
| `ocr_no_cell_matching` | OCR + structure prediction | Combine OCR with better table handling |
| `ocr_easyocr` | EasyOCR engine | Test EasyOCR quality |
| `ocr_mac` | macOS Vision OCR | Test macOS-specific OCR |
| `ocr_remote_services` | Remote OCR services | Test cloud-based OCR |
| `images_with_descriptions` | AI image descriptions | Generate image captions |
| `ocr_with_descriptions` | OCR + AI descriptions | Comprehensive image analysis |
| `full_page_thumbnails` | Page thumbnails + images | Complete visual documentation |
| `ocr_easyocr_with_descriptions` | EasyOCR + AI descriptions | Best of both worlds |

## Output Files

### Per Configuration

Each configuration generates:

- `{document}_{config_name}.md` - Markdown output with formatted content
- `{document}_{config_name}.json` - Full JSON document structure
- `{document}_{config_name}_artifacts/images/` - Extracted images (when using `referenced` mode)

### Summary Report

After running all configurations, a comprehensive report is generated:

- `configuration_test_report.md` - Detailed comparison report including:
  - Summary table of all configurations
  - Success/failure status for each
  - Configuration parameters
  - Evaluation criteria

## Evaluation Criteria

When comparing outputs, consider:

### Table Quality
- ✅ Correct column headers
- ✅ Proper column order
- ✅ Cell alignment and merging
- ✅ Data accuracy

### Image Extraction
- ✅ All figures extracted
- ✅ Image quality and resolution
- ✅ Correct image references in markdown
- ✅ AI descriptions accuracy (if enabled)

### OCR Quality
- ✅ Text extraction accuracy
- ✅ Handling of special characters
- ✅ Layout preservation

### Overall Structure
- ✅ Document hierarchy (headings, sections)
- ✅ Markdown formatting
- ✅ Completeness of content

## Examples

### Example 1: Find Best Table Extraction Settings

```bash
# Run all configurations
python run_configurations.py sample-tables.pdf ./table_tests

# Review the report
cat ./table_tests/configuration_test_report.md

# Compare specific configurations
diff ./table_tests/sample-tables_baseline.md ./table_tests/sample-tables_no_cell_matching.md
```

### Example 2: Optimize Image Extraction

```bash
# Test image extraction with different settings
python docling_test.py document.pdf --generate-picture-images --image-mode referenced --images-scale 3.0

# Test with AI descriptions
python docling_test.py document.pdf --generate-picture-images --picture-description --image-mode referenced
```

### Example 3: OCR Comparison

```bash
# Compare different OCR engines
python docling_test.py scanned.pdf --enable-ocr --ocr-engine easyocr --config-name easyocr
python docling_test.py scanned.pdf --enable-ocr --ocr-engine rapidocr --config-name rapidocr
python docling_test.py scanned.pdf --enable-ocr --ocr-engine tesseract --config-name tesseract
```

## Advanced Usage

### Custom Configuration

Create your own configuration by modifying `CONFIGURATIONS` in `run_configurations.py`:

```python
{
    "name": "my_custom_config",
    "description": "Custom configuration for my use case",
    "args": {
        "table_cell_matching": False,
        "enable_ocr": True,
        "ocr_engine": "easyocr",
        "enable_remote_services": False,
        "generate_picture_images": True,
        "generate_page_images": False,
        "images_scale": 3.0,
        "image_mode": "referenced",
        "picture_description": True,
        "picture_description_prompt": "Describe this technical diagram in detail.",
    },
    "rationale": "Optimized for technical documents with diagrams",
}
```

### Programmatic Usage

Use `docling_test.py` functions in your own scripts:

```python
from docling_test import build_pipeline_options, convert_document_sdk
from pathlib import Path

# Build custom pipeline options
pipeline_options = build_pipeline_options(
    table_cell_matching=False,
    enable_ocr=True,
    ocr_engine="easyocr",
    generate_picture_images=True,
    images_scale=2.0,
)

# Convert document
result, base_name = convert_document_sdk("document.pdf", pipeline_options)

# Access converted content
markdown = result.document.export_to_markdown()
json_dict = result.document.export_to_dict()
```

## Troubleshooting

### OCR Not Working

- Ensure OCR dependencies are installed
- For Tesseract, verify system installation: `tesseract --version`
- For macOS OCR, ensure you're running on macOS

### Memory Issues

- Reduce `--images-scale` value (try 1.0 or 1.5)
- Process smaller documents or page ranges
- Disable `--generate-page-images` if not needed

### Slow Performance

- Use `rapidocr` instead of `easyocr` for faster OCR
- Disable AI descriptions if not needed
- Process documents in batches

### Image Extraction Issues

- Ensure `--generate-picture-images` is enabled
- Use `--image-mode referenced` for separate image files
- Check that output directory has write permissions

## Performance Tips

1. **Start with baseline** - Run baseline configuration first to establish a reference
2. **Selective testing** - Comment out configurations you don't need in `run_configurations.py`
3. **Parallel processing** - Run different PDFs in parallel (separate terminal windows)
4. **Resource monitoring** - Monitor CPU/memory usage, especially with AI descriptions
5. **Incremental testing** - Test on small documents first, then scale up

## Contributing

Contributions are welcome! Areas for improvement:

- Additional pre-configured scenarios
- Support for more document formats
- Performance optimizations
- Enhanced reporting features
- Integration with document analysis tools

## License

This project uses [Docling](https://github.com/DS4SD/docling), which is licensed under MIT License.

## Resources

- [Docling Documentation](https://ds4sd.github.io/docling/)
- [Docling GitHub](https://github.com/DS4SD/docling)
- [Docling Core](https://github.com/DS4SD/docling-core)

## Support

For issues related to:
- **This framework**: Open an issue in this repository
- **Docling itself**: Visit [Docling GitHub Issues](https://github.com/DS4SD/docling/issues)

---

**Happy Document Converting! 📄✨**