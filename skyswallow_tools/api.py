from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import BadZipFile

from flask import Blueprint, jsonify, request, send_file
from openpyxl.utils.exceptions import InvalidFileException

from tina_明细利润 import DataFormatError, process


api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.get("/health")
def health():
    return jsonify(status="ok")


@api_bp.post("/profit")
def create_profit_report():
    uploaded_file = request.files.get("file")

    if uploaded_file is None:
        return jsonify(error="没有收到上传文件。"), 400

    if not uploaded_file.filename:
        return jsonify(error="请选择一个文件。"), 400

    if not uploaded_file.filename.lower().endswith(".xlsx"):
        return jsonify(error="目前只支持 .xlsx 文件。"), 400

    try:
        with TemporaryDirectory(prefix="skyswallow_") as temporary_directory:
            temporary_path = Path(temporary_directory)
            input_path = temporary_path / "input.xlsx"
            output_path = temporary_path / "result.xlsx"

            uploaded_file.save(input_path)

            processed, warnings, _ = process(
                input_path,
                output_path,
                backup=False,
            )

            if processed == 0:
                return jsonify(
                    error="没有找到可以处理的明细利润表。",
                    warnings=warnings,
                ), 400

            result_data = output_path.read_bytes()

        response = send_file(
            BytesIO(result_data),
            as_attachment=True,
            download_name="明细利润_处理结果.xlsx",
            mimetype=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
        )

        response.headers["X-Processed-Blocks"] = str(processed)
        response.headers["X-Warning-Count"] = str(len(warnings))

        return response

    except (DataFormatError, InvalidFileException, BadZipFile) as error:
        return jsonify(error=str(error)), 400