import os
import pdfplumber
from common import *
import re
import pandas as pd
import openpyxl

reserved_table_keyword = '@@reserved_table'


# Helper functions
def _extract_table_text(page, table):
    table_text = page.crop(table.bbox).extract_text()
    return table_text


def _remove_table_text(page_text, table_text, table_number):
    updated_text = page_text.replace(table_text, f"\n{reserved_table_keyword} Table {table_number}.png")
    return updated_text


def _table_to_image(page, table, table_number, save_location, table_resolution=100):
    table_filepath = os.path.join(save_location, f"TABLE {table_number}.png")
    page.crop(table.bbox).to_image(resolution=table_resolution).save(table_filepath)


def _create_df(doc_col, heading1_col, heading2_col, requirement_col):
    return pd.DataFrame(columns=[str(doc_col), str(heading1_col), str(heading2_col), str(requirement_col)])


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


def _find_img_name_in_cell(cell,
                           img_extension='.png'
                           ):
    a = cell.value.find(reserved_table_keyword) + len(reserved_table_keyword)
    b = cell.value.find(img_extension) + len(img_extension)

    img_name = cell.value[a:b].strip()

    return img_name


def _insert_img_to_cell(img_dir,
                        cell_text,
                        cell,
                        ws
                        ):
    img = openpyxl.drawing.image.Image(img_dir)
    img.anchor = str(cell.coordinate)
    cell.value = cell_text
    ws.add_image(img)


def _post_process_sheet(
        sheet_dir,
        extract_tables=True,
        img_folder=None,
        table_text='Inserted_Table'
):
    wb = openpyxl.load_workbook(sheet_dir)
    ws = wb.active
    if extract_tables and img_folder is None:
        raise ValueError('Require a directory for table_folder if extract_tables is True.')

    # Replace reserved table keyword with an image of the table...

    for row in ws.rows:
        for cell in row:
            if cell.value is not None:
                if reserved_table_keyword in str(cell.value):
                    if extract_tables:
                        img_name = _find_img_name_in_cell(cell)
                        img_dir = os.path.join(img_folder, img_name)
                        _insert_img_to_cell(img_dir, table_text, cell, ws)
                    else:
                        cell.value = table_text


class Scraper:
    def __init__(self, input_pdf, output_path, temp_folder_name='temp_image_folder'):
        self._input_path = input_pdf
        self._output_path = output_path
        self._temp_image_folder = os.path.join(output_path, temp_folder_name)

        # Dataframe Columns
        self.__doc_col = "Document"
        self.__heading1 = "Heading 1"
        self.__heading2 = "Heading 2"
        self.__requirement = "Requirement Text"

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

    def scrape_pdf(
            self,
            headings_str,
            requirements_str,
            table_settings,
            extract_tables=True,
            page_margins_preset='TfNSW'
    ):
        """Main function to convert document requirements to a dataframe."""
        # Initiate DataFrame

        doc_col = "Document"
        heading_col = "Heading"
        requirement_col = "Requirement Text"

        df = _create_df(self.__doc_col, self.__heading1, self.__heading2, self.__requirement)

        # Indexes / variables
        table_index = 0
        all_text = ""

        # Folder for saving images:

        if extract_tables:
            temp_folder = os.path.join(self._output_path, self._temp_image_folder)

            if not os.path.exists(temp_folder):
                os.makedirs(temp_folder)

        # Main function
        pdfreader = pdfplumber.open(self._input_path)
        pages = pdfreader.pages

        for page in pages:

            page_margins = pdf_page_margins(page, preset=page_margins_preset)

            # Crop header, extract text, locate tables to extract
            # later/remove text
            # page = page.crop(page_margins)
            page_text = page.extract_text()
            tables = page.find_tables()

            # Extract text from page, remove text from page, extract table
            # to image if extract_tables=True, add to all_text
            for table in tables:
                table_index += 1
                table_text = _extract_table_text(page, table)
                page_text = _remove_table_text(page_text, table_text, table_index)

                if extract_tables:
                    _table_to_image(page, table, table_index, self._temp_image_folder)
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
            print('1')
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

    def df_to_excel(self, df, output_file, table_images=False):
        """Convert requirements dataframe to Excel file. Only
        use after generating dataframe using scrape_pdf()
        Overwrites output_file."""

        delete_dir(output_file)  # Delete output if it doesn't exist already.

        df.to_excel(output_file)

        _post_process_sheet(output_file, img_folder=self._temp_image_folder)

    def _append_to_df(self,
                      df,
                      previous_heading_tuple,
                      current_heading_tuple,
                      requirement_tuple,
                      last_heading=False,
                      ):
        """Writes the doc name, heading and requirement to dataframe in accordance with their positions. Treats
        last heading separately"""

        if last_heading:
            if requirement_tuple[0] > current_heading_tuple[0]:
                heading_text = current_heading_tuple[2]
                requirement_text = requirement_tuple[2]
                new_row = pd.DataFrame(
                    {self.__doc_col: [self._input_path], self.__heading1: [heading_text], self.__heading2: [""],
                     self.__requirement: [requirement_text]})

                return pd.concat([df, new_row])
        else:
            if previous_heading_tuple[0] < requirement_tuple[0] < current_heading_tuple[0]:
                heading_text = previous_heading_tuple[2]
                requirement_text = requirement_tuple[2]
                new_row = pd.DataFrame(
                    {self.__doc_col: [self._input_path], self.__heading1: [heading_text], self.__heading2: [""],
                     self.__requirement: [requirement_text]})

                return pd.concat([df, new_row])
