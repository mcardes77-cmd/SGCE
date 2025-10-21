#!/usr/bin/env python3
"""
Script para verificar rotas duplicadas no app.py
"""

import ast
import collections

def find_duplicate_routes(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Parse do código Python
    tree = ast.parse(content)
    
    # Encontrar todas as rotas
    routes = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Verificar se é uma rota (tem decorator)
            for decorator in node.decorator_list:
                if (isinstance(decorator, ast.Call) and 
                    isinstance(decorator.func, ast.Attribute) and
                    decorator.func.attr == 'route'):
                    
                    # Extrair o path da rota
                    if decorator.args and isinstance(decorator.args[0], ast.Str):
                        route_path = decorator.args[0].s
                        routes.append((route_path, node.name))
    
    # Verificar duplicatas
    route_paths = [route[0] for route in routes]
    duplicates = [item for item, count in collections.Counter(route_paths).items() if count > 1]
    
    if duplicates:
        print("🚨 ROTAS DUPLICADAS ENCONTRADAS:")
        for dup in duplicates:
            functions = [name for path, name in routes if path == dup]
            print(f"  {dup}: {functions}")
    else:
        print("✅ Nenhuma rota duplicada encontrada")
    
    return duplicates

if __name__ == "__main__":
    duplicates = find_duplicate_routes('app.py')
    if duplicates:
        exit(1)
    else:
        exit(0)
