
プログラム名：Skeleton_Analysis_GUI
作成日付：2023.01.30
作成者：Yeon Je Yun (12401908038 )
説明：
	画像を読み込み、OpenPoseを用いて関節の座標を求める。
 	各関節の座標はCSVファイルにセーブされる。


設置
	1．ウェブでpythonを最新バージョンで設置
	2．ターミナルまたはコンソールを開く
	3．requirements.txtがあるフォルダまで移動する。
	4. pip3 install -r requirements.txt　を実行させる。


起動方法：基本
	1．ターミナルまたはコンソールを開く
	2．Skeleton_Analysis_GUI.py　があるフォルダまで移動する。
	3．python Skeleton_Analysis_GUI.py を実行する。

起動方法：Windows
	1．run_for_windows.bat　を実行する

起動方法：Mac
	1. command + spaceでterminalを検索、実行
	2. cd を入力しpythonファイルがあるフォルダをターミナルにドラッグ&ドロップ、Enterを押す。
	3. python Skeleton_Analysis_GUI.pywを入力、Enterを押す。

フォルダーツリー
	Skeleton_Analysis_GUI
	-models 分析に必要なモデルがあるフォルダ 	
	--body_25
 	以下は分析を回すと自動的に生成される。
 	-img_after
 	-csv
 	--coord
	--angle

注意事項
 	モデルフォルダは触らないでください。
 	必ず.pyファイルとモデルフォルダが同一フォルダに入るようにしてください。
	画像の読み込みは.jpgか.png限定です。

