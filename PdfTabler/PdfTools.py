import os

import pdfplumber
import re


# Global functions
def detect_input_pdfs(self, input_path):
    """Returns a list with filepaths of all pdfs being used in the input"""

    input_pdfs = []

    for file in os.listdir(self.output_path):
        if file.endswith('.pdf'):
            input_pdfs.append(os.path.join(self.input_path, file))

    return input_pdfs


class RequirementsScraper:

    def __init__(self, input_path, output_path, table_settings, pdf_schema):
        self.input_path = input_path
        self.output_path = output_path
        self.table_settings = table_settings  # These should be class variables not functions. Restructure your code
        self.pdf_schema = pdf_schema

        # Class-wide settings
        table_resolution = 100

    class TableSettings:
        # Need to think about best method to
        """ This class stores detection parameters for PDFPlumber. Currently only supports TfNSW table preset (should be
        good enough for most cases """

        def __init__(self):
            self.table_settings = self.settings()

        @classmethod
        def settings(cls, preset='TfNSW'):

            available_presets = ['TfNSW']

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
            try:
                return table_settings
            except UnboundLocalError:
                print(f"Error! No table preset \"{preset}\" exists.")

    class PdfSettings:

        """ Set parameters related to page / text layout such as regexes for finding requirements and
        setting page margins"""

        def __init__(self):

            self.chapter_headings, self.requirements = self.search_patterns()
            self.page_margins = self.page_margins()

        @classmethod
        def search_patterns(cls, preset='TfNSW'):
            if preset == 'TfNSW':
                chapter_headings = r"(\n\s*\d[.]?\d?[.]?\d?\s+[A-Z].*)"
                requirements = r"(?sm)^([(]\w{0,4}[)]\s)(.*?)(?=^[(]\w{0,4}[)]\s)"
            try:
                return chapter_headings, requirements
            except UnboundLocalError:
                print(f"Error! No pdf page preset {preset} exists.")

        @classmethod
        def page_margins(cls, page, preset='TfNSW'):
            width = page.width
            height = page.height

            """ This function takes a pdfplumber page object and returns page margins based on value of `preset`"""
            if preset == 'TfNSW':
                page_margins = (0, 50, width, height - 70)
            try:
                return page_margins
            except UnboundLocalError:
                print(f"Error! No pdf page preset {preset} exists.")

    def pdf_schema_helper(self, page):

        """This function provides specific information about the requirement brief's format,
        such as the regexes for chapter headings and individual requirements, as well as
        the bounding box for page to exclude headers. pdfplumber page is an input so margins are returned."""

        if self.pdfSchema == 'TfNSW':
            chapter_headings = r"(\n\s*\d[.]?\d?[.]?\d?\s+[A-Z].*)"
            requirements = r"(?sm)^([(]\w{0,4}[)]\s)(.*?)(?=^[(]\w{0,4}[)]\s)"
            page_margins = (0, 50, page.width, page.height - 70)

        try:
            return chapter_headings, requirements, page_margins,

        except NameError:
            print("Invalid PDF schema selected!")

    @staticmethod
    def scrape_pdfs(self, extract_tables=True):

        """Main function to convert document requirements to a dataframe."""
        input_pdfs = self.detect_input_pdfs(self.input_path)

        pdfreader = pdfplumber.open(self.input_path)
        pages = pdfreader.pages

        # Indexes
        table_index = 0

        for page in pages:

            chapter_headings, requirements, page_margins = self.pdf_schema_helper(page)

            # Crop header, extract text, locate tables to extract later/ remove text
            page = page.crop(page_margins)
            page_text = page.extract_text()
            tables = page.find_tables()
            tables_bbox = []

            for table in tables:
                table_index += 1
                tables_bbox.append(table.bbox)
                table_filename = f"TABLE {table_index}.png"
                temp_folder = self.output_path()
                table_filepath = os.path.join(self.input_path, "scrape_temp_folder")
                if not os.path.exists(table_filepath):
                    os.makedirs(table_filepath)
                page.crop(table.bbox).to_image()
            if extract_tables:
                pass
                # Find tables
