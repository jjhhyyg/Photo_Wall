# -*- coding: utf-8 -*-
"""
阿里云函数计算 - 生成 OSS 预签名上传 URL
功能：
1. 接收文件名，生成有时效性的 OSS 预签名 PUT URL
2. 前端使用该 URL 直接将文件上传至 OSS，不经过函数计算
"""

import json
import os
import oss2


def handler(event, context):
    """
    请求方式: POST
    请求体 (JSON):
        {
            "filename": "photo.jpg"
        }

    返回:
        JSON: {
            "success": true,
            "upload_url": "https://...",
            "object_key": "images/photo.jpg"
        }
    """
    headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type'
    }

    try:
        try:
            evt = json.loads(event)
        except Exception:
            evt = {}

        if evt.get('httpMethod') == 'OPTIONS':
            return {
                "isBase64Encoded": False,
                "statusCode": 200,
                "headers": headers,
                "body": ""
            }

        body_str = evt.get('body', '{}')
        if evt.get('isBase64Encoded'):
            import base64
            body_str = base64.b64decode(body_str).decode('utf-8')

        request_data = json.loads(body_str) if body_str else {}
        filename = request_data.get('filename')

        if not filename:
            return {
                "isBase64Encoded": False,
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({"success": False, "error": "缺少必要参数: filename"}, ensure_ascii=False)
            }

        access_key_id = os.environ.get('OSS_ACCESS_KEY_ID')
        access_key_secret = os.environ.get('OSS_ACCESS_KEY_SECRET')
        bucket_name = os.environ.get('OSS_BUCKET_NAME')
        endpoint = os.environ.get('OSS_ENDPOINT')
        image_prefix = os.environ.get('OSS_IMAGE_PREFIX', 'images/')

        if endpoint and not endpoint.startswith('http'):
            endpoint = 'https://' + endpoint

        # 预签名 URL 必须使用公网 endpoint（去掉 -internal 后缀）
        public_endpoint = endpoint.replace('-internal', '')

        auth = oss2.Auth(access_key_id, access_key_secret)
        bucket = oss2.Bucket(auth, public_endpoint, bucket_name)

        object_key = f"{image_prefix}{filename}"
        expires = 3600  # 预签名 URL 有效期 1 小时

        # 生成预签名 PUT URL
        # slash_safe=True：保留 key 中的 '/' 不编码为 '%2F'
        # 若编码为 %2F，OSS 正规化路径时会导致签名不匹配（403）
        upload_url = bucket.sign_url('PUT', object_key, expires, slash_safe=True)

        return {
            "isBase64Encoded": False,
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps({
                "success": True,
                "upload_url": upload_url,
                "object_key": object_key
            }, ensure_ascii=False)
        }

    except Exception as e:
        return {
            "isBase64Encoded": False,
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)
        }
