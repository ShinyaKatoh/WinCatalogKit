#!/usr/bin/env python3
"""
make_REAL_station.py

channel_HAGI のような WIN チャンネルリストから、REAL 用の station file を作成する補助スクリプトです。

入力の想定列は、既存 notebook と同じです。
- line.split()[3]  : station name
- line.split()[4]  : component
- line.split()[13] : latitude
- line.split()[14] : longitude
- line.split()[15] : elevation [m]

REAL 用出力形式:
    longitude latitude network station channel elevation_km

例:
    python make_REAL_station.py

通常は run_sequential_pipeline.py から自動的に呼ばれるため、単独実行は不要です。
"""

from __future__ import annotations

from pathlib import Path


def make_real_station_file(
    channel_file: str = "channel_HAGI",
    output_file: str = "./station_for_REAL.dat",
    component: str = "U",
    network: str = "CT",
    real_channel: str = "HHZ",
) -> int:
    """
    WIN チャンネルリストから REAL 用 station file を作成する。

    Parameters
    ----------
    channel_file : str
        入力チャンネルリスト。例: channel_HAGI
    output_file : str
        出力する REAL 用 station file。例: ./station_for_REAL.dat
    component : str
        REAL station file に採用する成分。通常は U 成分のみを使用する。
    network : str
        REAL に渡す network 名。
    real_channel : str
        REAL に渡す channel 名。

    Returns
    -------
    n_station : int
        出力した観測点数。
    """
    channel_path = Path(channel_file)
    output_path = Path(output_file)

    if not channel_path.exists():
        raise FileNotFoundError(f"channel file not found: {channel_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    n_station = 0
    with channel_path.open("r", encoding="utf-8", errors="replace") as f, output_path.open("w") as of:
        for raw in f:
            cols = raw.split()
            if len(cols) < 16:
                continue

            if cols[4] != component:
                continue

            station = cols[3]
            lat = cols[13]
            lon = cols[14]
            elev_km = float(cols[15]) / 1000.0

            of.write(f"{lon} {lat} {network} {station} {real_channel} {elev_km}\n")
            n_station += 1

    print(f"[make_REAL_station] wrote {n_station} stations -> {output_path}", flush=True)
    return n_station


if __name__ == "__main__":
    make_real_station_file()
