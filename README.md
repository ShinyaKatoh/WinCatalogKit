# Sequential pipeline scripts

このセットは、以下の 3 段階の処理を 1 本の Python ファイルから順番に実行するためのものです。

1. `phase_pick_configurable.py`  
   連続 WIN 波形を読み込み、SegPhase により P/S ピックを作成します。

2. `run_REAL_configurable.py`  
   SegPhase の P/S ピックを REAL に入力し、イベント association を行います。

3. `pola_win_configurable.py`  
   REAL の `phase_sel.txt` と WIN 波形を読み込み、PoViT により P 波初動極性を推定し、HYPOMH 用入力ファイルを作成します。

加えて、`run_sequential_pipeline.py` 内で `channel_HAGI` から REAL 用 station file を自動作成します。

## 実行方法

python run_sequential_pipeline.py


## 設定方法

`run_sequential_pipeline.py` の冒頭にある `CONFIG` を編集してください。

```python
CONFIG = {
    "win_dir": "./trg_20250401_HAGI",
    "pick_dir": "./pred_res",
    "final_output_dir": "./pred_res",

    "channel_file": "channel_HAGI",

    "real_station_file": "./station_for_REAL.dat",
    "make_real_station": True,
    "overwrite_real_station": True,
    "real_station_component": "U",
    "real_network": "CT",
    "real_channel": "HHZ",

    "real_ttime": "./REAL/tt_db/ttdb_JMA2001.txt",
    "real_binary": "./REAL/REAL",

    "segphase_model": "SegPhase/best_model.pth",
    "povit_model": "./PoViT/model_100Hz.pth",
    "device": "cuda:2",

    "p_threshold": 0.5,
    "s_threshold": 0.5,

    "real_year": "2025",　#カタログを作り始める日付
    "real_month": "4",
    "real_day": "1",
    "real_lat_ref": "34.475",　#解析領域の平均lat

    "skip_phase_pick": False,
    "skip_real_station": False,
    "skip_real": False,
    "skip_polarity": False,
}
```

## REAL 用 station file の作成

`channel_HAGI` の各行から、`U` 成分の観測点だけを使用して `station_for_REAL.dat` を作成します。
使用する列は、添付 notebook の処理と同じです。

```python
station = cols[3]
component = cols[4]
lat = cols[13]
lon = cols[14]
elev_km = float(cols[15]) / 1000.0
```

出力形式は以下です。

```text
longitude latitude network station channel elevation_km
```

例: \
networkとchannelは適当

```text
131.1234 34.5678 CT ABCD HHZ 0.123
```

## ファイル一覧

- `run_sequential_pipeline.py`  
  統合実行ファイル。通常はこのファイルだけを実行します。

- `make_REAL_station.py`  
  `channel_HAGI` から REAL 用 station file を作成する補助ファイルです。統合実行ファイルにも同じ処理を組み込んであります。

- `phase_pick_configurable.py`  
  SegPhase による P/S ピック作成処理です。

- `run_REAL_configurable.py`  
  REAL を実行する処理です。

- `pola_win_configurable.py`  
  PoViT による初動極性推定と HYPOMH 用入力ファイル作成処理です。

# pickファイルの追加項目の説明
#sで始まる観測値の⾏のフォーマット \
観測点コード、 P初動極性（データなしまた判定不可能は "N"）、P時刻(s)、P精度(s)、
S時刻(s)、S精度(s)、 F-P時間(s)、最⼤振幅、観測点緯度(度)、 経度(度)、⾼度(m)、P
の観測点補正(s)、Sの観測点補正(s)、 P波⾛時の出⼒確率値、 S波⾛時の出⼒確率値、
2列⽬のP初動極性である確率、2列⽬のP初動極性の不確実性、SegPhaseとPoViT-UQ
のP波⾛時位置のサンプル差
(3X, A10, 1X,A1, F8.3, F6.3, F8.3, F6.3, F6.1, E9.2, F11.5, F11.5, I7, F7.3, F7.3)
⿊⽂字はオリジナルのpickファイルと同じ、⾚⽂字で書かれた項⽬が新たに追加したもの
極性の使⽤基準
極性を使⽤する基準として2列⽬のP初動極性である確率、2列⽬のP初動極性の不確実
性を使⽤すると精度がいい極性のみを選別できる。詳細は、PoViT-UQの論⽂を参照。
SegPhaseとPoViT-UQのP波⾛時位置のサンプル差
両モデルが独⽴に推定した P 到着の サンプル index 差のこと、例えば100 Hzサンプリ
ングの観測点で1だった場合、読み取り差が0.01秒あることを⽰す。
この絶対値が 0 に近いほど同⼀箇所を読んでいると判断できる。値が⼤きい観測点は極
性を採⽤するかの判断材料になる。256 や 128 は PoViT-UQ で P 到着を決定できなか
ったことを表す。
