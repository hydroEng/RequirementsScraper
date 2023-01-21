import RequirementsScraper
import common
import warnings
import os
import pandas as pd

warnings.simplefilter(action='ignore', category=FutureWarning)

input_path = r"/home/Taha/PyEngTools/PyEngTools/Macq park reqts/OCR_/"
output_path = r'./'


# input_pdfs = []
#
# for file in os.listdir(r"/home/Taha/PyEngTools/PyEngTools/Macq park reqts/"):
#     if file.endswith('.pdf'):
#         input_pdfs.append(os.path.join("/home/Taha/PyEngTools/PyEngTools/Macq park reqts/", file))
#
# output_pdfs = r"/home/Taha/PyEngTools/PyEngTools/Macq park reqts/"
#
# common.ocr_pdfs(input_pdfs, output_pdfs)


def subroutine():
    df = pd.DataFrame()
    for file in os.listdir(input_path):
        if file.endswith('.pdf'):
            scraper = RequirementsScraper.Scraper(input_pdf=os.path.join(input_path, file),
                                                  output_path=output_path)

            headings = scraper.heading_patterns(preset="TfNSW")
            requirements = scraper.requirement_patterns(preset='General')

            table_settings = common.table_settings()

            df1 = scraper.scrape_pdf(headings_str=headings,
                                    requirements_str=requirements,
                                    table_settings=table_settings,
                                    extract_tables=False)
            df = pd.concat([df,df1],ignore_index=True)

    scraper.df_to_excel(df, 'dataframe.xlsx', extract_tables=False)
    # scraper.df_to_excel(df, 'dataframe.xlsx')


def textroutine():
    scraper = RequirementsScraper.Scraper(input_pdf=input_path,
                                          output_path=output_path)

    x = scraper.dump_text()
    print(x)


# 0 = generate excel
# 1 = debug

RUN = 0

if __name__ == "__main__":

    if RUN == 0:
        subroutine()
    else:
        textroutine()
