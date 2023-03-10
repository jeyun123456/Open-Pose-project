#region ReadMe
# プログラム名：Skeleton_Analysis_GUI
# 作成日付：2023.01.30
# 作成者：Yeon Je Yun (12401908038 )
# 説明：
# 	画像を読み込み、OpenPoseを用いて関節の座標を求める。
# 	各関節の座標はCSVファイルにセーブされる。

# フォルダーツリー
# 	Skeleton_Analysis_GUI
# 	-models 分析に必要なモデルがあるフォルダ
# 	--body_25
# 	以下は分析を回すと自動的に生成される。
# 	-img_after
# 	-csv
# 	--coord
# 	--angle

# 注意事項
# 	モデルフォルダは触らないでください。
# 	必ず.pyファイルとモデルフォルダが同一フォルダに入るようにしてください。
# 	画像の読み込みは.jpgか.png限定です。

#endregion ReadMe	

# ライブラリーインポート
#region Import
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk

import os
import sys
import cv2
import numpy as np
import pandas as pd
import math

#endregion Import

# 無視してよし
#Relative Directory Setting
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# グローバル変数の設定
#region Keypoint setting
protoFile = "./models/body_25/pose_deploy.prototxt"
weightsFile = "./models/body_25/pose_iter_584000.caffemodel"

nPoints = 25

keypointsMapping = ["Nose","Neck","RShoulder", "RElbow", "RWrist", "LShoulder", "LElbow",
					"LWrist", "MidHip", "RHip","RKnee", "RAnkle", "LHip", "LKnee",
					"LAnkle", "REye", "LEye", "REar", "LEar", "LBigToe", "LSmallToe",
					"LHeel",  "RBigToe", "RSmallToe", "RHeel"]
					#9-15, 20-25
POSE_PAIRS = [[1,2], [1,5], [2,3], [3,4], [5,6], [6,7],	 
			[1,8], [8,9], [9,10], [10,11], [8,12], [12,13], [13,14], 
			[11,24], [11,22], [22,23], [14,21],[14,19],[19,20],  
			[1,0], [0,15], [15,17], [0,16], [16,18],
			[2,17], [5,18]]
mapIdx = [[40,41],[48,49],[42,43],[44,45],[50,51],[52,53],
		[26,27],[32,33],[28,29],[30,31],[34,35],[36,37],
		[38,39],[76,77],[72,73],[74,75],[70,71],[66,67],
		[68,69],[56,57],[58,59],[62,63],[60,61],[64,65],
		[46,47],[54,55]]
colors = [ [0,100,255], [0,100,255], [0,255,255], [0,100,255], [0,255,255], [0,100,255],
		[0,255,0], [255,200,100], [255,0,255], [0,255,0], [255,200,100], [255,0,255],
		[0,0,255], [255,0,0], [200,200,0], [255,0,0], [125,200,125], [125,200,0],
		[200,200,200],[200,100,200],[200,200,0],[0,200,0],[200,0,255],[0,250,125],
		[0,200,0],[0,120,200]]
#endregion Keypoint setting

# 関数の定義
#region Define

# フォルダ生成関数
# リターンなし
def createDirectory(directory):
		try:
			if not os.path.exists(directory):
				os.makedirs(directory)
		except OSError:
			print("Error: Failed to create the directory.")

# 関節に対するキーポイントリスト生成関数
# リターン：[(X,Y,確率)]
def getKeypoints(probMap, threshold=0.1):
	
	mapSmooth = cv2.GaussianBlur(probMap,(3,3),0,0)

	mapMask = np.uint8(mapSmooth>threshold)
	keypoints = []
	#find the blobs
	contours, _ = cv2.findContours(mapMask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

	#for each blob find the maxima
	for cnt in contours:
		blobMask = np.zeros(mapMask.shape)
		blobMask = cv2.fillConvexPoly(blobMask, cnt, 1)
		maskedProbMap = mapSmooth * blobMask
		#maxVal = 있을 확률
		#maxLoc = x,y좌표
		_, maxVal, _, maxLoc = cv2.minMaxLoc(maskedProbMap)
		keypoints.append(maxLoc + (probMap[maxLoc[1], maxLoc[0]],))
	return keypoints

# 関節をペアで結ぶ関数
# リターン：valid_pairs, invalid_pairs
def getValidPairs(output,frameWidth,frameHeight,detected_keypoints):
	valid_pairs = []
	invalid_pairs = []
	n_interp_samples = 10 # 벡터를 나눌 수
	paf_score_th = 0.1
	conf_th = 0.7
	# loop for every POSE_PAIR
	for k in range(len(mapIdx)):
		# A->B constitute a limb
		pafA = output[0, mapIdx[k][0], :, :]
		pafB = output[0, mapIdx[k][1], :, :]
		pafA = cv2.resize(pafA, (frameWidth, frameHeight))
		pafB = cv2.resize(pafB, (frameWidth, frameHeight))

		# Find the keypoints for the first and second limb
		candA = detected_keypoints[POSE_PAIRS[k][0]]
		candB = detected_keypoints[POSE_PAIRS[k][1]]
		nA = len(candA)
		nB = len(candB)

		# If keypoints for the joint-pair is detected
		# check every joint in candA with every joint in candB 
		# Calculate the distance vector between the two joints
		# Find the PAF values at a set of interpolated points between the joints
		# Use the above formula to compute a score to mark the connection valid
		
		if( nA != 0 and nB != 0):
			valid_pair = np.zeros((0,3))
			for i in range(nA):
				max_j=-1
				maxScore = -1
				found = 0
				for j in range(nB):
					# Find d_ij
					d_ij = np.subtract(candB[j][:2], candA[i][:2])
					norm = np.linalg.norm(d_ij)
					if norm:
						d_ij = d_ij / norm
					else:
						continue
					# Find p(u)
					interp_coord = list(zip(np.linspace(candA[i][0], candB[j][0], num=n_interp_samples),
											np.linspace(candA[i][1], candB[j][1], num=n_interp_samples)))
					# Find L(p(u))
					paf_interp = []
					for k in range(len(interp_coord)):
						paf_interp.append([pafA[int(round(interp_coord[k][1])), int(round(interp_coord[k][0]))],
										pafB[int(round(interp_coord[k][1])), int(round(interp_coord[k][0]))] ]) 
					# Find E
					paf_scores = np.dot(paf_interp, d_ij)
					avg_paf_score = sum(paf_scores)/len(paf_scores)
					
					# Check if the connection is valid
					# If the fraction of interpolated vectors aligned with PAF is higher then threshold -> Valid Pair  
					if ( len(np.where(paf_scores > paf_score_th)[0]) / n_interp_samples ) > conf_th :
						if avg_paf_score > maxScore:
							max_j = j
							maxScore = avg_paf_score
							found = 1
				# Append the connection to the list
				if found:			
					valid_pair = np.append(valid_pair, [[candA[i][3], candB[max_j][3], maxScore]], axis=0)
					
			# Append the detected connections to the global list
			valid_pairs.append(valid_pair)
		else: # If no keypoints are detected
			invalid_pairs.append(k)
			valid_pairs.append([])
	return valid_pairs, invalid_pairs

# キーポイントを人ごとに分離する関数
# リターン：valid_pairs, invalid_pairs
def getPersonwiseKeypoints(valid_pairs, invalid_pairs,keypoints_list):
	# the last number in each row is the overall score 
	personwiseKeypoints = -1 * np.ones((0, 26))

	for k in range(len(mapIdx)):
		if k not in invalid_pairs:
			partAs = valid_pairs[k][:,0]
			partBs = valid_pairs[k][:,1]
			indexA, indexB = np.array(POSE_PAIRS[k])

			for i in range(len(valid_pairs[k])): 
				found = 0
				person_idx = -1
				for j in range(len(personwiseKeypoints)):
					if personwiseKeypoints[j][indexA] == partAs[i]:
						person_idx = j
						found = 1
						break

				if found:
					personwiseKeypoints[person_idx][indexB] = partBs[i]
					personwiseKeypoints[person_idx][-1] += keypoints_list[partBs[i].astype(int), 2] + valid_pairs[k][i][2]

				# if find no partA in the subset, create a new subset
				elif not found and k < 24:
					row = -1 * np.ones(26)
					row[indexA] = partAs[i]
					row[indexB] = partBs[i]
					# add the keypoint_scores for the two keypoints and the paf_score 
					row[-1] = sum(keypoints_list[valid_pairs[k][i,:2].astype(int), 2]) + valid_pairs[k][i][2]
					personwiseKeypoints = np.vstack([personwiseKeypoints, row])
	return personwiseKeypoints	

#イメージを入力して分析結果を出す関数
# リターン：イメージ、キーポイントリスト
def processing(net, image_input, file_name):
	
	keypoints_list_list = np.array([])
	keypoints_list_list = np.append("frame,parts,x,y,prop",keypoints_list_list)
	key_list = np.array([])

	frameWidth = image_input.shape[1]
	frameHeight = image_input.shape[0]	

	# Fix the input Height and get the width according to the Aspect Ratio
	inHeight = 368
	inWidth = int((inHeight/frameHeight)*frameWidth)

	inpBlob = cv2.dnn.blobFromImage(image_input,
								1.0 / 255, (inWidth, inHeight),
							(0, 0, 0), swapRB=False, crop=False)

	net.setInput(inpBlob)
	output = net.forward()

	detected_keypoints = []
	keypoints_list = np.zeros((0,3))
	keypoint_id = 0
	threshold = 0.1

	#9-15, 20-25
	for part in range(nPoints):
		keypoints = []
		if (8 <= part<= 15) or (19 <= part <= 25):
			probMap = output[0,part,:,:]
			probMap = cv2.resize(probMap, (image_input.shape[1], image_input.shape[0]))
			keypoints = getKeypoints(probMap, threshold)
		if keypoints == []:
				tmp = ("{},{},{},{},{}".format(file_name[:-4], keypointsMapping[part], 0,0,0))
		else:
			maxp = keypoints[0]
			for p in keypoints:
				if abs(p[0]-frameWidth/2) < abs(maxp[0]-frameWidth/2) :
					maxp = p

			tmp = ("{},{},{},{},{}".format(file_name[:-4], keypointsMapping[part], maxp[0],maxp[1],maxp[2]))
			if keypoints[0][2] < 0:
				keypoints = []
				tmp = ("{},{},{},{},{}".format(file_name[:-4], keypointsMapping[part], 0,0,0))
		#print(tmp)

		key_list = np.append(key_list, tmp)
		keypoints_with_id = []
		for i in range(len(keypoints)):
			keypoints_with_id.append(keypoints[i] + (keypoint_id,))
			keypoints_list = np.vstack([keypoints_list, keypoints[i]])
			keypoint_id += 1

		detected_keypoints.append(keypoints_with_id)

	frameClone = image_input.copy()
	for i in range(nPoints):
		for j in range(len(detected_keypoints[i])):
			cv2.circle(frameClone, detected_keypoints[i][j][0:2], 5, colors[i], -1, cv2.LINE_AA)
	#cv2.imshow("Keypoints",frameClone)

	valid_pairs, invalid_pairs = getValidPairs(output,frameWidth,frameHeight,detected_keypoints)
	personwiseKeypoints = getPersonwiseKeypoints(valid_pairs, invalid_pairs,keypoints_list)

	for i in range(24):
		for n in range(len(personwiseKeypoints)):
			index = personwiseKeypoints[n][np.array(POSE_PAIRS[i])]
			if -1 in index:
				continue
			B = np.int32(keypoints_list[index.astype(int), 0])
			A = np.int32(keypoints_list[index.astype(int), 1])
			cv2.line(frameClone, (B[0], A[0]), (B[1], A[1]), colors[i], 3, cv2.LINE_AA)
	
	keypoints_list_list = np.append(keypoints_list_list, key_list)

	return frameClone, keypoints_list_list

# フォルダー検索用関数
# ボタンにリックされている。
def browse_file():
    file_path = filedialog.askdirectory(initialdir = "/", title = "Select folder")
    file_path_entry.delete(0, tk.END)
    file_path_entry.insert(0, file_path)
 
#  角度計算関数
def calculate_angle(p1, p2, p3):
    x1, y1 = p1[0], p1[1]
    x2, y2 = p2[0], p2[1]
    x3, y3 = p3[0], p3[1]

    dot_product = (x3 - x2) * (x2 - x1) + (y3 - y2) * (y2 - y1)
    magnitude = math.sqrt((x3 - x2) ** 2 + (y3 - y2) ** 2) * math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    cos_theta = dot_product / magnitude
    theta = math.acos(cos_theta)
    theta_degrees = math.degrees(theta)
    if math.isnan(theta_degrees):
        theta_degrees = 90
    return theta_degrees

# 関節の角度計算
# 右骨盤・左骨盤・水平線
# 右骨盤・右膝・右足首
# 右膝・右足首・垂直線
# 左骨盤・左膝・左足首
# 左膝・左足首・垂直線
# リターン：{"RHip-LHip-horizontal":0 ,"RHip-RKnee-RAnkle":0, "RKnee-RAnkle-vertical":0, "LHip-LKnee-LAnkle":0, "LKnee-LAnkle-vertical":0}
def Angle_get(list):
    RHip = np.array([int(list[10].split(",")[2]), int(list[10].split(",")[3])])
    LHip = np.array([int(list[13].split(",")[2]), int(list[13].split(",")[3])])
    RKnee = np.array([int(list[11].split(",")[2]), int(list[11].split(",")[3])])
    LKnee = np.array([int(list[14].split(",")[2]), int(list[14].split(",")[3])])
    RAnkle = np.array([int(list[12].split(",")[2]), int(list[12].split(",")[3])])
    LAnkle = np.array([int(list[15].split(",")[2]), int(list[15].split(",")[3])])
    Angle = {"RHip-LHip-horizontal":0 , "RHip-RKnee-RAnkle":0, "RKnee-RAnkle-vertical":0, "LHip-LKnee-LAnkle":0, "LKnee-LAnkle-vertical":0}
    
    Angle["RHip-LHip-horizontal"] = 90-calculate_angle(RHip,LHip,[LHip[0],RHip[1]])
    Angle["RHip-RKnee-RAnkle"] = 180-calculate_angle(RHip,RKnee,RAnkle)
    if RAnkle[0]<RKnee[0] : Angle["RHip-RKnee-RAnkle"] = -Angle["RHip-RKnee-RAnkle"]
    Angle["RKnee-RAnkle-vertical"] = 180-calculate_angle(RKnee,RAnkle,[RAnkle[0],RKnee[1]])
    Angle["LHip-LKnee-LAnkle"] = 180-calculate_angle(LHip,LKnee,LAnkle)
    if LAnkle[0]>LKnee[0] : Angle["LHip-LKnee-LAnkle"] = -Angle["LHip-LKnee-LAnkle"]
    Angle["LKnee-LAnkle-vertical"] = 180-calculate_angle(LKnee,LAnkle,[LAnkle[0],LKnee[1]])
    return Angle

# 分析ボタンにつながっている関数
# 実際に画像を読み込み、processing関数で処理、ファイルにセーブする。
def Analysis():
	if not os.path.exists(file_path_entry.get()):
		messagebox.showerror("Error", "The specified directory does not exist.")
	else:
		directory = file_path_entry.get()
		file_list = [file for file in os.listdir(directory) if file.endswith(".jpg") or file.endswith(".png")]

		resize = 10
		progressbar.start()
		progressbar.config(value=0, maximum=len(file_list),cursor="watch")

		for img_name in file_list:
			now_file_label.config(text=img_name+"  "+str(progressbar["value"]+1)+"/"+str(len(file_list)))
			now_file_label.update()

			img_path = directory+"/"+img_name

			createDirectory("./img_after")
			createDirectory("./csv/coord")
			createDirectory("./csv/angle")
   
			net = cv2.dnn.readNetFromCaffe(protoFile, weightsFile)

			img = cv2.resize(cv2.imread(img_path),dsize = None, fx=resize,fy=resize)

			outimg, keylist = processing(net, img, img_name)
			angle = Angle_get(keylist)
   
			cv2.imwrite("./img_after/after_"+img_name, outimg)

			np.savetxt("./csv/coord/"+img_name[:-4]+"_coord.csv", keylist, fmt = "%s")

			df1 = pd.DataFrame([angle])
			df2 = pd.DataFrame([{"name":img_name}])
			df = pd.concat([df2,df1],axis=1)
			df.to_csv("./csv/angle/"+img_name[:-4]+"_angle.csv", index=False)
			progressbar.update()
   
		if int(progressbar["value"])==0:now_file_label.config(text="complete")
		progressbar["cursor"]="arrow"
		progressbar.stop()

# CSVファイルを合併する関数
def Csv_Merge():
	df_list = []
	directory = "./csv/angle/"
	file_list = [file for file in os.listdir(directory) if file.endswith(".csv")]
	progressbar.config(value=0, maximum=len(file_list),cursor="watch")
	for csv_file in file_list:
		now_file_label.config(text=csv_file+"  "+str(progressbar["value"]+1)+"/"+str(len(file_list)))
		now_file_label.update()
		df = pd.read_csv(directory + csv_file)
		df_list.append(df)
		progressbar["value"] += 1
	if int(progressbar["value"])==(0 or 6):now_file_label.config(text="complete")
	progressbar["cursor"]="arrow"
	progressbar.stop()

	merged_df = pd.concat(df_list)

	merged_df.to_csv('Angle_merged.csv', index=False)

#endregion Define

# GUIの設定
#region TK
root = tk.Tk()
root.title("File Browse")

frame1 = tk.Frame(root)
frame1.pack()

file_path_label = tk.Label(frame1, text="File path:")
file_path_label.grid(row = 0, column=0)

file_path_entry = tk.Entry(frame1, text = "/Users/isaka-lab/Desktop/CODE/Skeleton_Analysis_Gui/basic")
file_path_entry.grid(row = 0, column=1)

browse_button = tk.Button(frame1, text="Browse", command=browse_file)
browse_button.grid(row=0, column=2)

analysis_button = tk.Button(frame1, text="Analysis", command=Analysis)
analysis_button.grid(row=1, column=1)

csv_merge_button = tk.Button(frame1, text="Merge Angle Csv", command=Csv_Merge)
csv_merge_button.grid(row=1, column=2)

now_file_label = tk.Label(frame1, text="File Name 0/0")
now_file_label.grid(row=2, column=1)

progressbar = ttk.Progressbar(frame1)
progressbar.grid(row=3, column = 0, columnspan=3, sticky = tk.W+tk.E)

#Start the Tkinter event loop with this
frame1.mainloop()
#endregion TK