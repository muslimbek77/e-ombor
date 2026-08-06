"""CSV eksport — hujjat, inventar va murojaat bo'limlarida ishlatiladi."""

import csv
from io import StringIO

from django.http import HttpResponse


def export_to_csv(filename, fieldnames, rows):
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)

    response = HttpResponse(output.getvalue(), content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
