"""LLM interaction utilities for knowledge graph generation."""
import requests
import json
import re
from openai import OpenAI

def call_llm(
    model,
    user_prompt,
    api_key,
    system_prompt=None,
    max_tokens=1000,
    temperature=0.2,
    base_url=None
) -> str:
    client=OpenAI(api_key=api_key, base_url=base_url, timeout=60.0)
    messages = []
    if system_prompt:
        messages.append({'role': 'system', 'content': system_prompt})
    messages.append({'role': 'user', 'content': user_prompt})

    max_retry=3
    for attempt in range(max_retry + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=False
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error calling LLM: {e}")

# def call_llm(
#     model,
#     user_prompt,
#     api_key,
#     system_prompt=None,
#     max_tokens=1000,
#     temperature=0.2,
#     base_url=None
# ) -> str:
#     """
#     适配阿里云通义千问
#     """
#     headers = {
#         'Content-Type': 'application/json',
#         'Authorization': f"Bearer {api_key}"  # 阿里云兼容Bearer格式
#     }
#
#     messages = []
#     if system_prompt:
#         messages.append({'role': 'system', 'content': system_prompt})
#     messages.append({'role': 'user', 'content': user_prompt})
#
#     payload = {
#         'model': model,
#         'messages': messages,
#         'max_tokens': max_tokens,
#         'temperature': temperature,
#         'stream': False  # 关闭流式返回
#     }
#
#     api_url = f"{base_url.rstrip('/')}/chat/completions"
#
#     try:
#         response = requests.post(
#             api_url,
#             headers=headers,
#             json=payload,
#             timeout=60
#         )
#         response.raise_for_status()
#
#         result = response.json()
#         return result['choices'][0]['message']['content']
#
#     except requests.exceptions.RequestException as e:
#         error_detail = response.text if 'response' in locals() else '无响应内容'
#         raise Exception(f"阿里云API调用失败: {str(e)} | 错误详情: {error_detail}")

def extract_json_from_text(text):
    code_block_pattern = r'```(?:json)?\s*([\s\S]*?)```'
    code_match = re.search(code_block_pattern, text)
    if code_match:
        text = code_match.group(1).strip()
        print("Found JSON in code block, extracting content...")

    try:
        # Try direct parsing in case the response is already clean JSON
        return json.loads(text)
    except json.JSONDecodeError:
        # Look for opening and closing brackets of a JSON array
        start_idx = text.find('[')
        if start_idx == -1:
            print("No JSON array start found in text")
            return None

        # Simple bracket counting to find matching closing bracket
        bracket_count = 0
        complete_json = False
        for i in range(start_idx, len(text)):
            if text[i] == '[':
                bracket_count += 1
            elif text[i] == ']':
                bracket_count -= 1
                if bracket_count == 0:
                    # Found the matching closing bracket
                    json_str = text[start_idx:i+1]
                    complete_json = True
                    break

        # Handle complete JSON array
        if complete_json:
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                print("Found JSON-like structure but couldn't parse it.")
                print("Trying to fix common formatting issues...")

                # Try to fix missing quotes around keys
                fixed_json = re.sub(r'(\s*)(\w+)(\s*):(\s*)', r'\1"\2"\3:\4', json_str)
                # Fix trailing commas
                fixed_json = re.sub(r',(\s*[\]}])', r'\1', fixed_json)

                try:
                    return json.loads(fixed_json)
                except:
                    print("Could not fix JSON format issues")
        else:
            # Handle incomplete JSON - try to complete it
            print("Found incomplete JSON array, attempting to complete it...")

            # Get all complete objects from the array
            objects = []
            obj_start = -1
            obj_end = -1
            brace_count = 0

            # First find all complete objects
            for i in range(start_idx + 1, len(text)):
                if text[i] == '{':
                    if brace_count == 0:
                        obj_start = i
                    brace_count += 1
                elif text[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        obj_end = i
                        objects.append(text[obj_start:obj_end+1])

            if objects:
                # Reconstruct a valid JSON array with complete objects
                reconstructed_json = "[\n" + ",\n".join(objects) + "\n]"
                try:
                    return json.loads(reconstructed_json)
                except json.JSONDecodeError:
                    print("Couldn't parse reconstructed JSON array.")
                    print("Trying to fix common formatting issues...")

                    # Try to fix missing quotes around keys
                    fixed_json = re.sub(r'(\s*)(\w+)(\s*):(\s*)', r'\1"\2"\3:\4', reconstructed_json)
                    # Fix trailing commas
                    fixed_json = re.sub(r',(\s*[\]}])', r'\1', fixed_json)

                    try:
                        return json.loads(fixed_json)
                    except:
                        print("Could not fix JSON format issues in reconstructed array")

        print("No complete JSON array could be extracted")
        return None