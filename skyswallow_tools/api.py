from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import BadZipFile

from flask import Blueprint, jsonify, request, send_file
from openpyxl.utils.exceptions import InvalidFileException

from tina_明细利润 import DataFormatError
from tina_明细利润 import process as process_profit
from tina_生成总表 import process as process_summary

from .auth import permission_required


api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.get("/health")
def health():
    return jsonify(status="ok")


@api_bp.post("/profit")
@permission_required("profit")
def create_profit_report():
    uploaded_file = request.files.get("file")

    if uploaded_file is None:
        return jsonify(error="没有收到上传文件。"), 400

    if not uploaded_file.filename:
        return jsonify(error="请选择一个文件。"), 400

    if not uploaded_file.filename.lower().endswith(".xlsx"):
        return jsonify(error="目前只支持 .xlsx 文件。"), 400

    try:
        with TemporaryDirectory(
            prefix="skyswallow_profit_"
        ) as temporary_directory:
            temporary_path = Path(temporary_directory)
            input_path = temporary_path / "input.xlsx"
            output_path = temporary_path / "result.xlsx"

            uploaded_file.save(input_path)

            processed, warnings, _ = process_profit(
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

    except (
        DataFormatError,
        InvalidFileException,
        BadZipFile,
    ) as error:
        return jsonify(error=str(error)), 400


@api_bp.post("/summary")
@permission_required("summary")
def create_summary_report():
    uploaded_file = request.files.get("file")
    ck_file = request.files.get("ck_file")

    if uploaded_file is None:
        return jsonify(error="没有收到明细文件。"), 400

    if not uploaded_file.filename:
        return jsonify(error="请选择已经计算过利润的明细文件。"), 400

    if not uploaded_file.filename.lower().endswith(".xlsx"):
        return jsonify(error="明细文件必须是 .xlsx 格式。"), 400

    if ck_file and ck_file.filename:
        if not ck_file.filename.lower().endswith(".xlsx"):
            return jsonify(error="C/K 标记文件必须是 .xlsx 格式。"), 400

    try:
        with TemporaryDirectory(
            prefix="skyswallow_summary_"
        ) as temporary_directory:
            temporary_path = Path(temporary_directory)
            input_path = temporary_path / "input.xlsx"
            output_path = temporary_path / "summary.xlsx"

            uploaded_file.save(input_path)

            ck_path = None

            if ck_file and ck_file.filename:
                ck_path = temporary_path / "ck_mapping.xlsx"
                ck_file.save(ck_path)

            order_count, client_count, warnings = process_summary(
                input_path,
                output_path,
                ck_path,
            )

            result_data = output_path.read_bytes()

        response = send_file(
            BytesIO(result_data),
            as_attachment=True,
            download_name="客户总表_处理结果.xlsx",
            mimetype=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
        )

        response.headers["X-Order-Count"] = str(order_count)
        response.headers["X-Client-Count"] = str(client_count)
        response.headers["X-Warning-Count"] = str(len(warnings))

        return response

    except (
        DataFormatError,
        InvalidFileException,
        BadZipFile,
    ) as error:
        return jsonify(error=str(error)), 400