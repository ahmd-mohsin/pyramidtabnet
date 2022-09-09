"""
Cloned from:
            https://github.com/victorqribeiro/groupImg
MIT License

Copyright (c) 2018 Victor Ribeiro

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
"""

import os
import shutil
import glob
import math
import argparse
import warnings
import numpy as np
from PIL import Image
from tqdm import tqdm
from multiprocessing.dummy import Pool as ThreadPool
from multiprocessing import cpu_count

Image.MAX_IMAGE_PIXELS = None
warnings.simplefilter("ignore")


class KMeans:
    def __init__(self, k=3, size=False, resample=32):
        self.k = k
        self.cluster = []
        self.data = []
        self.end = []
        self.i = 0
        self.size = size
        self.resample = resample

    def manhattan_distance(self, x1, x2):
        s = 0.0
        for i in range(len(x1)):
            s += abs(float(x1[i]) - float(x2[i]))
        return s

    def euclidian_distance(self, x1, x2):
        s = 0.0
        for i in range(len(x1)):
            s += math.sqrt((float(x1[i]) - float(x2[i])) ** 2)
        return s

    def read_image(self, im):
        if self.i >= self.k:
            self.i = 0
        try:
            img = Image.open(im)
            osize = img.size
            img.thumbnail((self.resample, self.resample))
            v = [
                float(p) / float(img.size[0] * img.size[1]) * 100
                for p in np.histogram(np.asarray(img))[0]
            ]
            if self.size:
                v += [osize[0], osize[1]]
            pbar.update(1)
            i = self.i
            self.i += 1
            return [i, v, im]
        except Exception as e:
            print("Error reading ", im, e)
            return [None, None, None]

    def generate_k_means(self):
        final_mean = []
        for c in range(self.k):
            partial_mean = []
            for i in range(len(self.data[0])):
                s = 0.0
                t = 0
                for j in range(len(self.data)):
                    if self.cluster[j] == c:
                        s += self.data[j][i]
                        t += 1
                if t != 0:
                    partial_mean.append(float(s) / float(t))
                else:
                    partial_mean.append(float("inf"))
            final_mean.append(partial_mean)
        return final_mean

    def generate_k_clusters(self, folder):
        pool = ThreadPool(cpu_count())
        result = pool.map(self.read_image, folder)
        pool.close()
        pool.join()
        self.cluster = [r[0] for r in result if r[0] != None]
        self.data = [r[1] for r in result if r[1] != None]
        self.end = [r[2] for r in result if r[2] != None]

    def rearrange_clusters(self):
        isover = False
        while not isover:
            isover = True
            m = self.generate_k_means()
            for x in range(len(self.cluster)):
                dist = []
                for a in range(self.k):
                    dist.append(self.manhattan_distance(self.data[x], m[a]))
                _mindist = dist.index(min(dist))
                if self.cluster[x] != _mindist:
                    self.cluster[x] = _mindist
                    isover = False


ap = argparse.ArgumentParser()
ap.add_argument("--f", "--folder", required=True, help="Path to image folder.")
ap.add_argument("--k", "--kmeans", type=int, default=5, help="Number of clusters.")
ap.add_argument("--r", "--resample", type=int, default=256, help="Resampling size.")
ap.add_argument(
    "--s",
    default=False,
    action="store_true",
    help="Use size as a feature for clustering.",
)
ap.add_argument(
    "--m", "--move", default=False, action="store_true", help="Move instead of copying."
)
args = vars(ap.parse_args())
types = ("*.jpg", "*.JPG", "*.png", "*.jpeg")
imagePaths = []
folder = args["folder"]
if not folder.endswith("/"):
    folder += "/"
for files in types:
    imagePaths.extend(sorted(glob.glob(folder + files)))

nimages = len(imagePaths)
nfolders = int(math.log(args["kmeans"], 10)) + 1

if nimages <= 0:
    print("No images found!")
    exit()
if args["resample"] < 16 or args["resample"] > 256:
    print("-r should be a value between 16 and 256")
    exit()

pbar = tqdm(total=nimages)
k = KMeans(args["kmeans"], args["size"], args["resample"])
k.generate_k_clusters(imagePaths)
k.rearrange_clusters()
for i in range(k.k):
    try:
        os.makedirs(folder + "K_" + str(i + 1).zfill(nfolders))
    except:
        print("Folder already exists.")
action = shutil.copy
if args["move"]:
    action = shutil.move
for i in range(len(k.cluster)):
    action(k.end[i], folder + "/" + "K_" + str(k.cluster[i] + 1).zfill(nfolders) + "/")
