# -*- coding: utf-8 -*-
# @Time    : 2019/9/8 14:18
# @Author  : zhoujun
import cv2
import torch
import numpy as np

from .pypan import decode_torch as py_decode_torch,decode_numpy as py_decode_np
from .pypse2 import pse


def decode_np(preds, scale=1, threshold=0.7311, min_area=5):
    """
    在输出上使用sigmoid 将值转换为置信度，并使用阈值来进行文字和背景的区分
    :param preds: 网络输出
    :param scale: 网络的scale
    :param threshold: sigmoid的阈值
    :return: 最后的输出图和文本框
    """
    preds[:2, :, :] = torch.sigmoid(preds[:2, :, :])
    preds = preds.detach().cpu().numpy()
    score = preds[0].astype(np.float32)
    preds[0] = preds[0] > threshold  # text
    preds[1] = (preds[1] > threshold) * preds[0] # kernel

    label_num, label = cv2.connectedComponents(preds[1].astype(np.uint8), connectivity=4)
    label_values = []
    for label_idx in range(1, label_num):
        if np.sum(label == label_idx) < min_area:
            label[label == label_idx] = 0
            continue
        label_values.append(label_idx)

    import time
    start = time.time()
    pred = pse(preds, label, label_values)
    print(time.time()-start)
    bbox_list = []
    for label_value in label_values:
        points = np.array(np.where(pred == label_value)).transpose((1, 0))[:, ::-1]

        if points.shape[0] < 100 / (scale * scale):
            continue

        score_i = np.mean(score[pred == label_value])
        if score_i < 0.1:
            continue

        rect = cv2.minAreaRect(points)
        bbox = cv2.boxPoints(rect)
        bbox_list.append([bbox[1], bbox[2], bbox[3], bbox[0]])
    return pred, np.array(bbox_list)

def decode_torch(preds, scale=1, threshold=0.7311, min_area=5):
    """
    在输出上使用sigmoid 将值转换为置信度，并使用阈值来进行文字和背景的区分
    :param preds: 网络输出
    :param scale: 网络的scale
    :param threshold: sigmoid的阈值
    :return: 最后的输出图和文本框
    """
    preds[:2, :, :] = torch.sigmoid(preds[:2, :, :])
    score = preds[0].detach().cpu().numpy()
    preds[0] = preds[0] > threshold  # text
    preds[1] = (preds[1] > threshold).float() * preds[0] # kernel

    label_num, label = cv2.connectedComponents(preds[1].detach().cpu().numpy().astype(np.uint8), connectivity=4)
    label_values = []
    for label_idx in range(1, label_num):
        if np.sum(label == label_idx) < min_area:
            label[label == label_idx] = 0
            continue
        label_values.append(label_idx)
    import time
    start = time.time()
    label = torch.from_numpy(label.astype(float)).to(preds.device)
    pred = py_decode_torch(preds, label, label_values)
    pred = pred.cpu().numpy()
    print(time.time() - start)

    bbox_list = []
    for label_value in label_values:
        points = np.array(np.where(pred == label_value)).transpose((1, 0))[:, ::-1]

        if points.shape[0] < 800 / (scale * scale):
            continue

        score_i = np.mean(score[pred == label_value])
        if score_i < 0.93:
            continue

        rect = cv2.minAreaRect(points)
        bbox = cv2.boxPoints(rect)
        bbox_list.append([bbox[1], bbox[2], bbox[3], bbox[0]])
    return pred, np.array(bbox_list)
