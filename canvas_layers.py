from pydantic import BaseModel
from enum import IntEnum, Enum
from typing import List, Dict, Optional
from PIL import Image, ImageFont, ImageDraw
import base64
import qrcode
import requests
from io import BytesIO


class ResourceType(IntEnum):
    EMPTY = 0
    TEXT = 1
    IMAGE = 3


class LocalImage(IntEnum):
    BILIBILI_ICON = 1
    CANVAS_FOOTER = 2
    DYNAMIC_QR = 3
    INTELLIGENT = 4
    ENTERPRISE = 5


class ResourceImageSrcType(IntEnum):
    LOCAL = 1
    REMOTE = 2


class FontFamily(Enum):
    NotoSansCJK = "NotoSansCJKsc-Regular.otf"
    FansNum = "FansNum.ttf"


class CanvasSize(BaseModel):
    height: int
    width: int


class Pos(BaseModel):
    axis_x: int
    axis_y: int
    coordinate_pos: int


class RenderSpec(BaseModel):
    opacity: float


class Size(BaseModel):
    height: int
    width: int


class GeneralSpec(BaseModel):
    pos_spec: Pos
    render_spec: RenderSpec
    size_spec: Size


class LayerConfig(BaseModel):
    is_critical: bool
    is_circular: bool = False
    layer_mode: Optional[str] = "RGBA"
    background_color: Optional[str] = "#ffffff00"
    font_family: FontFamily = FontFamily.NotoSansCJK
    font_color: Optional[str] = "#000000"
    font_size: Optional[int] = 25


class ResourceText(BaseModel):
    orig_text: str


class RemoteImage(BaseModel):
    url: str


class ResourceImageSrc(BaseModel):
    local: Optional[LocalImage]
    remote: Optional[str]
    src_type: ResourceImageSrcType


class ResourceImage(BaseModel):
    image_src: ResourceImageSrc


class Resource(BaseModel):
    text: Optional[ResourceText]
    res_image: Optional[ResourceImage]
    res_type: ResourceType


class Layer(BaseModel):
    general_spec: GeneralSpec
    layer_config: LayerConfig
    resource: Resource


class Element(BaseModel):
    container_size: CanvasSize
    layers: List[Layer]


class Canvas(BaseModel):
    version: str
    canvas_top: Element
    canvas_footer: Element
    canvas_avatar: Element


class StyleAnalysis:
    def __init__(self) -> None:
        pass


def img_author(ima):
    size = ima.size

    # 因为是要圆形，所以需要正方形的图片
    r2 = min(size[0], size[1])
    if size[0] != size[1]:
        ima = ima.resize((r2, r2), Image.ANTIALIAS)

    # 最后生成圆的半径
    r3 = int(r2 / 2)

    imb = Image.new('RGBA', (r3 * 2, r3 * 2), "#ffffff00")
    pima = ima.load()  # 像素的访问对象
    pimb = imb.load()
    r = float(r2 / 2)  # 圆心横坐标

    for i in range(r2):
        for j in range(r2):
            lx = abs(i - r)  # 到圆心距离的横坐标
            ly = abs(j - r)  # 到圆心距离的纵坐标
            l = (pow(lx, 2) + pow(ly, 2)) ** 0.5  # 三角函数 半径

            if l <= r3:
                pimb[i - (r - r3), j - (r - r3)] = pima[i, j]

    return imb


def makeQRcode(data):
    """制作二维码"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=3,
        border=4
    )
    qr.add_data(data)
    qr.make(fit=True)
    return qr.make_image(fill_color="#000000", back_color="#ffffff")


if __name__ == "__main__":
    iconelement = {
        LocalImage.BILIBILI_ICON: "./newelement/logo.png",
        LocalImage.CANVAS_FOOTER: "./newelement/canvas_footer.png",
        LocalImage.INTELLIGENT: "./newelement/intelligent.png",
        LocalImage.ENTERPRISE: "./newelement/enterprise.png"
    }

    import json
    with open("./style.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    data = Canvas(**data)
    style_name = "canvas_avatar"
    # style_name = "canvas_top"
    # try:
    style: Element = getattr(data, style_name)
    canvas = Image.new("RGBA", (style.container_size.width,
                                style.container_size.height), "#FFFFFF00")
    canvas_draw = ImageDraw.Draw(canvas)
    for layer in style.layers:
        # 遍历一个渲染对象当中的层，放置元素的左上角坐标，大小
        layer_config = layer.layer_config
        if not layer_config.is_critical:
            continue
        x, y = (layer.general_spec.pos_spec.axis_x,
                layer.general_spec.pos_spec.axis_y)
        width, height = (layer.general_spec.size_spec.width,
                         layer.general_spec.size_spec.height)
        resource_type = layer.resource.res_type
        layer_config = layer.layer_config
        if resource_type == ResourceType.TEXT:
            # 如果渲染对象是文字
            text_height = layer_config.font_size
            text = layer.resource.text.orig_text
            Font = ImageFont.truetype(
                f"./bilibili_dynamic/typeface/{layer_config.font_family.value}", text_height)
            canvas_draw.text((x, y), text=text, font=Font,
                             fill=layer_config.font_color)

        elif resource_type == ResourceType.IMAGE:
            image_info = layer.resource.res_image
            if image_info.image_src.src_type == ResourceImageSrcType.LOCAL:
                if image_info.image_src.local == LocalImage.DYNAMIC_QR:
                    img = makeQRcode(
                        "https://t.bilibili.com/12312312312313248679")
                else:
                    print(image_info.image_src.local)
                    img = Image.open(iconelement[image_info.image_src.local])

            elif image_info.image_src.src_type == ResourceImageSrcType.REMOTE:
                url = image_info.image_src.remote
                res = requests.get(url)
                img = Image.open(BytesIO(res.content))

            img = img.resize((width, height))
            img = img.convert("RGBA")
            if layer_config.is_circular:
                img = img_author(img)

            canvas.paste(img, (x, y), mask=img)

        elif resource_type == ResourceType.EMPTY:
            img = Image.new(layer_config.layer_mode,
                            (width, height), layer_config.background_color)
            img = img.convert("RGBA")
            canvas.paste(img, (x, y), mask=img)

    canvas.save("./test.png")
    # except AttributeError:
    #     print(f"渲染样式表中未定义{style_name}样式")
