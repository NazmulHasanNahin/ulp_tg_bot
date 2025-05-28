import os
import zipfile

def process_zip_file(zip_path, keyword):
    extract_dir = "temp_extracted"
    os.makedirs(extract_dir, exist_ok=True)

    matched_lines = []
    is_zip = zip_path.endswith(".zip")
    is_rar = zip_path.endswith(".rar")

    try:
        if is_zip:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
        
        else:
            raise ValueError("Unsupported file type.")

        for root, dirs, files in os.walk(extract_dir):
            for file in files:
                if file.endswith(".txt"):
                    with open(os.path.join(root, file), 'r', encoding='utf-8', errors='ignore') as f:
                        for line in f:
                            if keyword in line:
                                matched_lines.append(line.strip())

        result_file = "result.txt"
        with open(result_file, "w", encoding="utf-8") as f:
            for line in matched_lines:
                f.write(line + "\n")

        return result_file, len(matched_lines)

    finally:
        if os.path.exists(extract_dir):
            for root, dirs, files in os.walk(extract_dir, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(extract_dir)
            
            
            
            
def process_txt_file(file_path, keyword):
    output_file = "result_from_txt.txt"
    count = 0
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f, open(output_file, "w", encoding="utf-8") as out:
        for line in f:
            if keyword in line:
                out.write(line)
                count += 1
    return output_file, count
