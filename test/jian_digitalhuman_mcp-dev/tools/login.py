#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
吉安管理系统登录获取access token
"""

import os
import json
import base64
import logging
from typing import Optional

import httpx
from httpx import Response
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)

__access_token: Optional[str] = None


def _encrypt_password_with_rsa(password: str, public_key_str: str) -> str:
    """使用RSA公钥加密密码"""
    try:
        # 解码base64公钥
        public_key_bytes = base64.b64decode(public_key_str)

        # 加载公钥
        public_key = serialization.load_der_public_key(
            public_key_bytes, backend=default_backend()
        )

        # 加密密码
        encrypted_password = public_key.encrypt(
            password.encode("utf-8"), padding.PKCS1v15()
        )

        # 返回base64编码的加密结果
        return base64.b64encode(encrypted_password).decode("utf-8")

    except Exception as e:
        logger.error(f"Failed to encrypt password with RSA: {e}")
        raise


async def login() -> Optional[str]:
    login_url: str = os.getenv("JAMS_BASE_URL") + "/login"
    public_key: str = os.getenv("JAMS_PUBLIC_KEY")
    username: str = os.getenv("JAMS_USERNAME")
    password: str = os.getenv("JAMS_PASSWORD")
    # encrypted_password: str = _encrypt_password_with_rsa(password, public_key)
    login_data: dict = {"username": username, "password": password}
    headers: dict = {"Content-Type": "application/json"}

    try:
        async with httpx.AsyncClient() as client:
            response: Response = await client.post(
                login_url, json=login_data, headers=headers, timeout=30
            )

            response.raise_for_status()
            result: dict = response.json()

            if result is None:
                logger.warning(f"Failed to login to the jian-management ({login_url})")
                return None

            code: int = result.get("code")

            if code != 200:
                error_msg: str = result.get("msg", "Unknown error")
                logger.error(f"Login failed: {error_msg}")
                return None

            # 获取access_token
            global __access_token
            __access_token = result.get("token")
            return __access_token
    except httpx.RequestError as e:
        logger.error(f"HTTP request failed: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        return None
    except Exception as e:
        logger.error(f"An error occurred during login: {e}")
        return None


async def get_access_token() -> Optional[str]:
    return __access_token if __access_token else await login()
