import json
import csv
import os

JSON_INPUT_PATH= r"data\qa.json"
CSV_OUTPUT_FOLDER=r"data"

def json_to_csv(json_path, csv_folder):
    """
    Convert JSON knowledge graph data to CSV format.
    Args:
        json_path: Path to JSON file containing triples data
        csv_path: Path to save the CSV file
    """
    json_basename=os.path.basename(json_path)
    json_filename=os.path.splitext(json_basename)[0]
    csv_full_path=os.path.join(csv_folder,json_filename+".csv")

    try:
        with open(json_path,'r',encoding='utf-8-sig') as f:
            data=json.load(f)
        print(f"成功读取JSON文件")
    except FileNotFoundError:
        print(f"未找到JSON文件")

    try:
        with open(csv_full_path,"w",encoding="utf-8-sig",newline="") as f:
            writer=csv.writer(f)
            writer.writerow(['subject','predicate','object'])
            row_count=0
            for item in data:
                if all(key in item for key in ['subject','predicate','object']):
                    subject=item['subject'].strip()
                    predicate=item['predicate'].strip()
                    object=item['object'].strip()

                    if subject and predicate and object:
                        writer.writerow([subject,predicate,object])
                        row_count+=1
        print(f"成功生成csv文件，共写入{row_count}条有效三元组")
    except Exception as e:
        print(f"生成csv文件失败：{e}")

if __name__=="__main__":
    json_to_csv(JSON_INPUT_PATH,CSV_OUTPUT_FOLDER)
