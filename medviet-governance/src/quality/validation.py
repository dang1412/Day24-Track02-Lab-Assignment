# src/quality/validation.py
import re
import pandas as pd


def validate_anonymized_data(filepath: str, original_filepath: str = None) -> dict:
    """
    Validate anonymized data.
    Trả về dict: {"success": bool, "failed_checks": list, "stats": dict}
    """
    df = pd.read_csv(filepath)
    results = {
        "success": True,
        "failed_checks": [],
        "stats": {
            "total_rows": len(df),
            "columns": list(df.columns)
        }
    }

    # Check 1: CCCD trong anonymized phải khác CCCD gốc
    if original_filepath:
        df_orig = pd.read_csv(original_filepath)
        orig_cccds = set(df_orig["cccd"].astype(str).str.zfill(12))
        anon_cccds = set(df["cccd"].astype(str).str.zfill(12))
        leaked = orig_cccds & anon_cccds
        if leaked:
            results["success"] = False
            results["failed_checks"].append(
                f"Check 1 FAILED: {len(leaked)} original CCCDs still present in anonymized output"
            )

    # Check 2: Không có null values trong các cột quan trọng
    important_cols = ["patient_id", "benh", "ket_qua_xet_nghiem"]
    for col in important_cols:
        if col in df.columns:
            null_count = df[col].isnull().sum()
            if null_count > 0:
                results["success"] = False
                results["failed_checks"].append(
                    f"Check 2 FAILED: column '{col}' has {null_count} null values"
                )

    # Check 3: Số rows phải bằng original nếu có
    if original_filepath:
        df_orig = pd.read_csv(original_filepath)
        if len(df) != len(df_orig):
            results["success"] = False
            results["failed_checks"].append(
                f"Check 3 FAILED: row count mismatch {len(df)} vs {len(df_orig)}"
            )

    # Check 4: ket_qua_xet_nghiem trong khoảng hợp lệ [0, 50]
    if "ket_qua_xet_nghiem" in df.columns:
        out_of_range = df[
            (df["ket_qua_xet_nghiem"] < 0) | (df["ket_qua_xet_nghiem"] > 50)
        ]
        if len(out_of_range) > 0:
            results["success"] = False
            results["failed_checks"].append(
                f"Check 4 FAILED: {len(out_of_range)} rows have out-of-range test results"
            )

    # Check 5: benh phải thuộc danh sách hợp lệ
    valid_conditions = {"Tiểu đường", "Huyết áp cao", "Tim mạch", "Khỏe mạnh"}
    if "benh" in df.columns:
        invalid_benh = df[~df["benh"].isin(valid_conditions)]
        if len(invalid_benh) > 0:
            results["success"] = False
            results["failed_checks"].append(
                f"Check 5 FAILED: {len(invalid_benh)} rows have invalid 'benh' values"
            )

    # Check 6: Không có duplicate patient_id
    if "patient_id" in df.columns:
        dup_count = df["patient_id"].duplicated().sum()
        if dup_count > 0:
            results["success"] = False
            results["failed_checks"].append(
                f"Check 6 FAILED: {dup_count} duplicate patient_id values"
            )

    if results["success"]:
        results["message"] = "All validation checks passed"

    return results
