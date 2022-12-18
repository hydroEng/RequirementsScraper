# Scratch area

for pdf in pdfDir:
    df = PdfTabler.read_requirements(pdf, tables=True)
    df.to_excel()