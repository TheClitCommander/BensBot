#!/usr/bin/env python3

import re

def fix_app_file():
    print("Reading app.py file...")
    with open("app.py", "r") as file:
        content = file.read()
    
    print("Fixing docstrings...")
    # Replace any docstrings in function definitions with comments
    content = re.sub(r'(\s*)def\s+([^\(]+)\([^\)]*\):\s*\n\s*"""([^"]+)"""', r'\1def \2():\n\1    # \3', content)
    
    print("Fixing bullet characters...")
    # Replace bullet characters with HTML entities
    content = content.replace(" • ", " &bull; ")
    
    print("Fixing string formatting issues...")
    # Fix multiline f-strings by using raw strings
    pattern = r'st\.markdown\(f"""'
    replacement = r'st.markdown(fr"""'
    content = content.replace(pattern, replacement)
    
    print("Writing fixed file to app_fixed.py...")
    with open("app_fixed.py", "w") as file:
        file.write(content)
    
    print("Done! Run 'streamlit run app_fixed.py' to start the app.")

if __name__ == "__main__":
    fix_app_file() 