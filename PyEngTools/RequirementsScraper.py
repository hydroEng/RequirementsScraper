import os
import pdfplumber
from common import *
import re
import pandas as pd
import openpyxl


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


def _create_df(doc_col, heading_col, requirement_col):
    return pd.DataFrame(columns=[str(doc_col), str(heading_col), str(requirement_col)])


def _req_under_heading(
        previous_heading_tuple, current_heading_tuple, requirement_tuple, last_heading=False
):
    """Function checks if the requirement sits after previous_heading and before current_heading."""
    if last_heading:
        if requirement_tuple[0] > current_heading_tuple[1]:
            return True
    else:
        if previous_heading_tuple[1] < requirement_tuple[0] < current_heading_tuple[1]:
            return True
        else:
            return False


def _append_to_df(
        df,
        doc_name,
        previous_heading_tuple,
        current_heading_tuple,
        requirement_tuple,
        last_heading=False,
):
    """Writes the doc name, heading and requirement to dataframe in accordance with their positions. Treats
    last heading separately"""
    new_row = pd.Series()

    if last_heading:
        if requirement_tuple[0] > current_heading_tuple[0]:
            heading_text = current_heading_tuple[2]
            requirement_text = requirement_tuple[2]
            new_row = pd.Series([doc_name, heading_text, requirement_text])

    else:
        if previous_heading_tuple[0] < requirement_tuple[0] < current_heading_tuple[0]:
            heading_text = previous_heading_tuple[2]
            requirement_text = requirement_tuple[2]
            new_row = pd.Series([doc_name, heading_text, requirement_text])

    return df.append(new_row, ignore_index=True)


def _post_process_sheet(sheet_dir, extract_tables=True, table_folder=None):
    wb = openpyxl.load_workbook(sheet_dir)
    ws = wb.active
    if extract_tables and table_folder is None:
        raise ValueError('Require a directory for table_folder if extract_tables is True.')
    if extract_tables:
        pass

    else:
        pass


class RequirementsScraper:
    def __init__(self, input_path, output_path):
        self._input_path = input_path
        self._output_path = output_path

    @staticmethod
    def search_patterns(preset="TfNSW"):

        """Returns a tuple with chapter headings and requirements strings that can be compiled into
        a regex object"""
        available_presets = ["TfNSW"]

        if preset in available_presets:
            if preset == "TfNSW":
                chapter_headings = r"(\n\s*\d[.]?\d?[.]?\d?\s+[A-Z].*)"
                requirements = r"(?sm)^([(]\w{0,4}[)]\s)(.*?)(?=^[(]\w{0,4}[)]\s)"
                return chapter_headings, requirements
        else:
            print(f"Search pattern preset {preset} not found!")
            return None

    def scrape_pdfs(
            self,
            headings_str,
            requirements_str,
            table_settings,
            page_start,
            page_end,
            extract_tables=True,
    ):
        """Main function to convert document requirements to a dataframe."""
        input_pdfs = detect_input_pdfs(self._input_path)

        # Initiate DataFrame

        doc_col = "Document"
        heading_col = "Heading"
        requirement_col = "Requirement Text"

        df = _create_df(doc_col, heading_col, requirement_col)

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
            pages = pdfreader.pages[page_start:page_end]

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

            # Find compile search strings into regex

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
                    df = _append_to_df(
                        df,
                        input_pdf,
                        previous_heading,
                        current_heading,
                        requirement,
                        last_heading=last_heading,
                    )
        return df

    @staticmethod
    def df_to_excel(df, output_file, table_images=False):
        delete_dir(output_file)  # Delete output if it doesn't exist already.

        df.to_excel(output_file)
