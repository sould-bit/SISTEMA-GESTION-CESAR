
import os

path = r'c:\Users\jp151\lab\el_rincon\SISTEMA-GESTION-CESAR\panel admin y operativo\src\features\admin\CreateOrderPage.tsx'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip = False
for i in range(len(lines)):
    if skip:
        skip = False
        continue
    
    # Check for duplicate return (
    if i < len(lines) - 1:
        line1 = lines[i].strip()
        line2 = lines[i+1].strip()
        
        if line1 == 'return (' and line2 == 'return (':
            new_lines.append(lines[i]) # Keep one
            skip = True
            continue
            
        if line1 == '<button' and line2 == '<button':
            new_lines.append(lines[i]) # Keep one
            skip = True
            continue

    new_lines.append(lines[i])

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print("File fixed successfully")
