import sys

try:
    # Try different encodings
    encodings = ['utf-16', 'utf-16le', 'utf-8', 'cp1252']
    content = ""
    
    for enc in encodings:
        try:
            with open("server_debug_v4.log", "r", encoding=enc) as f:
                content = f.read()
                print(f"Successfully read with {enc}")
                break
        except Exception:
            continue
            
    if not content:
        print("Failed to read log file with any encoding")
        sys.exit(1)
        
    lines = content.splitlines()
    debug_lines = [line for line in lines if "DEBUG:" in line]
    
    print(f"Found {len(debug_lines)} DEBUG lines:")
    for line in debug_lines:
        print(line)
        
except Exception as e:
    print(f"Error: {e}")
