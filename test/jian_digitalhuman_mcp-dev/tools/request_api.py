import httpx
import os
import json
import traceback
from httpx import Response
from .login import get_access_token, login
import logging
from typing import Union

logger = logging.getLogger(__name__)
base_url: str = os.getenv("JAMS_BASE_URL")


async def post_request(*, uri: str, data: dict) -> Union[dict, str]:
    """
    Send a post request to the given uri with the given data

    Args:
        uri: The uri to send the request to
        data: The data to send in the request

    Returns:
        The response from the request
    """

    url: str = base_url + uri
    access_token = await get_access_token()

    headers: dict = {
        "Content-Type": "application/json",
        "Authorization": f"{access_token}",
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:

            print(json.dumps(data, ensure_ascii=False))
            response: Response = await client.post(url, json=data, headers=headers)

            print("response:", response.json())

            try:
                ryCode = response.json().get("code")
            except:
                ryCode = 200

            # 401 Unauthorized
            if response.status_code == 401 or ryCode == 401:
                access_token = await login()

                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"{access_token}",
                }

                response = await client.post(url, json=data, headers=headers)

            response.raise_for_status()

            # 检查响应体是否为空
            if not response.text or response.text.strip() == "":
                logger.warning("Response body is empty")
                return {}

            try:
                result = response.json()
                print(json.dumps(result, ensure_ascii=False))
                return result
            except json.JSONDecodeError as e:
                logger.error(
                    f"Failed to parse JSON response: {e}, response text: {response.text[:200]}"
                )
                return {"error": "Invalid JSON response", "text": response.text}
    except Exception as e:
        error_type = type(e).__name__
        error_detail = str(e) if str(e) else "No error message"
        logger.error(f"Request failed: [{error_type}] {error_detail}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return f"HTTP request failed: [{error_type}] {error_detail}"


async def get_request(*, uri: str, params: dict) -> Union[dict, str]:
    """
    Send a get request to the given uri with the given params

    Args:
        uri: The uri to send the request to
        params: The params to send in the request

    Returns:
        The response from the request
    """

    url: str = base_url + uri
    access_token = await get_access_token()

    headers: dict = {
        "Content-Type": "application/json",
        "Authorization": f"{access_token}",
    }

    try:
        async with httpx.AsyncClient() as client:
            print(json.dumps(params, ensure_ascii=False))
            response: Response = await client.get(url, params=params, headers=headers)

            try:
                ryCode = response.json().get("code")
            except:
                ryCode = 200

            # 401 Unauthorized
            if response.status_code == 401 or ryCode == 401:
                access_token = await login()

                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"{access_token}",
                }

                response = await client.get(url, params=params, headers=headers)

            response.raise_for_status()

            # 检查响应体是否为空
            if not response.text or response.text.strip() == "":
                logger.warning("Response body is empty")
                return {}

            try:
                result = response.json()
                print(json.dumps(result, ensure_ascii=False))
                return result
            except json.JSONDecodeError as e:
                logger.error(
                    f"Failed to parse JSON response: {e}, response text: {response.text[:200]}"
                )
                return {"error": "Invalid JSON response", "text": response.text}
    except Exception as e:
        error_type = type(e).__name__
        error_detail = str(e) if str(e) else "No error message"
        logger.error(f"Request failed: [{error_type}] {error_detail}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return f"HTTP request failed: [{error_type}] {error_detail}"
