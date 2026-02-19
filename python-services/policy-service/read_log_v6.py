import sys

try:
    # Try different encodings
    encodings = ['utf-16', 'utf-16le', 'utf-8', 'cp1252']
    content = ""
    
    for enc in encodings:
        try:
            with open("server_debug_v6.log", "r", encoding=enc) as f:
                content = f.read()
                print(f"Successfully read with {enc}")
                break
        except Exception:
            continue
            
    if not content:
        print("Failed to read log file with any encoding")
        sys.exit(1)
        
    print(content)
        
except Exception as e:
    print(f"Error: {e}")
