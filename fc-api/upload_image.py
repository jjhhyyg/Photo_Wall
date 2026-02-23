# -*- coding: utf-8 -*-
"""
阿里云函数计算 - 上传图片 API
功能：
1. 接收前端上传的图片
2. 提取 EXIF 信息
3. 上传到 OSS 并附加元数据
"""

import json
import os
import base64
from datetime import datetime
from urllib.parse import quote
import oss2
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from io import BytesIO


def handler(event, context):
    """
    事件触发器入口函数 (Compatible with API Gateway / Event Bridge)

    请求方式: POST
    请求体 (JSON):
        {
            "filename": "image.jpg",
            "data": "base64编码的图片数据",
            "metadata": {  // 可选
                "note": "备注信息"
            }
        }

    返回:
        JSON: {
            "success": true,
            "filename": "xxx.jpg",
            "url": "图片URL"
        }
    """
    # CORS 头
    headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type'
    }

    try:
        # 解析 event
        try:
            evt = json.loads(event)
        except:
            evt = {}

        # 处理 OPTIONS 请求（CORS 预检）
        if evt.get('httpMethod') == 'OPTIONS':
            return {
                "isBase64Encoded": False,
                "statusCode": 200,
                "headers": headers,
                "body": ""
            }

        # 读取请求体
        body_str = evt.get('body')
        if evt.get('isBase64Encoded'):
            # 如果是 base64 编码的 body，先解码
            # 注意：这里的 data 是请求体的 base64，不是图片内容的 base64
            body_bytes = base64.b64decode(body_str)
            body_str = body_bytes.decode('utf-8')
        
        request_data = json.loads(body_str) if body_str else {}

        # 解析参数
        filename = request_data.get('filename')
        image_data_base64 = request_data.get('data')
        user_metadata = request_data.get('metadata', {})

        if not filename or not image_data_base64:
             return {
                "isBase64Encoded": False,
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({"success": False, "error": "缺少必要参数: filename 或 data"}, ensure_ascii=False)
            }

        # Base64 解码图片数据 (这是图片内容的 base64)
        try:
            image_data = base64.b64decode(image_data_base64.split(',')[-1])
        except Exception as e:
             return {
                "isBase64Encoded": False,
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({"success": False, "error": f"Base64解码失败: {str(e)}"}, ensure_ascii=False)
            }

        # 提取 EXIF 元数据
        metadata = extract_exif_metadata(image_data)

        # 合并用户提供的元数据
        if user_metadata.get('note'):
            metadata['note'] = user_metadata['note']

        # 从环境变量读取配置
        access_key_id = os.environ.get('OSS_ACCESS_KEY_ID')
        access_key_secret = os.environ.get('OSS_ACCESS_KEY_SECRET')
        bucket_name = os.environ.get('OSS_BUCKET_NAME')
        endpoint = os.environ.get('OSS_ENDPOINT')
        
        # 确保 endpoint 包含协议头
        if endpoint and not endpoint.startswith('http'):
            endpoint = 'https://' + endpoint

        image_prefix = os.environ.get('OSS_IMAGE_PREFIX', 'images/')

        # 初始化 OSS 客户端
        auth = oss2.Auth(access_key_id, access_key_secret)
        bucket = oss2.Bucket(auth, endpoint, bucket_name)

        # 生成 OSS 路径
        oss_key = f"{image_prefix}{filename}"

        # 准备元数据 headers
        oss_headers = {
            'x-oss-meta-date': encode_oss_meta_value(metadata.get('date', '')),
            'x-oss-meta-time': encode_oss_meta_value(metadata.get('time', '')),
            'x-oss-meta-location': encode_oss_meta_value(metadata.get('location', '')),
            'x-oss-meta-camera': encode_oss_meta_value(metadata.get('camera', '')),
            'x-oss-meta-note': encode_oss_meta_value(metadata.get('note', '')),
            'x-oss-meta-upload-time': encode_oss_meta_value(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        }

        # 上传到 OSS
        bucket.put_object(oss_key, image_data, headers=oss_headers)
        
        # 计算返回的 URL (处理内网 Endpoint 替换)
        public_endpoint = endpoint.replace('-internal', '')
        url = f"{public_endpoint}/{oss_key}"
        # 确保 https
        if public_endpoint.startswith('https') and url.startswith('http:'):
             url = url.replace('http:', 'https:', 1)
        elif not url.startswith('http'):
             url = 'https://' + url # 兜底

        result = {
            'success': True,
            'filename': filename,
            'url': url
        }
        
        return {
            "isBase64Encoded": False,
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps(result, ensure_ascii=False)
        }

    except Exception as e:
        # 错误处理
        error_result = {
            'success': False,
            'error': str(e)
        }
        return {
            "isBase64Encoded": False,
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps(error_result, ensure_ascii=False)
        }


def extract_exif_metadata(image_data):
    """提取图片 EXIF 元数据"""
    metadata = {
        'date': '',
        'time': '',
        'location': '',
        'camera': '',
        'note': ''
    }

    try:
        image = Image.open(BytesIO(image_data))
        exif_data = image._getexif()

        if not exif_data:
            return metadata

        # 提取拍摄日期和时间
        datetime_original = exif_data.get(36867) or exif_data.get(306)
        if datetime_original:
            try:
                dt = datetime.strptime(datetime_original, '%Y:%m:%d %H:%M:%S')
                metadata['date'] = dt.strftime('%Y-%m-%d')
                metadata['time'] = dt.strftime('%H:%M:%S')
            except:
                pass

        # 提取相机型号
        camera_make = exif_data.get(271)
        camera_model = exif_data.get(272)
        if camera_make and camera_model:
            metadata['camera'] = f"{camera_make} {camera_model}"
        elif camera_model:
            metadata['camera'] = camera_model

        # 提取 GPS 位置
        gps_info = exif_data.get(34853)
        if gps_info:
            location = parse_gps(gps_info)
            if location:
                metadata['location'] = location

    except:
        pass

    return metadata


def parse_gps(gps_info):
    """解析 GPS 信息"""
    try:
        gps_data = {}
        for tag, value in gps_info.items():
            decoded = GPSTAGS.get(tag, tag)
            gps_data[decoded] = value

        lat = gps_data.get('GPSLatitude')
        lat_ref = gps_data.get('GPSLatitudeRef')
        lon = gps_data.get('GPSLongitude')
        lon_ref = gps_data.get('GPSLongitudeRef')

        if lat and lon:
            lat_decimal = convert_to_degrees(lat)
            if lat_ref == 'S':
                lat_decimal = -lat_decimal

            lon_decimal = convert_to_degrees(lon)
            if lon_ref == 'W':
                lon_decimal = -lon_decimal

            return f"{lat_decimal:.6f},{lon_decimal:.6f}"
    except:
        pass

    return None


def convert_to_degrees(value):
    """将 GPS 坐标转换为十进制度数"""
    d = float(value[0])
    m = float(value[1])
    s = float(value[2])
    return d + (m / 60.0) + (s / 3600.0)


def encode_oss_meta_value(value):
    """对 OSS 自定义元数据做安全编码，避免中文导致签名不一致"""
    if value is None:
        return ''

    text = str(value).replace('\r', ' ').replace('\n', ' ').strip()
    # 显式使用 UTF-8 编码
    return quote(text, safe='-_.~', encoding='utf-8')
