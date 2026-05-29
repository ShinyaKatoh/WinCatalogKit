#!/usr/bin/env python3
"""
run_sequential_pipeline.py

3つの Python 処理を逐次的に実行する統合スクリプトです。
コマンドライン引数は使用せず、このファイル冒頭の CONFIG のみで設定します。

実行順序
--------
1. phase_pick_configurable.py
   1分単位の連続 WIN 波形を読み込み、SegPhase により P/S ピックを検出します。
   出力先には CT.{station}.P.txt と CT.{station}.S.txt が作成されます。

2. make_REAL_station.py 相当の処理
   channel_HAGI から REAL 用 station file を自動作成します。
   出力例: station_for_REAL.dat

3. run_REAL_configurable.py
   1で作成した P/S ピックと、2で作成した station file を REAL に入力し、
   イベント association を行います。
   通常、pick_dir 内に phase_sel.txt が作成されます。

4. pola_win_configurable.py
   REAL の phase_sel.txt と WIN 波形を読み込み、PoViT による P 波初動極性推定を行います。
   HYPOMH 用入力ファイルを final_output_dir/res_pre_pick に出力します。

使い方
------
    python run_sequential_pipeline.py

設定を変える場合は、下の CONFIG を編集してください。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# =============================================================================
# User settings
# =============================================================================
CONFIG = {
    # 入出力ディレクトリ
    "win_dir": "./trg_20250401_HAGI",
    "pick_dir": "./pred_res",
    "final_output_dir": "./pred_res",

    # WIN 読み込み用チャンネルリスト
    "channel_file": "channel_HAGI.list",

    # REAL 用 station file
    # このファイルは channel_file から自動作成する。
    "real_station_file": "./station_for_REAL.dat",
    "make_real_station": True,
    "overwrite_real_station": True,
    "real_station_component": "U",
    "real_network": "CT",
    "real_channel": "HHZ",

    # REAL 関連ファイル
    "real_ttime": "./REAL/tt_db/ttdb_JMA2001.txt",
    "real_binary": "./REAL/REAL",

    # モデル
    "segphase_model": "SegPhase_V2_JP/best_model.pth",
    "povit_model": "PoViT/model_100Hz.pth",
    "device": "cuda:2",

    # SegPhase ピーク検出閾値
    "p_threshold": 0.5,
    "s_threshold": 0.5,

    # REAL -D の設定
    "real_year": "2025",
    "real_month": "4",
    "real_day": "1",
    "real_lat_ref": "34.475",

    # 実行制御
    "skip_phase_pick": False,
    "skip_real_station": False,
    "skip_real": False,
    "skip_polarity": False,
}
# =============================================================================


def make_real_station_file(
    channel_file: str,
    output_file: str,
    component: str = "U",
    network: str = "CT",
    real_channel: str = "HHZ",
) -> int:
    """
    channel_HAGI から REAL 用 station file を作成する。

    入力 channel file の列は、添付 notebook の処理に合わせて以下を使用する。
        cols[3]  : station name
        cols[4]  : component
        cols[13] : latitude
        cols[14] : longitude
        cols[15] : elevation [m]

    REAL station file の出力形式:
        longitude latitude network station channel elevation_km
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


def print_step(title: str) -> None:
    """処理ステップを見やすく表示する。"""
    print("\n" + "=" * 100, flush=True)
    print(title, flush=True)
    print("=" * 100, flush=True)


def main() -> None:
    """CONFIG に基づいて、phase_pick → REAL station 作成 → REAL → polarity 推定を順番に実行する。"""
    cfg = CONFIG

    script_dir = Path(__file__).resolve().parent
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))

    win_dir = Path(cfg["win_dir"])
    pick_dir = Path(cfg["pick_dir"])
    final_output_dir = Path(cfg["final_output_dir"])
    channel_file = cfg["channel_file"]
    real_station_file = cfg["real_station_file"]

    pick_dir.mkdir(parents=True, exist_ok=True)
    final_output_dir.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------------------
    # 1. SegPhase phase picking
    # -------------------------------------------------------------------------
    if not cfg["skip_phase_pick"]:
        print_step("[1/4] phase picking by SegPhase")
        from phase_pick_configurable import run_phase_pick

        run_phase_pick(
            input_dir=str(win_dir),
            output_dir=str(pick_dir),
            station_file=channel_file,
            model_path=cfg["segphase_model"],
            device=cfg["device"],
            p_threshold=cfg["p_threshold"],
            s_threshold=cfg["s_threshold"],
        )
    else:
        print_step("[1/4] skip phase picking")

    # -------------------------------------------------------------------------
    # 2. Make REAL station file from channel_HAGI
    # -------------------------------------------------------------------------
    if not cfg["skip_real_station"]:
        print_step("[2/4] make REAL station file from channel file")

        output_path = Path(real_station_file)
        if cfg["make_real_station"] and (cfg["overwrite_real_station"] or not output_path.exists()):
            make_real_station_file(
                channel_file=channel_file,
                output_file=real_station_file,
                component=cfg["real_station_component"],
                network=cfg["real_network"],
                real_channel=cfg["real_channel"],
            )
        else:
            print(f"[make_REAL_station] use existing file: {output_path}", flush=True)
    else:
        print_step("[2/4] skip REAL station file creation")

    # -------------------------------------------------------------------------
    # 3. REAL association
    # -------------------------------------------------------------------------
    if not cfg["skip_real"]:
        print_step("[3/4] event association by REAL")
        from run_REAL_configurable import main as run_real

        run_real(
            str(pick_dir),
            year=cfg["real_year"],
            mon=cfg["real_month"],
            day=cfg["real_day"],
            lat_ref=cfg["real_lat_ref"],
            station_file=real_station_file,
            ttime=cfg["real_ttime"],
            real_binary=cfg["real_binary"],
        )
    else:
        print_step("[3/4] skip REAL")

    # -------------------------------------------------------------------------
    # 4. Polarity estimation and HYPOMH input creation
    # -------------------------------------------------------------------------
    if not cfg["skip_polarity"]:
        print_step("[4/4] polarity estimation and HYPOMH input creation")
        from pola_win_configurable import load_povit_model, main as run_polarity, read_event_pick_file

        phase_sel = pick_dir / "phase_sel.txt"
        if not phase_sel.exists():
            raise FileNotFoundError(f"phase_sel.txt not found: {phase_sel}")

        events_df, picks_df = read_event_pick_file(str(phase_sel))
        print(events_df.head(), flush=True)
        print(picks_df.head(), flush=True)

        model100_P, device = load_povit_model(cfg["povit_model"], cfg["device"])
        run_polarity(
            events_df,
            picks_df,
            str(final_output_dir),
            win_root=str(win_dir),
            station_file=channel_file,
            model100_P=model100_P,
            device=device,
        )
    else:
        print_step("[4/4] skip polarity estimation")

    print("\n[pipeline] all requested steps finished", flush=True)


if __name__ == "__main__":
    main()
