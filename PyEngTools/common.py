import os
import ocrmypdf
import shutil

"""
Functions / classes common to all PyEngTools modules
"""


def detect_input_pdfs(input_path):
    """Returns a list with filepaths of all pdfs being used in the input"""

    input_pdfs = []

    for file in os.listdir(input_path):
        if file.endswith('.pdf'):
            input_pdfs.append(os.path.join(input_path, file))

    return input_pdfs


def create_dir(directory):
    """Creates a directory if it does not exist already. If the directory
    exists, does nothing."""

    if not os.path.exists(directory):
        os.makedirs(directory)


def delete_dir(directory):
    if os.path.exists(directory):
        os.remove(directory)


def table_settings(preset='TfNSW'):
    available_presets = ['TfNSW']

    """ This class stores detection parameters for PDFPlumber. """

    if preset in available_presets:
        if preset == 'TfNSW':
            table_settings = {
                "vertical_strategy": "lines",
                "horizontal_strategy": "lines",
                "explicit_vertical_lines": [],
                "explicit_horizontal_lines": [],
                "snap_tolerance": 10,
                "snap_x_tolerance": 10,
                "snap_y_tolerance": 10,
                "join_tolerance": 3,
                "join_x_tolerance": 3,
                "join_y_tolerance": 3,
                "edge_min_length": 3,
                "min_words_vertical": 3,
                "min_words_horizontal": 1,
                "keep_blank_chars": False,
                "text_tolerance": 3,
                "text_x_tolerance": 3,
                "text_y_tolerance": 3,
                "intersection_tolerance": 3,
                "intersection_x_tolerance": 3,
                "intersection_y_tolerance": 3,
            }
            return table_settings

    # Ignore invalid preset requests
    else:
        print(f"Table preset named {preset} not found!")
        return None


def pdf_page_margins(page, preset='TfNSW'):
    """ This function takes a pdfplumber page object and returns page
    margins based on value of `preset`"""
    available_presets = ['TfNSW']

    width = page.width
    height = page.height

    if preset in available_presets:
        if preset == 'TfNSW':
            page_margins = (0, 50, width, height - 70)

    else:
        print(f"Page margin preset named {preset} not found!")
        return None


def ocr_pdfs(pdf_filepaths, output_dir):
    create_dir(output_dir)

    for pdf in pdf_filepaths:
        output_path = os.path.join(output_dir, 'OCR_', os.path.basename(pdf))
        if os.path.exists(output_path):
            delete_dir(output_path)

        ocrmypdf.ocr(input_file=pdf, output_file=output_path)
