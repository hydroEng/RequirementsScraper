import os
import pdfplumber
from common import *
import re


# Helper functions
def _extract_table_text(page, table):
    table_text = page.crop(table.bbox).extract_text()
    return table_text


def _remove_table_text(page_text, table_text, table_number):
    updated_text = page_text.replace(table_text, f"\n@@reserved Table {table_number}")
    return updated_text


def _table_to_image(page, table, table_number, save_location, table_resolution=100):
    table_filepath = os.path.join(save_location, f"TABLE {table_number}.png")
    page.crop(table.bbox).to_image(resolution=table_resolution).save(table_filepath)


class RequirementsScraper:

    def __init__(self, input_path, output_path):
        self._input_path = input_path
        self._output_path = output_path

    @staticmethod
    def search_patterns(preset='TfNSW'):
        available_presets = ['TfNSW']

        if preset in available_presets:
            if preset == 'TfNSW':
                chapter_headings = r"(\n\s*\d[.]?\d?[.]?\d?\s+[A-Z].*)"
                requirements = r"(?sm)^([(]\w{0,4}[)]\s)(.*?)(?=^[(]\w{0,4}[)]\s)"
        else:
            print(f"Search pattern preset {preset} not found!")
            return None

    def scrape_pdfs(self, chapter_headings, requirements, table_settings, extract_tables=True):
        """Main function to convert document requirements to a dataframe."""
        input_pdfs = detect_input_pdfs(self._input_path)

        # Indexes / variables
        table_index = 0
        all_text = ""

        # Folder for saving images:

        if extract_tables:
            temp_folder = os.path.join(self._output_path(), "table_filepath")

            if not os.path.exists(temp_folder):
                os.makedirs(temp_folder)

        for input_pdf in input_pdfs:

            pdfreader = pdfplumber.open(self._input_path)
            pages = pdfreader.pages

            for page in pages:

                page_margins = pdf_page_margins(page)

                # Crop header, extract text, locate tables to extract
                # later/remove text
                page = page.crop(page_margins)
                page_text = page.extract_text()
                tables = page.find_tables()

                # Extract text from page, remove text from page, extract table
                # to image if extract_tables=True, add to all_text
                for table in tables:
                    table_index += 1
                    table_text = _extract_table_text(page, table)
                    page_text = _remove_table_text(page_text, table_text, table_index)

                    if extract_tables:
                        _table_to_image(page, table, table_index, self._output_path)
                    all_text += page_text

        # Find strings
