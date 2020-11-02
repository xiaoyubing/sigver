#!/usr/bin/env python
# encoding: utf-8
"""
@author: xyb
@license: (C) Copyright 2020, gjj.
@contact: 422749700@qq.com
@software: 
@file: gen_user_sign_data.py
@time: 2020/5/6 下午8:10
@desc: 生成用户的签名数据，使用采集的用户单字数据进行生成。
        1.先找一个字谢了多个的用户数据，来生成同一个人的签名。
        2.找不同人的同一个字签名认为是模仿笔记签名。
"""
import os
import random
from PIL import Image
import numpy as np
import struct
import random

# /ocr/shouji/class_user_characters/
all_use_user_data_root_path = '/ocr/shouji/class_user_characters/'  # 所有用户的手写数据对应文件夹char_imgs_3times中的图片数据


def deal_width_img(gray, random_padd=False, imagesize=(60, 60)):
    """
    处理传入的img,将img缩放到统一尺寸
    :param gray: 需要处理的灰度手写单子图
    :param random_padd: 随机间距
    :param imagesize: 图片统一签名尺寸
    :return:
    """
    width, height = gray.size
    new_img = np.ones((imagesize[0], imagesize[1]), dtype=np.float) * 255  # 构造一个二值化空白图像

    if height > width:
        scal = height / imagesize[0]
    else:
        scal = width / imagesize[1]

    s_h = int(height / scal)
    s_w = int(width / scal)

    if height > width:
        s_h = imagesize[1]
    else:
        s_w = imagesize[0]

    result = gray.resize((s_w, s_h), Image.ANTIALIAS)  # PIL是用宽, 高
    result = np.array(result, 'f')
    padd_left = 0
    padd_top = 0

    if height > width:  # 高度沾满,只在宽度上摆中间
        if random_padd:
            padd_left = random.randint(0, int((imagesize[1] - s_w) / 2))
        else:
            padd_left = int((imagesize[1] - s_w) / 2)
        new_img[:, padd_left:padd_left + s_w] = result
    else:  # 宽度沾满,只在高度上摆中间
        if random_padd:
            padd_top = random.randint(0, int((imagesize[0] - s_h) / 2))
        else:
            padd_top = int((imagesize[0] - s_h) / 2)

        new_img[padd_top:padd_top + s_h, :] = result

    result_img = Image.fromarray(np.uint8(new_img))
    # result_img.save('444.jpg', "JPEG")
    return result_img


def get_all_user_char_data(img_data_path):
    """
     扫描数据路径img_data_path，将该路径下面的
    :param img_data_path: 单字图片路径
    :return: 返回每个字对应的所有图片文件列表和每个字对应的所有笔迹json文件列表
    """
    char_image_path = {}  # 每个字对应的所有图片文件列表
    char_json_path = {}  # 每个字对应的所有笔迹json文件列表
    if not os.path.exists(img_data_path):
        print('data_path:', img_data_path, '不存在')
    for dirpath, dirnames, filenames in os.walk(img_data_path):
        for name in filenames:
            _, ext = os.path.splitext(name)
            ext = ext.lower()
            if ext == '.jpg' or ext == '.jpeg' or ext == '.png':
                image_path = os.path.join(dirpath, name)
                strokes_json_path = image_path.replace('class_user_characters', 'Word_Jsons_filter').replace('.jpg',
                                                                                                             '.json')
                tag = strokes_json_path.split("_")[-1].split(".json")[0]
                if tag in char_image_path.keys():
                    image_path_list = char_image_path[tag]
                else:
                    image_path_list = []
                image_path_list.append(image_path)
                char_image_path[tag] = image_path_list

                if tag in char_json_path.keys():
                    json_path_list = char_json_path[tag]
                else:
                    json_path_list = []
                json_path_list.append(strokes_json_path)
                char_json_path[tag] = json_path_list
    return char_image_path, char_json_path


def gen_user_sign_data(user_name, use_user_data, result_img_path, idx=None, number_of_name=10):
    """
    生成用户的真实签名和伪造签名数据。
    :param user_name: 需要生成的签名图片
    :param use_user_data: 使用那个用户的手写数据
    :param result_img_path: 生成的数据存储的文件夹
    :param number_of_name: 需要生成的签名数量
    :return:
    """
    user_name = user_name.strip()  # 去除空格
    use_user_data = use_user_data.strip().upper()  # 去除空格,且统一转换大写
    print(user_name, use_user_data)

    char_image_path = {}  # 该用户的所有图片文件列表
    char_json_path = {}  # 该用户的所有笔记json文件列表
    use_user_data_root_path = os.path.join(all_use_user_data_root_path, use_user_data)
    char_image_path, char_json_path = get_all_user_char_data(use_user_data_root_path)

    # char_image_path_file = open('char_image_path.json', 'w', encoding='utf-8')
    # json.dump(char_image_path, char_image_path_file)
    # char_json_path_file = open('char_json_path.json', 'w', encoding='utf-8')
    # json.dump(char_json_path, char_json_path_file)

    user_name_char_arr = list(user_name)
    # result_img = np.ones((len(user_name_char_arr) * 60, 60), dtype=np.float) * 255  # 构造一个二值化空白图像
    result_img = Image.new('RGB', (len(user_name_char_arr) * 60, 60))  # 创建一个新图
    for n in range(number_of_name):
        tag_code = ''
        for i, user_name_char in enumerate(user_name_char_arr):
            random_image_path = random.choice(char_image_path[user_name_char])
            img0 = Image.open(random_image_path)
            img0 = img0.convert("L")

            # TODO 修改此处为高度统一到60，字与字之间的宽度在阈值之内随机变化。组成宽度不一的签名图片
            img0 = deal_width_img(img0, random_padd=True)
            result_img.paste(img0, (i * 60, 0))
            tag_code += str(struct.unpack(">H", user_name_char.encode('gb2312'))[0])

        final_result_img_path = result_img_path + '_' + str(n + 1) + '.png'
        if idx:
            final_result_img_path = result_img_path + '_' + str(idx) + '.png'
        result_img.save(final_result_img_path)  # 保存新图


if __name__ == '__main__':
    use_user_data_arr = ['ex-zhaoyuanhang001', 'xiaoyubin462', 'xuyang006', 'ex-chenling005', 'LIJIULIN107',
                         'YANGJIANG002', 'LIUQIUJU574', 'GUANMIN', 'WANGZUHUA225', 'EX-ZHAOWU001', 'LICAN645',
                         'LIANGYAN253', 'ZHANGJINGUO004', 'LIUSONGLING004', 'LILIXIA026', 'EX-ZHANGHENG007',
                         'YANGJIONG686']

    # TODO
    # 每个人生成4个自己的姓名,生成4个伪造的姓名
    # 4个自己的姓名用两次写的字,4个伪造的姓名用另外4个人写的姓名
    data_dst_path = r'/ocr/sigver/data/name/train_data'
    users = []
    user_names = []
    with open("name.txt", "r") as f:
        for line in f.readlines():
            line = line.strip('\n')  # 去掉列表中每一个元素的换行符
            user, user_name = line.split(' ')
            users.append(user)
            user_names.append(user_name)
            print(user, ':', user_name)

    for i, user_name in enumerate(user_names):
        # 先生成本人的4个真实签名
        result_img_path = r'/ocr/sigver/data/name/train_data/full_org/original_' + str(i + 1)
        gen_user_sign_data(user_name, users[i], result_img_path, number_of_name=7)

        if i < 45:  # 小于50,则直接往后挨着4个用户的名字作为伪造签名
            k = 1
            for j in range(i + 1, i + 7):
                result_img_path = r'/ocr/sigver/data/name/train_data/full_forg/forgeries_' + str(i + 1)
                try:
                    gen_user_sign_data(user_name, users[j], result_img_path, k, number_of_name=1)
                except:
                    try:
                        gen_user_sign_data(user_name, users[random.randint(0, 45)], result_img_path, k,
                                           number_of_name=1)
                    except:
                        try:
                            gen_user_sign_data(user_name, users[random.randint(0, 45)], result_img_path, k,
                                               number_of_name=1)
                        except:
                            print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~1', user_name)
                            continue
                k += 1
        else:
            k = 1
            for j in range(i - 7, i - 1):
                result_img_path = r'/ocr/sigver/data/name/train_data/full_forg/forgeries_' + str(i + 1)
                try:
                    gen_user_sign_data(user_name, users[j], result_img_path, k, number_of_name=1)
                except:
                    try:
                        gen_user_sign_data(user_name, users[random.randint(0, 45)], result_img_path, k,
                                           number_of_name=1)
                    except:
                        print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~2', user_name)
                        continue
                k += 1
