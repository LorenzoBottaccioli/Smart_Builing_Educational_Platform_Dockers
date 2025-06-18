import os
import nbformat
from nbformat.v4 import new_code_cell

# 1. Localiza el IDF y el EPW subidos (ajusta el path si es distinto)
UPLOAD_DIR = os.path.join(os.getcwd(), 'uploads')
idf_files = [f for f in os.listdir(UPLOAD_DIR) if f.lower().endswith('.idf')]
epw_files = [f for f in os.listdir(UPLOAD_DIR) if f.lower().endswith('.epw')]

if not idf_files or not epw_files:
    raise RuntimeError("No se encontraron archivos .idf o .epw en uploads")

# Por ejemplo, nos quedamos con el primero de cada uno (o aplícales tu lógica)
idf_name = idf_files[0]
epw_name = epw_files[0]

# 2. Ruta al notebook
nb_path = os.path.join('surrogate_notebooks', 'SurrogateNotebook.ipynb')

# 3. Carga el notebook
nb = nbformat.read(nb_path, as_version=4)

# 4. Prepara la celda a insertar
cell_code = f"""# 🔧 Rutas de archivos subidos por el usuario
building = ef.get_building(r"../uploads/{idf_name}")
epw_file = r"../uploads/{epw_name}"
"""
injection_cell = new_code_cell(cell_code)

# 5. Encuentra la posición de la celda de imports (suponemos que es la primera)
#    e insertamos justo después
insert_at = 1  # si la celda 0 son los imports
nb.cells.insert(insert_at, injection_cell)

# 6. Guarda el notebook actualizado
nbformat.write(nb, nb_path)
print(f"Injected cell into {nb_path} with IDF={idf_name} and EPW={epw_name}")
