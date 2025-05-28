from parser import process_zip_file

zip_path = "test.zip"  # অথবা test.rar
keyword = "canva.com"

result_file, count = process_zip_file(zip_path, keyword)

print(f"Matched lines: {count}")
print(f"Result saved in: {result_file}")
