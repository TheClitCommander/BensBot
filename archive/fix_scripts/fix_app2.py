#!/usr/bin/env python3

def fix_app_file():
    print("Reading app.py file...")
    
    with open("app.py", "r") as file:
        lines = file.readlines()
    
    print("Fixing issues line by line...")
    fixed_lines = []
    in_markdown = False
    markdown_content = []
    
    for line in lines:
        # Fix docstrings
        if '"""' in line and 'def ' in line:
            line = line.replace('"""', '# ')
        
        # Fix bullet character
        if ' • ' in line:
            line = line.replace(' • ', ' &bull; ')
        
        # Handle multiline f-strings in st.markdown
        if 'st.markdown(f"""' in line:
            in_markdown = True
            line = line.replace('st.markdown(f"""', 'st.markdown("""')
            markdown_content = [line]
            continue
        
        if in_markdown:
            markdown_content.append(line)
            if '""", unsafe_allow_html=True)' in line:
                in_markdown = False
                # Join all lines and replace { with {{ and } with }}
                joined = ''.join(markdown_content)
                joined = joined.replace('{', '{{').replace('}', '}}')
                # But fix back the curly braces in actual variables
                joined = joined.replace('{{{{', '{').replace('}}}}', '}')
                fixed_lines.append(joined)
                markdown_content = []
            continue
        
        fixed_lines.append(line)
    
    print("Writing fixed file to app_fixed2.py...")
    with open("app_fixed2.py", "w") as file:
        file.writelines(fixed_lines)
    
    print("Done! Run 'streamlit run app_fixed2.py' to start the app.")

if __name__ == "__main__":
    fix_app_file() 