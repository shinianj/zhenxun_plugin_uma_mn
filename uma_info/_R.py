
import os
from urllib.parse import urljoin
from urllib.request import pathname2url
import base64

from io import BytesIO

from nonebot.adapters.onebot.v11  import MessageSegment
from PIL import Image
from services.log import logger

RES_PROTOCOL = 'file'

RES_URL = 'http://127.0.0.1:8080/res/'

def pic2b64(pic: Image) -> str:
    buf = BytesIO()
    pic.save(buf, format='PNG')
    base64_str = base64.b64encode(buf.getvalue()).decode()
    return 'base64://' + base64_str

class ResObj:
    def __init__(self, res_path):
        res_dir = os.path.expanduser('~/res')
        fullpath = os.path.abspath(os.path.join(res_dir, res_path))
        if not fullpath.startswith(os.path.abspath(res_dir)):
            raise ValueError('Cannot access outside RESOUCE_DIR')
        self.__path = os.path.normpath(res_path)

    @property
    def url(self):
        """资源文件的url，供Onebot（或其他远程服务）使用"""
        return urljoin(RES_URL, pathname2url(self.__path))

    @property
    def path(self):
        """资源文件的路径，供内部使用"""
        return os.path.join('~/res', self.__path)

    @property
    def exist(self):
        return os.path.exists(self.path)


class ResImg(ResObj):
    @property
    def cqcode(self) -> MessageSegment:
        if RES_PROTOCOL == 'http':
            return MessageSegment.image(self.url)
        elif RES_PROTOCOL == 'file':
            return MessageSegment.image(f'file:///{os.path.abspath(self.path)}')
        else:
            try:
                return MessageSegment.image(pic2b64(self.open()))
            except Exception as e:
                logger.exception(e)
                return MessageSegment.text('[图片出错]')

    def open(self) -> Image:
        try:
            return Image.open(self.path)
        except FileNotFoundError:
            logger.error(f'缺少图片资源：{self.path}')
            raise
def get(path, *paths):
    return ResObj(os.path.join(path, *paths))

def img(path, *paths):
    return ResImg(os.path.join('img', path, *paths))