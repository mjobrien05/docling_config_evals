"""Test runner script for Docling configuration iterations.

This script automatically runs docling_test.py with different configurations
to find optimal settings for table and image extraction.
"""
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Configuration definitions
CONFIGURATIONS: List[Dict[str, Any]] = [
    {
        "name": "baseline",
        "description": "Baseline with Image Extraction",
        "args": {
            "table_cell_matching": True,
            "enable_ocr": False,
            "ocr_engine": "auto",
            "enable_remote_services": False,
            "generate_picture_images": True,
            "generate_page_images": False,
            "images_scale": 2.0,
            "image_mode": "referenced",
            "picture_description": False,
            "picture_description_prompt": None,
        },
        "rationale": "Default settings with image extraction - baseline for comparison",
    },
    {
        "name": "no_cell_matching",
        "description": "Disable Cell Matching + Images",
        "args": {
            "table_cell_matching": False,
            "enable_ocr": False,
            "ocr_engine": "auto",
            "enable_remote_services": False,
            "generate_picture_images": True,
            "generate_page_images": False,
            "images_scale": 2.0,
            "image_mode": "referenced",
            "picture_description": False,
            "picture_description_prompt": None,
        },
        "rationale": "May fix merged column issues by using structure prediction instead of PDF cell mapping",
    },
    {
        "name": "ocr_auto",
        "description": "OCR + Image Extraction",
        "args": {
            "table_cell_matching": True,
            "enable_ocr": True,
            "ocr_engine": "auto",
            "enable_remote_services": False,
            "generate_picture_images": True,
            "generate_page_images": False,
            "images_scale": 2.0,
            "image_mode": "referenced",
            "picture_description": False,
            "picture_description_prompt": None,
        },
        "rationale": "Extract text from images using automatic OCR engine selection",
    },
    {
        "name": "ocr_no_cell_matching",
        "description": "OCR + No Cell Matching + Images",
        "args": {
            "table_cell_matching": False,
            "enable_ocr": True,
            "ocr_engine": "auto",
            "enable_remote_services": False,
            "generate_picture_images": True,
            "generate_page_images": False,
            "images_scale": 2.0,
            "image_mode": "referenced",
            "picture_description": False,
            "picture_description_prompt": None,
        },
        "rationale": "Combine OCR with structure prediction approach for tables",
    },
    {
        "name": "ocr_easyocr",
        "description": "OCR (EasyOCR) + Images",
        "args": {
            "table_cell_matching": False,
            "enable_ocr": True,
            "ocr_engine": "easyocr",
            "enable_remote_services": False,
            "generate_picture_images": True,
            "generate_page_images": False,
            "images_scale": 2.0,
            "image_mode": "referenced",
            "picture_description": False,
            "picture_description_prompt": None,
        },
        "rationale": "Test EasyOCR engine quality for image text extraction",
    },
    {
        "name": "ocr_mac",
        "description": "OCR (macOS) + Images",
        "args": {
            "table_cell_matching": False,
            "enable_ocr": True,
            "ocr_engine": "mac",
            "enable_remote_services": False,
            "generate_picture_images": True,
            "generate_page_images": False,
            "images_scale": 2.0,
            "image_mode": "referenced",
            "picture_description": False,
            "picture_description_prompt": None,
        },
        "rationale": "Use macOS Vision framework for OCR (may provide better results on macOS)",
    },
    {
        "name": "ocr_remote_services",
        "description": "OCR (Remote) + Images",
        "args": {
            "table_cell_matching": False,
            "enable_ocr": True,
            "ocr_engine": "auto",
            "enable_remote_services": True,
            "generate_picture_images": True,
            "generate_page_images": False,
            "images_scale": 2.0,
            "image_mode": "referenced",
            "picture_description": False,
            "picture_description_prompt": None,
        },
        "rationale": "Enable remote OCR services for potentially better quality",
    },
    {
        "name": "images_with_descriptions",
        "description": "Images + AI Descriptions",
        "args": {
            "table_cell_matching": True,
            "enable_ocr": False,
            "ocr_engine": "auto",
            "enable_remote_services": False,
            "generate_picture_images": True,
            "generate_page_images": False,
            "images_scale": 2.0,
            "image_mode": "referenced",
            "picture_description": True,
            "picture_description_prompt": "Provide a detailed technical description of this image, including any charts, diagrams, or visual elements.",
        },
        "rationale": "Extract images with AI-generated descriptions using VLM",
    },
    {
        "name": "ocr_with_descriptions",
        "description": "OCR + Images + AI Descriptions",
        "args": {
            "table_cell_matching": False,
            "enable_ocr": True,
            "ocr_engine": "auto",
            "enable_remote_services": False,
            "generate_picture_images": True,
            "generate_page_images": False,
            "images_scale": 2.0,
            "image_mode": "referenced",
            "picture_description": True,
            "picture_description_prompt": "Describe this image in detail, focusing on technical content, charts, and any textual elements.",
        },
        "rationale": "Combine OCR text extraction with AI-powered image descriptions for comprehensive image analysis",
    },
    {
        "name": "full_page_thumbnails",
        "description": "Full-Page Thumbnails + Images",
        "args": {
            "table_cell_matching": True,
            "enable_ocr": False,
            "ocr_engine": "auto",
            "enable_remote_services": False,
            "generate_picture_images": True,
            "generate_page_images": True,
            "images_scale": 2.0,
            "image_mode": "referenced",
            "picture_description": False,
            "picture_description_prompt": None,
        },
        "rationale": "Generate both figure images and full-page thumbnails for complete visual documentation",
    },
    {
        "name": "ocr_easyocr_with_descriptions",
        "description": "OCR (EasyOCR) + Images + AI Descriptions",
        "args": {
            "table_cell_matching": False,
            "enable_ocr": True,
            "ocr_engine": "easyocr",
            "enable_remote_services": False,
            "generate_picture_images": True,
            "generate_page_images": False,
            "images_scale": 2.0,
            "image_mode": "referenced",
            "picture_description": True,
            "picture_description_prompt": "Provide a detailed technical description of this image, including any charts, diagrams, or visual elements.",
        },
        "rationale": "Combines EasyOCR's clean text extraction with AI-powered image descriptions for comprehensive document understanding",
    },
]


def build_command_args(config: Dict[str, Any], pdf_path: str, output_dir: str) -> List[str]:
    """Build command-line arguments for docling_test.py from configuration.
    
    Args:
        config: Configuration dictionary
        pdf_path: Path to PDF file to convert
        output_dir: Output directory for results
        
    Returns:
        List of command-line arguments
    """
    args = ["python", "docling_test.py", pdf_path, "--output-dir", output_dir, "--no-print"]
    
    # Add configuration arguments
    table_cell_matching = config["args"]["table_cell_matching"]
    args.extend(["--table-cell-matching", "true" if table_cell_matching else "false"])
    
    if config["args"]["enable_ocr"]:
        args.append("--enable-ocr")
        args.extend(["--ocr-engine", config["args"]["ocr_engine"]])
    
    if config["args"]["enable_remote_services"]:
        args.append("--enable-remote-services")
    
    # Add image processing arguments
    if config["args"].get("generate_picture_images", False):
        args.append("--generate-picture-images")
    
    if config["args"].get("generate_page_images", False):
        args.append("--generate-page-images")
    
    if "images_scale" in config["args"]:
        args.extend(["--images-scale", str(config["args"]["images_scale"])])
    
    if "image_mode" in config["args"]:
        args.extend(["--image-mode", config["args"]["image_mode"]])
    
    if config["args"].get("picture_description", False):
        args.append("--picture-description")
        if config["args"].get("picture_description_prompt"):
            args.extend(["--picture-description-prompt", config["args"]["picture_description_prompt"]])
    
    # Add config name for output file naming
    args.extend(["--config-name", config["name"]])
    
    return args


def run_configuration(
    config: Dict[str, Any],
    pdf_path: str,
    output_dir: str,
    config_num: int,
    total_configs: int,
) -> tuple[bool, str, float]:
    """Run a single configuration.
    
    Args:
        config: Configuration dictionary
        pdf_path: Path to PDF file to convert
        output_dir: Output directory for results
        config_num: Current configuration number (1-indexed)
        total_configs: Total number of configurations
        
    Returns:
        Tuple of (success: bool, output: str, duration: float)
    """
    print(f"\n{'='*80}")
    print(f"[{config_num}/{total_configs}] Running Configuration: {config['name']}")
    print(f"Description: {config['description']}")
    print(f"Rationale: {config['rationale']}")
    print(f"{'='*80}\n")
    
    cmd_args = build_command_args(config, pdf_path, output_dir)
    print(f"Command: {' '.join(cmd_args)}\n")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd_args,
            capture_output=True,
            text=True,
            check=True,
        )
        duration = time.time() - start_time
        print(result.stdout)
        return True, result.stdout, duration
    except subprocess.CalledProcessError as e:
        duration = time.time() - start_time
        print(f"ERROR: Configuration '{config['name']}' failed!")
        print(f"Return code: {e.returncode}")
        print(f"STDOUT:\n{e.stdout}")
        print(f"STDERR:\n{e.stderr}")
        return False, e.stderr, duration
    except Exception as e:
        duration = time.time() - start_time
        error_msg = f"Unexpected error running configuration '{config['name']}': {e}"
        print(f"ERROR: {error_msg}")
        return False, error_msg, duration


def generate_summary_report(
    results: List[Dict[str, Any]],
    output_dir: str,
    pdf_path: str,
) -> None:
    """Generate a summary report of all test runs.
    
    Args:
        results: List of result dictionaries with 'config', 'success', 'output' keys
        output_dir: Output directory
        pdf_path: Path to PDF file that was tested
    """
    report_path = Path(output_dir) / "configuration_test_report.md"
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Docling Configuration Test Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Test PDF:** `{pdf_path}`\n\n")
        f.write("---\n\n")
        
        # Summary table
        f.write("## Summary\n\n")
        f.write("| Configuration | Status | Description |\n")
        f.write("|---------------|--------|-------------|\n")
        for result in results:
            status = "✅ Success" if result["success"] else "❌ Failed"
            f.write(
                f"| {result['config']['name']} | {status} | "
                f"{result['config']['description']} |\n"
            )
        
        f.write("\n---\n\n")
        
        # Detailed results
        f.write("## Detailed Results\n\n")
        for result in results:
            config = result["config"]
            f.write(f"### {config['name']}: {config['description']}\n\n")
            f.write(f"**Rationale:** {config['rationale']}\n\n")
            f.write(f"**Status:** {'✅ Success' if result['success'] else '❌ Failed'}\n\n")
            f.write("**Configuration:**\n")
            f.write("```python\n")
            for key, value in config["args"].items():
                f.write(f"  {key} = {value}\n")
            f.write("```\n\n")
            
            if not result["success"]:
                f.write("**Error Output:**\n")
                f.write("```\n")
                f.write(result["output"])
                f.write("\n```\n\n")
            
            f.write("---\n\n")
        
        # Output files
        f.write("## Output Files\n\n")
        f.write("Each configuration generates the following files:\n")
        f.write("- `{base_name}_{config_name}.md` - Markdown output with image references\n")
        f.write("- `{base_name}_{config_name}.json` - Full JSON document structure\n")
        f.write("- `{base_name}_{config_name}_artifacts/images/` - Extracted image files (when using referenced mode)\n\n")
        f.write("Compare the markdown files to evaluate:\n")
        f.write("- Table extraction quality (headers, column order, cell alignment)\n")
        f.write("- Image extraction quality (extracted images, OCR text, AI descriptions)\n")
        f.write("- Image reference accuracy in markdown\n")
        f.write("- Overall markdown structure\n")
    
    print(f"\n{'='*80}")
    print(f"Summary report saved to: {report_path}")
    print(f"{'='*80}\n")


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def print_progress_summary(
    config_num: int,
    total_configs: int,
    config_name: str,
    success: bool,
    duration: float,
    successful: int,
    failed: int,
    avg_duration: float,
) -> None:
    """Print a progress summary after each configuration.
    
    Args:
        config_num: Current configuration number
        total_configs: Total number of configurations
        config_name: Name of the configuration
        success: Whether the configuration succeeded
        duration: Duration of the configuration in seconds
        successful: Number of successful configurations so far
        failed: Number of failed configurations so far
        avg_duration: Average duration per configuration
    """
    status = "✅ SUCCESS" if success else "❌ FAILED"
    progress_pct = (config_num / total_configs) * 100
    remaining = total_configs - config_num
    estimated_time = remaining * avg_duration if avg_duration > 0 else 0
    
    print(f"\n{'─'*80}")
    print(f"Configuration '{config_name}': {status} (took {format_duration(duration)})")
    print(f"Progress: {config_num}/{total_configs} ({progress_pct:.1f}%) | "
          f"✅ {successful} | ❌ {failed}")
    
    if remaining > 0 and avg_duration > 0:
        print(f"Estimated time remaining: {format_duration(estimated_time)} "
              f"({remaining} configurations left)")
    
    print(f"{'─'*80}\n")


def main():
    """Main entry point for test runner."""
    if len(sys.argv) < 2:
        print("Usage: python run_configurations.py <pdf_path> [output_dir]")
        print("\nExample:")
        print("  python run_configurations.py docling_poc.pdf")
        print("  python run_configurations.py docling_poc.pdf ./output")
        sys.exit(1)
    
    pdf_path = Path(sys.argv[1])
    if not pdf_path.exists():
        print(f"Error: PDF file not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)
    
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "./output"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    total_configs = len(CONFIGURATIONS)
    start_time = time.time()
    
    print(f"\n{'='*80}")
    print(f"🚀 Starting Docling Configuration Tests")
    print(f"{'='*80}")
    print(f"PDF: {pdf_path}")
    print(f"Output Directory: {output_dir}")
    print(f"Total configurations to test: {total_configs}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")
    
    results = []
    successful = 0
    failed = 0
    durations = []
    
    for idx, config in enumerate(CONFIGURATIONS, start=1):
        success, output, duration = run_configuration(
            config,
            str(pdf_path),
            str(output_dir),
            idx,
            total_configs,
        )
        
        durations.append(duration)
        avg_duration = sum(durations) / len(durations)
        
        results.append({
            "config": config,
            "success": success,
            "output": output,
            "duration": duration,
        })
        
        if success:
            successful += 1
        else:
            failed += 1
        
        # Print progress summary after each configuration
        print_progress_summary(
            idx,
            total_configs,
            config["name"],
            success,
            duration,
            successful,
            failed,
            avg_duration,
        )
    
    total_duration = time.time() - start_time
    
    # Generate summary report
    generate_summary_report(results, str(output_dir), str(pdf_path))
    
    # Final summary
    print(f"\n{'='*80}")
    print(f"✨ Test Run Complete")
    print(f"{'='*80}")
    print(f"Total configurations: {total_configs}")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"⏱️  Total time: {format_duration(total_duration)}")
    print(f"⏱️  Average time per config: {format_duration(total_duration / total_configs)}")
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\n📁 Review the output files in: {output_dir}")
    print(f"📊 See summary report: {output_dir / 'configuration_test_report.md'}")
    print(f"{'='*80}\n")
    
    # Exit with error code if any failed
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
