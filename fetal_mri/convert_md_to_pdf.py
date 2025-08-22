#!/usr/bin/env python3

"""
Enhanced Pandoc PDF Converter for Clinical Research Report
=========================================================

This script creates a clean markdown version and converts it to PDF using pandoc
with proper Unicode handling and professional formatting.
"""

import re
import os

def clean_markdown_for_latex(input_file, output_file):
    """Clean markdown file for better LaTeX/PDF conversion"""
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace Greek letters and mathematical symbols with LaTeX equivalents
    replacements = {
        'μ_WM': '$\\mu_{WM}$',
        'μ_GM': '$\\mu_{GM}$',
        'σ_WM²': '$\\sigma_{WM}^2$',
        'σ_GM²': '$\\sigma_{GM}^2$',
        '√[(σ_WM² + σ_GM²) / 2]': '$\\sqrt{(\\sigma_{WM}^2 + \\sigma_{GM}^2) / 2}$',
        '√': '$\\sqrt{}$',
        '±': '$\\pm$',
        '—': '--',
        '–': '--',
        '×': '$\\times$',
        '°': '$^\\circ$',
    }
    
    # Apply replacements
    for old, new in replacements.items():
        content = content.replace(old, new)
    
    # Fix any remaining mathematical formulas
    content = re.sub(r'CR = μ_WM / μ_GM', r'CR = $\\mu_{WM} / \\mu_{GM}$', content)
    content = re.sub(r'CNR = \|μ_WM - μ_GM\| / √\[(σ_WM² \+ σ_GM²\) / 2\]', 
                     r'CNR = $|\\mu_{WM} - \\mu_{GM}| / \\sqrt{(\\sigma_{WM}^2 + \\sigma_{GM}^2) / 2}$', content)
    
    # Save cleaned version
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Cleaned markdown saved to: {output_file}")
    return output_file

def convert_to_pdf_with_pandoc(input_md, output_pdf):
    """Convert markdown to PDF using pandoc with professional formatting"""
    
    pandoc_cmd = [
        'pandoc', input_md,
        '-o', output_pdf,
        '--pdf-engine=xelatex',
        '--toc',
        '--number-sections',
        '-V', 'geometry:margin=1in',
        '-V', 'fontsize=11pt',
        '-V', 'documentclass=article',
        '-V', 'classoption=onecolumn',
        '-V', 'title=Clinical Research Report: Impact of Echo Time and Stack Count on Fetal MRI Image Quality',
        '-V', 'author=Fetal MRI Image Quality Assessment Group, Laboratory for Neuro Imaging, USC',
        '-V', f'date=August 22, 2025',
        '-V', 'toc-title=Table of Contents',
        '-V', 'colorlinks=true',
        '-V', 'linkcolor=blue',
        '-V', 'urlcolor=blue',
        '-V', 'citecolor=blue',
        '--highlight-style=tango',
        '--template=default'
    ]
    
    # Run pandoc command
    import subprocess
    try:
        result = subprocess.run(pandoc_cmd, check=True, capture_output=True, text=True)
        print(f"PDF successfully created: {output_pdf}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Pandoc conversion failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def main():
    """Main function to clean markdown and convert to PDF"""
    
    input_file = '/home/ajoshi/Projects/disc_mri/fetal_mri/fetal_mri_clinical_research_report.md'
    clean_file = '/home/ajoshi/Projects/disc_mri/fetal_mri/fetal_mri_clinical_research_report_clean.md'
    output_pdf = '/home/ajoshi/Projects/disc_mri/fetal_mri/fetal_mri_clinical_research_report_pandoc_clean.pdf'
    
    print("=== Enhanced Pandoc PDF Converter ===\n")
    
    # Step 1: Clean markdown for LaTeX compatibility
    print("Step 1: Cleaning markdown for LaTeX compatibility...")
    cleaned_md = clean_markdown_for_latex(input_file, clean_file)
    
    # Step 2: Convert to PDF using pandoc
    print("Step 2: Converting to PDF using pandoc...")
    success = convert_to_pdf_with_pandoc(cleaned_md, output_pdf)
    
    if success:
        # Check file size
        file_size = os.path.getsize(output_pdf) / 1024  # KB
        print(f"\n=== Conversion Complete ===")
        print(f"Input file: {input_file}")
        print(f"Output PDF: {output_pdf}")
        print(f"File size: {file_size:.1f} KB")
        print(f"Features: Table of Contents, Section Numbers, Professional Formatting")
    else:
        print("Conversion failed. Please check the error messages above.")

if __name__ == "__main__":
    main()
