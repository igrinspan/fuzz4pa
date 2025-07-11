
def compactar_trx_mismo_estado(ret_transiciones):
    """
    Compacta las transiciones que tienen el mismo estado de origen y destino,
    combinando sus etiquetas con saltos de línea.
    Ejemplo:
    Input:  "S09->S09 [label=a();b();]"
    Output: "S09->S09 [label=a()\nb()]"
    """
    def f_name(s):
        ret = s.strip().replace("label=", "").replace("]", "")
        ret = ret.replace(";", "")
        ret = ret.replace("\"t()", "τ")
        ret = ret.replace("t()", "τ")
        ret = ret.replace("t(n)", "τ")
        ret = ret.replace("();", "")
        ret = ret.strip()
        return ret

    def new_f_name(names):
        ret = "[label=\""
        names = list(filter(lambda x: x != "\"\"", names))
        for i, name in enumerate(names):
            if i != 0:
                if name != "":
                    ret += "\\n"
            ret += name.replace("\"","").replace("t();", "τ").replace("t(n);", "τ")
        ret += "\"]"
        return ret

    new_txs = {}
    for txs in ret_transiciones:
        txs = txs.strip().replace(" ", "")
        tx = txs.split("[")  # S09->S09 [label=t]
        processed_function = f_name(tx[1])
        if tx[0] in new_txs:
            # Solo agregar si no existe ya en la lista (evitar duplicados)
            if processed_function not in new_txs[tx[0]]:
                new_txs[tx[0]].append(processed_function)
        else:
            new_txs[tx[0]] = [processed_function]

    ret_transiciones.clear()
    for key, tx in new_txs.items():
        if tx != "\"\"":
            curr_name = tx
            # curr_name = curr_name.replace(";", "").replace("t()", "τ")
            new_name = new_f_name(curr_name)            
            ret_transiciones.append(f"{key} {new_name}")

def format_graph_file(file_path, output_path=None):
    """
    Formatea un archivo de grafo .epa para darle un formato más agradable.
    
    Args:
        file_path (str): Path del archivo .epa a formatear
        output_path (str, optional): Path donde guardar el archivo formateado. 
                                   Si es None, se sobrescribe el archivo original.
    
    Returns:
        str: El contenido del grafo formateado
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            lines = file.readlines()
    except FileNotFoundError:
        raise FileNotFoundError(f"No se pudo encontrar el archivo: {file_path}")
    except Exception as e:
        raise Exception(f"Error al leer el archivo {file_path}: {e}")
    
    output = []
    line_tmp = ""
    primeras_lineas = []
    
    for line in lines:
        line = line.strip()
        if "Prueba" in line or "{" in line or "}" in line:
            if line_tmp != "":
                primeras_lineas.append(line_tmp)
                line_tmp = ""
            continue
        line_tmp += line
        if line[-1] != "]":
            continue
        else:
            if "->" in line_tmp:
                output.append(line_tmp)
            else:
                if not line_tmp in primeras_lineas:
                    primeras_lineas.append(line_tmp)
            line_tmp = ""
    
    # cambio el formato de los estados
    for index_linea in range(len(primeras_lineas)):
        if not "[" in primeras_lineas[index_linea]:
            continue
        
        # Separar el nodo y su contenido de label
        linea = primeras_lineas[index_linea]
        if "[label=" in linea:
            # Extraer el nombre del nodo y el contenido del label
            partes = linea.split("[label=")
            nombre_nodo = partes[0].strip()
            contenido_label = partes[1].replace("]", "").strip()
            
            # Limpiar el contenido y separar funciones (sin eliminar espacios)
            contenido_limpio = contenido_label.replace(";", "").replace("t()", "").replace("t(n)", "").replace("\"", "")
            
            # Si hay múltiples funciones separadas por algún delimitador, separarlas
            # Solo separar si son funciones (terminan con paréntesis)
            funciones = []
            if contenido_limpio:
                import re
                # Buscar patrones que parezcan nombres de funciones (terminan con paréntesis)
                patron_funciones = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*\([^)]*\)', contenido_limpio)
                if len(patron_funciones) > 1:
                    # Solo si hay múltiples funciones, las separamos
                    funciones = patron_funciones
                else:
                    # Si no hay múltiples funciones, mantener el contenido original
                    funciones = [contenido_limpio] if contenido_limpio else []
            
            # Formatear el label con saltos de línea SOLO si hay múltiples funciones
            if len(funciones) > 1:
                label_formateado = "\\n".join(funciones)
                primeras_lineas[index_linea] = f'{nombre_nodo}[label="{label_formateado}"]'
            else:
                primeras_lineas[index_linea] = f'{nombre_nodo}[label="{contenido_limpio}"]'
        else:
            # Si no tiene label, solo agregar el formato de círculo
            estilo_circulo = "]"
            primeras_lineas[index_linea] = primeras_lineas[index_linea][0:-1] + estilo_circulo
            new_label_state = primeras_lineas[index_linea].replace(";", "").replace("t()", "").replace("t(n)", "")
            primeras_lineas[index_linea] = new_label_state

    compactar_trx_mismo_estado(output)

    output.extend(primeras_lineas)
    output.insert(0, "digraph {")
    output.append("}")

    formatted_content = "\n".join(output)
    
    # Guardar el archivo formateado
    save_path = output_path if output_path else file_path
    try:
        with open(save_path, "w", encoding="utf-8") as file:
            file.write(formatted_content)
    except Exception as e:
        raise Exception(f"Error al escribir el archivo {save_path}: {e}")
    
    return formatted_content
