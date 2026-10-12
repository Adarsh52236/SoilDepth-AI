"""Unit tests for multi-format tabular ingestion and chunked streaming."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from soildepth_preprocessing.readers import (
    CorruptFileError,
    FileNotFoundCustomError,
    UnsupportedFormatError,
    detect_file_format,
    read_tabular,
    read_tabular_chunks,
)


@pytest.fixture
def sample_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "station_id": ["S1", "S2", "S3", "S4", "S5"],
            "soil_moisture": [0.22, 0.28, 0.19, 0.35, 0.31],
            "latitude": [45.1, 45.2, 45.3, 45.4, 45.5],
            "longitude": [9.1, 9.2, 9.3, 9.4, 9.5],
        }
    )


def test_detect_file_format(tmp_path: Path) -> None:
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("a,b\n1,2")
    assert detect_file_format(csv_file) == "csv"

    tsv_file = tmp_path / "data.tsv"
    tsv_file.write_text("a\tb\n1\t2")
    assert detect_file_format(tsv_file) == "tsv"

    parquet_file = tmp_path / "data.parquet"
    pd.DataFrame({"x": [1]}).to_parquet(parquet_file)
    assert detect_file_format(parquet_file) == "parquet"

    # Unsupported format
    unknown_file = tmp_path / "data.xyz"
    unknown_file.write_text("hello")
    with pytest.raises(UnsupportedFormatError):
        detect_file_format(unknown_file)


def test_read_csv(tmp_path: Path, sample_dataframe: pd.DataFrame) -> None:
    file_path = tmp_path / "test.csv"
    sample_dataframe.to_csv(file_path, index=False)

    df_read = read_tabular(file_path)
    assert len(df_read) == 5
    assert list(df_read.columns) == list(sample_dataframe.columns)


def test_read_tsv(tmp_path: Path, sample_dataframe: pd.DataFrame) -> None:
    file_path = tmp_path / "test.tsv"
    sample_dataframe.to_csv(file_path, sep="\t", index=False)

    df_read = read_tabular(file_path)
    assert len(df_read) == 5
    assert df_read["station_id"].tolist() == ["S1", "S2", "S3", "S4", "S5"]


def test_read_parquet(tmp_path: Path, sample_dataframe: pd.DataFrame) -> None:
    file_path = tmp_path / "test.parquet"
    sample_dataframe.to_parquet(file_path, index=False)

    df_read = read_tabular(file_path)
    assert len(df_read) == 5
    assert df_read["soil_moisture"].iloc[0] == pytest.approx(0.22)


def test_read_json_and_jsonl(tmp_path: Path, sample_dataframe: pd.DataFrame) -> None:
    # Standard JSON
    json_path = tmp_path / "test.json"
    sample_dataframe.to_json(json_path)
    df_json = read_tabular(json_path)
    assert len(df_json) == 5

    # JSON Lines
    jsonl_path = tmp_path / "test.jsonl"
    sample_dataframe.to_json(jsonl_path, orient="records", lines=True)
    df_jsonl = read_tabular(jsonl_path)
    assert len(df_jsonl) == 5


def test_read_excel(tmp_path: Path, sample_dataframe: pd.DataFrame) -> None:
    file_path = tmp_path / "test.xlsx"
    sample_dataframe.to_excel(file_path, index=False)

    df_read = read_tabular(file_path)
    assert len(df_read) == 5
    assert "station_id" in df_read.columns


def test_chunked_reading_csv(tmp_path: Path, sample_dataframe: pd.DataFrame) -> None:
    file_path = tmp_path / "large.csv"
    sample_dataframe.to_csv(file_path, index=False)

    chunks = list(read_tabular_chunks(file_path, chunk_size=2))
    assert len(chunks) == 3
    assert len(chunks[0]) == 2
    assert len(chunks[1]) == 2
    assert len(chunks[2]) == 1


def test_chunked_reading_parquet(tmp_path: Path, sample_dataframe: pd.DataFrame) -> None:
    file_path = tmp_path / "large.parquet"
    sample_dataframe.to_parquet(file_path, index=False)

    chunks = list(read_tabular_chunks(file_path, chunk_size=2))
    assert sum(len(c) for c in chunks) == 5


def test_file_not_found() -> None:
    with pytest.raises(FileNotFoundCustomError):
        read_tabular("non_existent_file.csv")


def test_corrupt_file_handling(tmp_path: Path) -> None:
    bad_file = tmp_path / "bad.parquet"
    bad_file.write_text("Not a real parquet binary header")
    with pytest.raises(CorruptFileError):
        read_tabular(bad_file)


def test_read_ismn_stm_header_values(tmp_path: Path) -> None:
    stm_content = (
        "SMOSMANIA SMOSMANIA Narbonne 43.15000 2.95670 112.00 0.05 0.05 ThetaProbe-ML2X\n"
        "2007/01/01 01:00 0.2140 U M\n"
        "2007/01/01 02:00 0.2135 G M\n"
    )
    file_path = tmp_path / "test_sensor.stm"
    file_path.write_text(stm_content, encoding="utf-8")

    df = read_tabular(file_path)
    assert len(df) == 2
    assert "station_id" in df.columns
    assert df["station_id"].iloc[0] == "Narbonne"
    assert df["latitude"].iloc[0] == 43.15
    assert df["depth_from_m"].iloc[0] == 0.05
    assert df["soil_moisture"].iloc[0] == 0.2140
    assert df["quality_flag"].iloc[1] == "G"


def test_read_ismn_stm_ceop(tmp_path: Path) -> None:
    ceop_content = (
        "2013/08/13 10:00 2013/08/13 10:00 FR_Aqui FR_Aqui fraye 44.46700 -0.72690 52.42 0.05 0.05 0.0345 G M\n"
        "2013/08/13 11:00 2013/08/13 11:00 FR_Aqui FR_Aqui fraye 44.46700 -0.72690 52.42 0.05 0.05 0.0787 G M\n"
    )
    file_path = tmp_path / "test_ceop.stm"
    file_path.write_text(ceop_content, encoding="utf-8")

    df = read_tabular(file_path)
    assert len(df) == 2
    assert df["station_id"].iloc[0] == "fraye"
    assert df["soil_moisture"].iloc[0] == 0.0345
