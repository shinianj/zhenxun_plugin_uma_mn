from bs4 import BeautifulSoup
import os
import json
import re
from datetime import datetime
import shutil
import asyncio
from functools import partial
from typing import Optional, Any

import requests
from requests import *

#from hoshino import aiorequests

url = 'https://wiki.biligame.com/umamusume/技能速查表'
current_dir = os.path.join(os.path.dirname(__file__), f'skills_config.json')

async def run_sync_func(func, *args, **kwargs) -> Any:
    return await asyncio.get_event_loop().run_in_executor(
        None, partial(func, *args, **kwargs))


class AsyncResponse:
    def __init__(self, response: requests.Response):
        self.raw_response = response

    @property
    def ok(self) -> bool:
        return self.raw_response.ok
    
    @property
    def status_code(self) -> int:
        return self.raw_response.status_code
    
    @property
    def headers(self):
        return self.raw_response.headers
    
    @property
    def url(self):
        return self.raw_response.url
    
    @property
    def encoding(self):
        return self.raw_response.encoding
    
    @property
    def cookies(self):
        return self.raw_response.cookies

    def __repr__(self):
        return '<AsyncResponse [%s]>' % self.raw_response.status_code

    def __bool__(self):
        return self.ok

    @property
    async def content(self) -> Optional[bytes]:
        return await run_sync_func(lambda: self.raw_response.content)

    @property
    async def text(self) -> str:
        return await run_sync_func(lambda: self.raw_response.text)

    async def json(self, **kwargs) -> Any:
        return await run_sync_func(self.raw_response.json, **kwargs)
    
    def raise_for_status(self):
        self.raw_response.raise_for_status()

async def request(method, url, **kwargs) -> AsyncResponse:
    return AsyncResponse(await run_sync_func(requests.request,
                                             method=method, url=url, **kwargs))

async def get(url, params=None, **kwargs) -> AsyncResponse:
    return AsyncResponse(
        await run_sync_func(requests.get, url=url, params=params, **kwargs))

async def options(url, **kwargs) -> AsyncResponse:
    return AsyncResponse(
        await run_sync_func(requests.options, url=url, **kwargs))


async def head(url, **kwargs) -> AsyncResponse:
    return AsyncResponse(await run_sync_func(requests.head, url=url, **kwargs))


async def post(url, data=None, json=None, **kwargs) -> AsyncResponse:
    return AsyncResponse(await run_sync_func(requests.post, url=url,
                                             data=data, json=json, **kwargs))


async def put(url, data=None, **kwargs) -> AsyncResponse:
    return AsyncResponse(
        await run_sync_func(requests.put, url=url, data=data, **kwargs))


async def patch(url, data=None, **kwargs) -> AsyncResponse:
    return AsyncResponse(
        await run_sync_func(requests.patch, url=url, data=data, **kwargs))


async def delete(url, **kwargs) -> AsyncResponse:
    return AsyncResponse(
        await run_sync_func(requests.delete, url=url, **kwargs))



# 获取最新的更新时间
async def get_update_time():
    update_url = 'https://wiki.biligame.com/umamusume/index.php?title=技能速查表&action=history'
    rep = await get(update_url, timeout=10)
    soup = BeautifulSoup(await rep.text, 'lxml')
    last_time_tmp = soup.find('a', {'class': 'mw-changeslist-date'}).text.replace(' ', '')
    group = re.search(r'^([0-9]{4})年([0-9]{1,2})月([0-9]{1,2})日\S*([0-9]{2}):([0-9]{2})$', last_time_tmp)
    last_time = datetime(int(group.group(1)), int(group.group(2)), int(group.group(3)), int(group.group(4)), int(group.group(5)))
    return last_time

# 更新数据
async def update_info():
    rep = await get(url, timeout=10)
    soup = BeautifulSoup(await rep.text, 'lxml')
    with open(current_dir, 'r', encoding='UTF-8') as f:
        f_data = json.load(f)
    # 获取最新版的更新时间
    last_time = await get_update_time()
    f_data['last_time'] = str(last_time)
    f_data['cn_name_dict'] = {}
    f_data['tw_name_dict'] = {}
    # 获取所有技能
    f_data['skills'] = {}
    res_tag = soup.find('table', {'class': 'CardSelect wikitable sortable'})
    # 删除影响查找的多余标签
    res_tag.find('tr', {'id': 'CardSelectTabHeader'}).decompose()
    # 这样就全部都是有效的标签
    tr_list = res_tag.find_all('tr', {'class': 'divsort'})
    for each_tr in tr_list:
        rarity = each_tr.get('data-param1')
        color = each_tr.get('data-param3')
        each_tr_list = []
        for each_td in each_tr.find_all('td'):
            each_td = each_td.text.replace('\n', '')
            each_tr_list.append(each_td)
        skill_name_jp = each_tr_list[1].replace(' ', '_')
        skill_name_cn = each_tr_list[2].replace(' ', '_')
        skill_name_tw = each_tr_list[3].replace(' ', '_')
        # 额外处理一下继承技能
        if rarity == '普通·继承':
            skill_name_jp = '继承技/' + skill_name_jp
            skill_name_cn = '继承技/' + skill_name_cn
            skill_name_tw = '继承技/' + skill_name_tw
        # 对异常的结果修改
        skill_type = '条件1: 速度条件2: 速度、加速度' if each_tr_list[12] == '加速度条件2: 速度、条件1: 速度' else each_tr_list[12]
        # 注：嘉年华活动技能就不做额外处理了，仅保留最新的
        each_tr_dict = {
            '中文名': skill_name_cn,
            '稀有度': rarity,
            '颜色': color,
            '繁中译名': skill_name_tw,
            '条件限制': each_tr_list[4],
            '技能描述': each_tr_list[5],
            '技能数值': each_tr_list[6],
            '持续时间': each_tr_list[7],
            '评价分': each_tr_list[8],
            '需要PT': each_tr_list[9],
            'PT评价比': each_tr_list[10],
            '触发条件': each_tr_list[11],
            '技能类型': skill_type
        }
        f_data['cn_name_dict'][skill_name_cn] = skill_name_jp
        f_data['tw_name_dict'][skill_name_tw] = skill_name_jp
        f_data['skills'][skill_name_jp] = each_tr_dict
    # 都做完了再写入
    with open(current_dir, 'w', encoding='UTF-8') as f:
        json.dump(f_data, f, indent=4, ensure_ascii=False)

# 判断是否有更新
async def judge_update():
    last_time = await get_update_time()
    with open(current_dir, 'r', encoding='UTF-8') as f:
        f_data = json.load(f)
    set_time = datetime.strptime(f_data['last_time'], "%Y-%m-%d %H:%M:%S")
    if last_time > set_time:
        return True
    else:
        return False

# 若有更新就删除已经生成过的所有图片
async def del_img(root_path):
    path = os.path.join(root_path, 'uma_skills/')
    if os.path.exists(path):
        shutil.rmtree(path)
        os.mkdir(path)
    else:
        os.mkdir(path)