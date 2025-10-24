from flask import render_template
import pdfkit

## FUNÇÃO GLOBAL PDF ##
def gerar_pdf(template_name, **kwargs):
    rendered = render_template(template_name, **kwargs)
    config = pdfkit.configuration(wkhtmltopdf=r'C:/Arquivos de Programas/wkhtmltopdf/bin/wkhtmltopdf.exe')
    return pdfkit.from_string(rendered, False, configuration=config)