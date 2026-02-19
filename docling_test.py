"""Convert documents using Docling document converter.

This script follows Docling best practices by using the DocumentConverter API
directly when available, with fallback to server-based conversion.
It supports both local file paths and URLs.
"""
from pathlib import Path
import json
import argparse
import sys

# Try to import the Python SDK, fall back to server-based approach if not available
try:
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.pipeline_options import (
        PdfPipelineOptions,
        TableStructureOptions,
        OcrAutoOptions,
        EasyOcrOptions,
        RapidOcrOptions,
        TesseractOcrOptions,
        OcrMacOptions,
    )
    from docling.datamodel.base_models import InputFormat
    from docling.exceptions import ConversionError
    from docling_core.types.doc.base import ImageRefMode
    SDK_AVAILABLE = True
except ImportError:
    import requests
    SDK_AVAILABLE = False
    DOCLING_SERVER_URL = "http://localhost:5001"


def build_pipeline_options(
    table_cell_matching: bool = True,
    enable_ocr: bool = False,
    ocr_engine: str = "auto",
    enable_remote_services: bool = False,
    generate_picture_images: bool = False,
    generate_page_images: bool = False,
    images_scale: float = 2.0,
    do_picture_description: bool = False,
    picture_description_prompt: str | None = None,
) -> PdfPipelineOptions:
    """Build PdfPipelineOptions from configuration parameters.
    
    Args:
        table_cell_matching: If True, maps table structure back to PDF cells.
                           If False, uses text cells from structure prediction.
        enable_ocr: Enable OCR for image extraction
        ocr_engine: OCR engine to use (auto, easyocr, rapidocr, tesseract, mac)
        enable_remote_services: Enable remote OCR services if available
        generate_picture_images: Extract figure/picture images from PDF
        generate_page_images: Generate full-page rendered images (thumbnails)
        images_scale: Resolution scale for generated images (higher = higher resolution)
        do_picture_description: Enable AI-powered image descriptions using VLM
        picture_description_prompt: Custom prompt for image descriptions
        
    Returns:
        Configured PdfPipelineOptions instance
    """
    pipeline_options = PdfPipelineOptions()

    # Images (PDF rasterization) note:
    # - If a downstream pipeline wants *thumbnail/page preview* images, enable full-page rendering:
    #     pipeline_options.generate_page_images = True
    #     pipeline_options.images_scale = 2.0  # higher = higher resolution (and larger files)
    # - For extracted figure/picture images (not full pages), use:
    #     pipeline_options.generate_picture_images = True
    
    # Table structure options
    pipeline_options.do_table_structure = True
    pipeline_options.table_structure_options = TableStructureOptions(
        do_cell_matching=table_cell_matching
    )
    
    # OCR options
    pipeline_options.do_ocr = enable_ocr
    pipeline_options.enable_remote_services = enable_remote_services
    
    if enable_ocr:
        ocr_engine_lower = ocr_engine.lower()
        if ocr_engine_lower == "auto":
            pipeline_options.ocr_options = OcrAutoOptions()
        elif ocr_engine_lower == "easyocr":
            pipeline_options.ocr_options = EasyOcrOptions()
        elif ocr_engine_lower == "rapidocr":
            pipeline_options.ocr_options = RapidOcrOptions()
        elif ocr_engine_lower == "tesseract":
            pipeline_options.ocr_options = TesseractOcrOptions()
        elif ocr_engine_lower == "mac":
            pipeline_options.ocr_options = OcrMacOptions()
        else:
            # Default to auto if unknown engine specified
            pipeline_options.ocr_options = OcrAutoOptions()
    
    # Image generation options
    pipeline_options.generate_picture_images = generate_picture_images
    pipeline_options.generate_page_images = generate_page_images
    pipeline_options.images_scale = images_scale
    
    # Picture description (AI captioning) options
    if do_picture_description:
        pipeline_options.do_picture_description = True
        # Configure with custom prompt using inline VLM
        from docling.datamodel.pipeline_options import PictureDescriptionVlmOptions
        # Use default SmolVLM model if no specific model is provided
        prompt = picture_description_prompt if picture_description_prompt else "Describe this image in detail."
        pipeline_options.picture_description_options = PictureDescriptionVlmOptions(
            repo_id="HuggingFaceTB/SmolVLM-Instruct",  # Default VLM model
            prompt=prompt
        )
    
    return pipeline_options


def convert_document_sdk(
    source: str | Path,
    pipeline_options: PdfPipelineOptions | None = None,
) -> tuple:
    """Convert document using Docling DocumentConverter (Python SDK).
    
    Args:
        source: Path to local file or URL to convert
        pipeline_options: Optional PdfPipelineOptions for configuration.
                         If None, uses default settings.
        
    Returns:
        Tuple of (ConversionResult, base_name for output files)
        
    Raises:
        ConversionError: If conversion fails
        FileNotFoundError: If local file doesn't exist
    """
    if pipeline_options is not None:
        format_options = {
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
        converter = DocumentConverter(format_options=format_options)
    else:
        converter = DocumentConverter()
    
    result = converter.convert(source)
    
    # Extract base name from source
    if isinstance(source, Path):
        base_name = source.stem
    else:
        # For URLs, use a generic name or extract from URL
        base_name = Path(source).stem if Path(source).suffix else "converted_document"
    
    return result, base_name


def convert_document_server(file_path: Path, server_url: str) -> dict:
    """Convert document using Docling server API.
    
    Args:
        file_path: Path to local file to convert
        server_url: URL of the Docling server
        
    Returns:
        Dictionary with conversion results
        
    Raises:
        requests.exceptions.RequestException: If server request fails
    """
    with open(file_path, 'rb') as f:
        files = {'files': (file_path.name, f)}
        response = requests.post(f"{server_url}/v1/convert/file", files=files)
        response.raise_for_status()
        return response.json()


def main():
    """Main entry point for document conversion."""
    parser = argparse.ArgumentParser(
        description='Convert documents using Docling DocumentConverter',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s document.pdf
  %(prog)s https://arxiv.org/pdf/2408.09869
  %(prog)s document.pdf --output-dir ./output
  %(prog)s document.pdf --generate-picture-images --image-mode referenced
  %(prog)s document.pdf --generate-picture-images --picture-description --image-mode referenced
  %(prog)s document.pdf --generate-page-images --images-scale 3.0 --image-mode embedded
        """
    )
    parser.add_argument(
        'source',
        help='Path to local file or URL to convert'
    )
    parser.add_argument(
        '--output-dir',
        default='./output',
        help='Output directory (default: ./output)'
    )
    parser.add_argument(
        '--no-print',
        action='store_true',
        help='Skip printing markdown content to stdout'
    )
    server_url_default = "http://localhost:5001" if not SDK_AVAILABLE else None
    parser.add_argument(
        '--server-url',
        default=server_url_default,
        help='Docling server URL (only used if Python SDK is not available)'
    )
    
    # Configuration options (only available when SDK is available)
    if SDK_AVAILABLE:
        parser.add_argument(
            '--table-cell-matching',
            type=str,
            choices=['true', 'false', 'True', 'False'],
            default='true',
            help='Enable table cell matching (true/false, default: true)'
        )
        parser.add_argument(
            '--enable-ocr',
            action='store_true',
            help='Enable OCR for image extraction'
        )
        parser.add_argument(
            '--ocr-engine',
            choices=['auto', 'easyocr', 'rapidocr', 'tesseract', 'mac'],
            default='auto',
            help='OCR engine to use (default: auto)'
        )
        parser.add_argument(
            '--enable-remote-services',
            action='store_true',
            help='Enable remote OCR services if available'
        )
        parser.add_argument(
            '--config-name',
            default=None,
            help='Optional name to append to output files for configuration tracking'
        )
        
        # Image processing options
        parser.add_argument(
            '--generate-picture-images',
            action='store_true',
            help='Extract figure/picture images from PDF'
        )
        parser.add_argument(
            '--generate-page-images',
            action='store_true',
            help='Generate full-page rendered images (thumbnails)'
        )
        parser.add_argument(
            '--images-scale',
            type=float,
            default=2.0,
            help='Resolution scale for generated images (default: 2.0)'
        )
        parser.add_argument(
            '--image-mode',
            choices=['placeholder', 'embedded', 'referenced'],
            default='placeholder',
            help='Image export mode: placeholder (<!-- image -->), embedded (base64), or referenced (file links, default: placeholder)'
        )
        parser.add_argument(
            '--picture-description',
            action='store_true',
            help='Enable AI-powered image descriptions using VLM'
        )
        parser.add_argument(
            '--picture-description-prompt',
            default='Describe this image in detail.',
            help='Custom prompt for image descriptions (default: "Describe this image in detail.")'
        )
    
    args = parser.parse_args()
    
    # Validate local file exists (if not a URL)
    source_path = Path(args.source)
    if not str(args.source).startswith(('http://', 'https://')):
        if not source_path.exists():
            print(f"Error: File not found: {args.source}", file=sys.stderr)
            sys.exit(1)
        source = source_path
    else:
        source = args.source
    
    print(f"Converting: {args.source}")
    
    # Use SDK if available, otherwise fall back to server
    if SDK_AVAILABLE:
        print("Using Docling Python SDK")
        
        # Build pipeline options from arguments
        pipeline_options = None
        if any([
            hasattr(args, 'table_cell_matching') and args.table_cell_matching.lower() != 'true',
            hasattr(args, 'enable_ocr') and args.enable_ocr,
            hasattr(args, 'enable_remote_services') and args.enable_remote_services,
            hasattr(args, 'generate_picture_images') and args.generate_picture_images,
            hasattr(args, 'generate_page_images') and args.generate_page_images,
            hasattr(args, 'picture_description') and args.picture_description,
        ]):
            table_cell_matching = getattr(args, 'table_cell_matching', 'true').lower() == 'true'
            pipeline_options = build_pipeline_options(
                table_cell_matching=table_cell_matching,
                enable_ocr=getattr(args, 'enable_ocr', False),
                ocr_engine=getattr(args, 'ocr_engine', 'auto'),
                enable_remote_services=getattr(args, 'enable_remote_services', False),
                generate_picture_images=getattr(args, 'generate_picture_images', False),
                generate_page_images=getattr(args, 'generate_page_images', False),
                images_scale=getattr(args, 'images_scale', 2.0),
                do_picture_description=getattr(args, 'picture_description', False),
                picture_description_prompt=getattr(args, 'picture_description_prompt', None) if getattr(args, 'picture_description', False) else None,
            )
            print(f"Configuration: table_cell_matching={table_cell_matching}, "
                  f"enable_ocr={getattr(args, 'enable_ocr', False)}, "
                  f"ocr_engine={getattr(args, 'ocr_engine', 'auto')}, "
                  f"enable_remote_services={getattr(args, 'enable_remote_services', False)}, "
                  f"generate_picture_images={getattr(args, 'generate_picture_images', False)}, "
                  f"generate_page_images={getattr(args, 'generate_page_images', False)}, "
                  f"images_scale={getattr(args, 'images_scale', 2.0)}, "
                  f"picture_description={getattr(args, 'picture_description', False)}")
        
        try:
            result, base_name = convert_document_sdk(source, pipeline_options)
        except ConversionError as e:
            print(f"Error during conversion: {e}", file=sys.stderr)
            sys.exit(1)
        except FileNotFoundError as e:
            print(f"Error: File not found: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Unexpected error: {e}", file=sys.stderr)
            sys.exit(1)
        
        # Check conversion status
        if result.status.value == "failure":
            print(f"Error: Conversion failed with status: {result.status.value}", file=sys.stderr)
            if result.errors:
                for error in result.errors:
                    print(f"  - {error.error_message}", file=sys.stderr)
            sys.exit(1)
        
        # Create output directory
        out_dir = Path(args.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        
        # Add config name suffix if provided
        config_suffix = f"_{getattr(args, 'config_name', '')}" if getattr(args, 'config_name', None) else ""
        
        # Export to JSON (full document structure)
        json_path = out_dir / f"{base_name}{config_suffix}.json"
        doc_dict = result.document.export_to_dict()
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(doc_dict, f, indent=2, ensure_ascii=False)
        print(f"JSON output saved to: {json_path}")
        
        # Export to Markdown with image handling
        md_path = out_dir / f"{base_name}{config_suffix}.md"
        
        # Determine image mode
        image_mode_str = getattr(args, 'image_mode', 'placeholder')
        if image_mode_str == 'embedded':
            image_mode = ImageRefMode.EMBEDDED
        elif image_mode_str == 'referenced':
            image_mode = ImageRefMode.REFERENCED
        else:
            image_mode = ImageRefMode.PLACEHOLDER
        
        # Create artifacts directory for referenced images
        if image_mode == ImageRefMode.REFERENCED:
            # Use absolute path to prevent Docling from creating nested directories
            artifacts_dir = (out_dir / f"{base_name}{config_suffix}_artifacts").resolve()
            artifacts_dir.mkdir(parents=True, exist_ok=True)
            result.document.save_as_markdown(
                md_path,
                artifacts_dir=artifacts_dir,
                image_mode=image_mode
            )
            print(f"Markdown output saved to: {md_path}")
            print(f"Image artifacts saved to: {artifacts_dir}")
        else:
            # For PLACEHOLDER or EMBEDDED modes, no artifacts directory needed
            markdown_content = result.document.export_to_markdown(image_mode=image_mode)
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)
            print(f"Markdown output saved to: {md_path}")
        
        # Read markdown for printing (if needed)
        if not args.no_print:
            with open(md_path, "r", encoding="utf-8") as f:
                markdown_content = f.read()
            print("\n" + "="*80)
            print("MARKDOWN CONTENT:")
            print("="*80)
            print(markdown_content)
            print("="*80 + "\n")
        
        print(f"\nConversion completed successfully! Status: {result.status.value}")
    
    else:
        # Fall back to server-based approach
        print(f"Using Docling server at: {args.server_url}")
        
        if isinstance(source, str) and source.startswith(('http://', 'https://')):
            print("Error: Server-based conversion only supports local files, not URLs", file=sys.stderr)
            sys.exit(1)
        
        if not isinstance(source, Path):
            source = Path(source)
        
        try:
            result = convert_document_server(source, args.server_url)
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to Docling server: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error during conversion: {e}", file=sys.stderr)
            sys.exit(1)
        
        # Create output directory
        out_dir = Path(args.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate output filename base from input filename
        base_name = source.stem
        
        # Save JSON output
        json_path = out_dir / f"{base_name}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"JSON output saved to: {json_path}")
        
        # Export to markdown (preferred format)
        if 'markdown' in result:
            markdown_content = result['markdown']
            md_path = out_dir / f"{base_name}.md"
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)
            print(f"Markdown output saved to: {md_path}")
            
            # Print markdown content to screen unless --no-print is specified
            if not args.no_print:
                print("\n" + "="*80)
                print("MARKDOWN CONTENT:")
                print("="*80)
                print(markdown_content)
                print("="*80 + "\n")
        
        # Export to plain text (fallback or additional format)
        if 'text' in result:
            text_content = result['text']
            text_path = out_dir / f"{base_name}.txt"
            with open(text_path, "w", encoding="utf-8") as f:
                f.write(text_content)
            print(f"Plain text saved to: {text_path}")
            
            # Print text content to screen if markdown wasn't available
            if 'markdown' not in result and not args.no_print:
                print("\n" + "="*80)
                print("TEXT CONTENT:")
                print("="*80)
                print(text_content)
                print("="*80 + "\n")
        
        print("\nConversion completed successfully!")


if __name__ == "__main__":
    main()

