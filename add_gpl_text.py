import sys
import os

GPL_TEXT_TEMPLATE = """
'''
    This file is part of {project_name} (More Info: https://github.com/shs-it/{github_id}).

    {project_name} is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    {project_name} is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with {project_name}. If not, see <https://www.gnu.org/licenses/>.
'''
"""

def add_gpl_text_to_file(filepath: str, gpl_text: str):
    print(f'add license text to {filepath}')
    with open(filepath, 'r') as f:
        file_content = f.read()
    if not file_content.startswith(gpl_text):
        with open(filepath, 'w') as f:
            f.write(gpl_text)
            f.write('\n')
            if file_content:
                f.write('\n')
                f.write(file_content)

def add_gpl_text_to_directory(directory: str, gpl_text: str):
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isdir(filepath):
            add_gpl_text_to_directory(filepath, gpl_text)
        elif any(filepath.endswith(ext) for ext in ('.py', '.pyx', '.pxd', '.pyi')):
            add_gpl_text_to_file(filepath, gpl_text)

if __name__ == '__main__':
    if len(sys.argv) != 4:
        raise ValueError(sys.argv)
    add_gpl_text_to_directory(sys.argv[1], GPL_TEXT_TEMPLATE\
        .replace('{project_name}', sys.argv[2])
        .replace('{github_id}', sys.argv[3])
        .strip()
    )