
プログラム名：Skeleton_Analysis_GUI
作成日付：2023.01.30
作成者：Yeon Je Yun (12401908038 )
説明：
	画像を読み込み、OpenPoseを用いて関節の座標を求める。
 	各関節の座標はCSVファイルにセーブされる。

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
