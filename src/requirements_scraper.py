import os
import pdfplumber
import src.utilities as utilities
import re
import pandas as pd


# Methods to be accessed via the RequirementsScraper class

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
    margins based on value of preset"""
    available_presets = ['TfNSW']

    width = page.width
    height = page.height

    if preset in available_presets:
        if preset == 'TfNSW':
            page_margins = (0, 57, width, height - 70)
        return page_margins
    else:
        print(f"Page margin preset named {preset} not found!")
        return None


def requirement_patterns(preset='General'):
    available_presets = ["General", "TfNSW"]

    if preset in available_presets:

        requirements = ""

        if preset == "General":
            requirements = r"(?sm)^\s*([A-Z]\D|[(]\w*[)]).*?([.:;]\s*\n)"
        if preset == "TfNSW":
            requirements = r"(?sm)^([(]\w{0,4}[)]\s)(.*?)(?=^[(]\w{0,4}[)]\s)"
        return requirements
    else:
        print(f"Search pattern preset {preset} not found!")
        return None


def heading_patterns(preset="TfNSW"):
    """Returns a string that matches headings which may be compiled into
    a regex object"""
    available_presets = ["TfNSW", "RMS QA SPEC"]

    if preset in available_presets:
        chapter_headings = ""

        if preset == "TfNSW":
            chapter_headings = r"(\s*\n\s*\d[.]?\d?[.]?\d?\s+[A-Z].*)"

        if preset == "RMS QA SPEC":
            chapter_headings = r"(?m)((^\s*[A-Z]\d)|(^\d[.]?))([^\n].*)"

        return chapter_headings
    else:
        print(f"Search pattern preset {preset} not found!")
        return None


class Scraper:
    def __init__(self, input_pdf):
        self._input_path = input_pdf

        # Dataframe Columns
        self.__doc_col = "Document"
        self.__heading1 = "Heading 1"
        self.__heading2 = "Heading 2"
        self.__requirement = "Requirement Text"

        # Temporary folder for saving images

        self.__temp_image_folder = os.getcwd()

    def scrape_pdf(
            self,
            headings_str,
            requirements_str,
            # table_settings,
            extract_tables=True,
            page_margins_preset='TfNSW'
    ):
        """Main function to convert document requirements to a dataframe."""
        # Initiate DataFrame

        doc_col = "Document"
        heading_col = "Heading"
        requirement_col = "Requirement Text"

        df = utilities.create_df(self.__doc_col, self.__heading1, self.__heading2, self.__requirement)

        # Indexes / variables
        table_index = 0
        all_text = ""

        # Folder for saving images:

        if extract_tables:

            if not os.path.exists(self.__temp_image_folder):
                os.makedirs(self.__temp_image_folder)

        # Main function
        pdfreader = pdfplumber.open(self._input_path)
        pages = pdfreader.pages

        for page in pages:

            page_margins = pdf_page_margins(page, preset=page_margins_preset)

            # Crop header, extract text, locate tables to extract
            # later/remove text
            page = page.crop(page_margins)
            page_text = page.extract_text()
            tables = page.find_tables()

            # Extract text from page, remove text from page, extract table
            # to image if extract_tables=True, add to all_text
            for table in tables:
                table_index += 1
                table_text = utilities.extract_table_text(page, table)
                page_text = utilities.remove_table_text(page_text, table_text, table_index)

                if extract_tables:
                    utilities.table_to_image(page, table, table_index, self.__temp_image_folder)
            all_text += page_text

        # Find compile search strings into regex
        all_text = utilities.remove_cid_text(all_text)

        headings_re = re.compile(headings_str)
        requirements_re = re.compile(requirements_str)

        # Empty lists to hold match positions and text

        headings = []
        requirements = []

        # Return tuples with start position, end position and the text of matches as tuple[0],[1],[2] respectively.

        for match in headings_re.finditer(all_text):
            headings.append((match.start(), match.end(), match.group()))

        for match in requirements_re.finditer(all_text):
            requirements.append((match.start(), match.end(), match.group()))
        # Write to dataframe

        for i, current_heading in enumerate(headings):
            if i == 0:  # Skip first heading as no previous heading exists
                continue

            previous_heading = headings[i - 1]

            for requirement in requirements:
                last_heading = i == len(headings) - 1
                df = self._append_to_df(
                    df,
                    previous_heading,
                    current_heading,
                    requirement,
                    last_heading=last_heading
                )

        return df

    @staticmethod
    def df_to_excel(df, output_file, extract_tables=False):
        """Convert requirements dataframe to Excel file. Only
        use after generating dataframe using scrape_pdf()
        Overwrites output_file."""

        utilities.df_to_excel(df, output_file, extract_tables=extract_tables)

    def _append_to_df(self,
                      df,
                      previous_heading_tuple,
                      current_heading_tuple,
                      requirement_tuple,
                      last_heading=False,
                      ):
        """Writes the doc name, heading and requirement to dataframe in accordance with their positions. Treats
        last heading separately"""
        df_concat = df
        doc_name = os.path.basename(self._input_path)

        requirement_text = requirement_tuple[2].replace("\n", " ")
        if last_heading:
            if requirement_tuple[0] > current_heading_tuple[0]:
                heading_text = current_heading_tuple[2]
                new_row = pd.DataFrame(
                    {self.__doc_col: [doc_name], self.__heading1: [heading_text], self.__heading2: [""],
                     self.__requirement: [requirement_text]})

                df_concat = pd.concat([df, new_row])

        else:
            if previous_heading_tuple[0] < requirement_tuple[0] < current_heading_tuple[0]:
                heading_text = previous_heading_tuple[2]
                new_row = pd.DataFrame(
                    {self.__doc_col: [doc_name], self.__heading1: [heading_text], self.__heading2: [""],
                     self.__requirement: [requirement_text]})

                df_concat = pd.concat([df, new_row])

        return df_concat

    def dump_text(self, page_margins_preset='TfNSW'):
        all_text = ""
        table_index = 0

        pdf = pdfplumber.open(self._input_path)
        pages = pdf.pages

        for page in pages:
            # Crop header, extract text, locate tables to extract
            # later/remove text
            page_margins = pdf_page_margins(page, page_margins_preset)
            page = page.crop(page_margins)
            page_text = page.extract_text()
            tables = page.find_tables()

            # Extract text from page, remove text from page, extract table
            # to image if extract_tables=True, add to all_text
            for table in tables:
                table_index += 1
                table_text = utilities.extract_table_text(page, table)
                page_text = utilities.remove_table_text(page_text, table_text, table_index)
            all_text += page_text
        all_text = utilities.remove_cid_text(all_text)
        return all_text
