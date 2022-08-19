import httpx
from bs4 import BeautifulSoup
import os
import json
import random
from services.log import logger
from utils.image_utils import BuildImage
from utils.message_builder import image
#import hoshino
#from hoshino import R
#from hoshino.typing import MessageSegment

async def update_info():
    img_dict = await get_imgurl()
    for img_id in list(img_dict.keys()):
        await download_img(img_id, img_dict[img_id]['url'])
    await create_config(img_dict)

# 获取表情包的url字典
async def get_imgurl():
    url = 'https://wiki.biligame.com/umamusume/表情包'
    res = httpx.get(url, timeout=15)
    soup = BeautifulSoup(res.text, 'lxml')
    img_dict = {}
    all_gallery = soup.find('ul', {"class": "gallery mw-gallery-traditional"}).find_all('img')
    for gallery in all_gallery:
        img_id = gallery.get('alt').replace('.png', '')
        img_dict[img_id] = {}
        img_dict[img_id]['url'] = gallery.get('src')
    return img_dict

# 创建json配置文件
async def create_config(img_dict):
    current_dir_tmp = os.path.join(os.path.dirname(__file__), f'face_info.json')
    with open(current_dir_tmp, 'r', encoding = 'UTF-8') as f:
        mean_data = json.load(f)
    for img_id in list(img_dict.keys()):
        if img_id in list(mean_data.keys()):
            img_dict[img_id]['en_name'] = mean_data[img_id]['en_name']
            img_dict[img_id]['meanings'] = mean_data[img_id]['meanings']
        else:
            img_dict[img_id]['en_name'] = ''
            img_dict[img_id]['meanings'] = ''
    current_dir = os.path.join(os.path.dirname(__file__), f'img_config.json')
    with open(current_dir, 'w', encoding = 'UTF-8') as af:
        json.dump(img_dict, af, indent=4, ensure_ascii=False)

# 下载图片
async def download_img(id, url):
    img_path = os.path.join(os.path.dirname(__file__), 'uma_face/')
    if not os.path.exists(img_path):
        os.mkdir(img_path)
    current_dir = os.path.join(img_path, f'{id}.png')
    if not os.path.exists(current_dir):
        response = httpx.get(url, timeout=10)
        with open(current_dir, 'wb') as f:
            f.write(response.read())
        logger.info(f'未检测到马娘表情包 {id}.png ，现已下载成功')
    else:
        logger.info(f'检测到马娘表情包 {id}.png 已存在，将不会重新下载')

async def get_en_name(name_tmp):
    with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uma_info/config.json'), 'r', encoding = 'UTF-8') as f:
        f_data = json.load(f)
        f.close()
    name_list = list(f_data.keys())
    name_list.remove('current_chara')
    with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uma_info/replace_dict.json'), 'r', encoding = 'UTF-8') as af:
        replace_data = json.load(af)
        af.close()
    name_list = list(f_data.keys())
    name_list.remove('current_chara')
    for uma_name in name_list:
        other_name_list = list(replace_data[uma_name])
        cn_name = f_data[uma_name]['cn_name']
        jp_name = f_data[uma_name]['jp_name']
        if str(name_tmp) == str(cn_name) or str(name_tmp) in other_name_list or str(name_tmp) == str(jp_name):
            return uma_name
    return ''

# 按马娘名字的表情包
async def get_face_uma(uma_name_tmp):
    uma_name = await get_en_name(uma_name_tmp)
    if not uma_name:
        return ''
    path = os.path.join(os.path.dirname(__file__), 'uma_face/')
    current_dir = os.path.join(os.path.dirname(__file__), f'img_config.json')
    with open(current_dir, 'r', encoding = 'UTF-8') as f:
        img_data = json.load(f)
    flag = 0
    for id in list(img_data.keys()):
        if img_data[id]['en_name'] == uma_name:
            img_path = os.path.join(path, f'{id}.png')
            # 当文件丢失就重新下载
            if not os.path.exists(img_path):
                url = img_data[id]['url']
                await download_img(id, url)
            id = str(int(id) - 100000)
            sv_help = f'{os.path.abspath(img_path)}' 
            async def n() -> str:
                        sv = BuildImage(0,0,background=sv_help)
                        return sv.pic2bs4() 
            msg = f'id: {id}'
            msg += image(b64=await n())
            flag = 1
            return msg
    if not flag:
        return ''

# 按编号的表情包
async def get_face_id(id):
    path = os.path.join(os.path.dirname(__file__), 'uma_face/')
    img_path = os.path.join(path, f'{id}.png')
    if not os.path.exists(img_path):
        lenth = len(os.listdir(path))
        return f'此编号的表情包不存在哦，目前有的编号范围为 1 到 {lenth}'
    sv_help = f'{os.path.abspath(img_path)}' 
    async def n() -> str:
                        sv = BuildImage(0,0,background=sv_help)
                        return sv.pic2bs4() 
    msg = image(b64=await n())
    return msg

# 随机表情包
async def get_face_random():
    path = os.path.join(os.path.dirname(__file__), 'uma_face/')
    if not os.listdir(path):
        await update_info()
        return '没有表情包文件呢，正在自动下载……'
    file_name = random.choice(os.listdir(path))
    img_path = os.path.join(path, file_name)
    id = file_name.replace('.png', '')
    id = str(int(id) - 100000)
    sv_help = f'{os.path.abspath(img_path)}' 
    async def n() -> str:
                        sv = BuildImage(0,0,background=sv_help)
                        return sv.pic2bs4() 
    msg = image(b64=await n())
    return msg

# 按编号查含义
async def get_mean_id(id):
    current_dir = os.path.join(os.path.dirname(__file__), f'img_config.json')
    with open(current_dir, 'r', encoding = 'UTF-8') as f:
        img_data = json.load(f)
    if id not in list(img_data.keys()):
        lenth = len(list(img_data.keys()))
        return f'此编号的表情包不存在哦，目前有的编号范围为 1 到 {lenth}'
    meanings = img_data[id]['meanings']
    id = str(int(id) - 100000)
    msg = f'该id: {id} 表情包的含义是：\n{meanings}'
    return msg

# 按马娘名字查含义
async def get_mean_uma(uma_name_tmp):
    uma_name = await get_en_name(uma_name_tmp)
    if not uma_name:
        return ''
    current_dir = os.path.join(os.path.dirname(__file__), f'img_config.json')
    with open(current_dir, 'r', encoding = 'UTF-8') as f:
        img_data = json.load(f)
    flag = 0
    for id in list(img_data.keys()):
        en_name = img_data[id]['en_name']
        if en_name == uma_name:
            flag = 1
            meanings = img_data[id]['meanings']
            id = str(int(id) - 100000)
            msg = f'该id: {id} 表情包的含义是：\n{meanings}'
            return msg
    if not flag:
        return ''