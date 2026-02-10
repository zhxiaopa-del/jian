# -*- coding: utf-8 -*-
import fileinput
import sys

# 要替换的文本
old_line = '3. 调试：如果用户反馈"不能执行"，请主动使用 ls -la 查看文件是否存在，使用 chmod +x 赋予权限。'
new_lines = """3. Windows 系统注意事项：
   - 创建文件夹：使用 `mkdir 路径` 或 `New-Item -ItemType Directory -Path 路径`
   - 写入文件：使用 PowerShell 的 `Set-Content` 或 `Out-File`，例如：
     `Set-Content -Path "文件路径" -Value @'多行内容'@` 或
     `python -c "with open('文件路径', 'w', encoding='utf-8') as f: f.write('内容')"`
   - 不要使用 `echo` 命令写入多行文件，Windows 的 echo 不支持转义字符
4. 调试：如果用户反馈"不能执行"，请主动检查文件是否存在，Windows 使用 `Test-Path 路径`，Linux/Mac 使用 `ls -la`。"""

file_path = r'd:\1work\test\skills\agent_skills.py'
found = False

with fileinput.FileInput(file_path, inplace=True, encoding='utf-8') as f:
    for line in f:
        if old_line in line and not found:
            print(new_lines, end='')
            found = True
        else:
            print(line, end='')

if found:
    print("文件已成功更新")
else:
    print("未找到要替换的文本")
