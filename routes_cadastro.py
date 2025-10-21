from flask import Blueprint, request, jsonify
from datetime import datetime
import logging
# Assumindo que db_utils contém as variáveis e funções do Supabase
from db_utils import supabase, handle_supabase_response 

# Define o Blueprint para as rotas de Cadastro
cadastro_bp = Blueprint('cadastro', __name__)

# =========================================================
# FUNÇÕES DE VALIDAÇÃO E UTILIDADE
# =========================================================

def validate_required_fields(data, required_fields):
    """Verifica se todos os campos obrigatórios estão presentes no dicionário de dados."""
    missing = [field for field in required_fields if not data.get(field)]
    if missing:
        return f"Campos obrigatórios ausentes: {', '.join(missing)}", False
    return None, True

# =========================================================
# ROTAS CRUD GENÉRICAS (STAFF, SALAS, DISCIPLINAS, ETC.)
# =========================================================

# --- Professores/Funcionários (d_funcionarios) --- CORRIGIDO
@cadastro_bp.route('/api/funcionarios', methods=['GET', 'POST'])
@cadastro_bp.route('/api/funcionarios/<item_id>', methods=['DELETE', 'PUT'])
def api_cadastro_staff(item_id=None):
    table_name = 'd_funcionarios'  # CORRIGIDO: era 'd_professores_funcionarios'
    # 'id' é a matrícula/ID do funcionário
    required_fields_post = ['id', 'nome', 'funcao', 'email', 'celular'] 
    
    try:
        if request.method == 'GET':
            resp = supabase.table(table_name).select('*').order('nome').execute()
            return jsonify(handle_supabase_response(resp)), 200

        elif request.method == 'POST':
            data = request.json
            error, valid = validate_required_fields(data, required_fields_post)
            if not valid: return jsonify({"error": error}), 400
            
            data['timestamp_cadastro'] = datetime.now().isoformat()
            
            # Upsert é mais seguro para evitar duplicidade de ID
            resp = supabase.table(table_name).upsert(data).execute()
            handle_supabase_response(resp)
            return jsonify({"message": "Colaborador cadastrado/atualizado.", "id": resp.data[0]['id']}), 201

        elif request.method == 'PUT' and item_id:
            data = request.json
            resp = supabase.table(table_name).update(data).eq('id', item_id).execute()
            handle_supabase_response(resp)
            return jsonify({"message": "Colaborador atualizado."}), 200

        elif request.method == 'DELETE' and item_id:
            resp = supabase.table(table_name).delete().eq('id', item_id).execute()
            handle_supabase_response(resp)
            return jsonify({"message": "Colaborador excluído."}), 200
            
    except Exception as e:
        logging.exception(f"Erro na rota /api/funcionarios: {e}")
        return jsonify({"error": str(e)}), 500

# Rota de atalho de cadastro (JS usa essa rota)
@cadastro_bp.route('/api/cadastrar_funcionario', methods=['POST'])
def cadastrar_funcionario(): return api_cadastro_staff()

# --- Salas (d_salas) --- CORRIGIDO
@cadastro_bp.route('/api/salas', methods=['GET', 'POST'])
@cadastro_bp.route('/api/salas/<int:sala_id>', methods=['DELETE'])
def api_cadastro_salas(sala_id=None):
    table_name = 'd_salas'
    
    try:
        if request.method == 'GET':
            # CORRIGIDO: usando campo 'sala' ao invés de 'nome_turma'
            resp = supabase.table(table_name).select('id, nivel_ensino, sala').order('sala').execute()
            return jsonify(handle_supabase_response(resp)), 200

        elif request.method == 'POST':
            data = request.json
            # CORRIGIDO: validação com campos corretos
            if not data.get('nivel_ensino') or not data.get('nome_turma'):
                return jsonify({"error": "Campos obrigatórios ausentes: nivel_ensino, nome_turma"}), 400
            
            # CORRIGIDO: mapeando nome_turma para sala
            sala_data = {
                'nivel_ensino': data['nivel_ensino'],
                'sala': data['nome_turma'],  # CORRIGIDO: campo correto
                'nome': f"{data['nivel_ensino']} - {data['nome_turma']}"
            }
            
            resp = supabase.table(table_name).insert(sala_data).execute()
            handle_supabase_response(resp)
            return jsonify({"message": "Sala cadastrada.", "id": resp.data[0]['id']}), 201
        
        elif request.method == 'DELETE' and sala_id:
            resp = supabase.table(table_name).delete().eq('id', sala_id).execute()
            handle_supabase_response(resp)
            return jsonify({"message": "Sala excluída."}), 200

    except Exception as e:
        logging.exception(f"Erro na rota /api/salas: {e}")
        return jsonify({"error": str(e)}), 500

# Rota de atalho de cadastro (JS usa essa rota)
@cadastro_bp.route('/api/cadastrar_sala', methods=['POST'])
def cadastrar_sala(): return api_cadastro_salas()

# --- Disciplinas, Eletivas, Clubes, Equipamentos (CRUD Genérico) --- CORRIGIDO
@cadastro_bp.route('/api/<string:entity>', methods=['GET'])
@cadastro_bp.route('/api/<string:entity>', methods=['POST']) # /api/cadastrar_...
@cadastro_bp.route('/api/<string:entity>/<item_id>', methods=['DELETE'])
def api_cadastro_generic_crud(entity, item_id=None):
    
    entity_map = {
        'disciplinas': {'table': 'd_disciplinas', 'req': ['nome', 'abreviacao'], 'key': 'abreviacao'}, # Usa abreviacao como ID (String)
        'eletivas': {'table': 'd_eletivas', 'req': ['nome', 'semestre']},
        'clubes': {'table': 'd_clubes', 'req': ['nome', 'semestre']},
        # CORRIGIDO: mapeando para tabela correta
        'inventario': {'table': 'd_inventario_equipamentos', 'req': ['colmeia', 'equipamento_id']},
        'equipamentos': {'table': 'd_inventario_equipamentos', 'req': ['colmeia', 'equipamento_id']},
    }
    
    # Mapeamento para rotas de cadastro específicas do JS
    if 'cadastrar_' in entity:
        entity = entity.replace('cadastrar_', '')
    
    if entity not in entity_map:
        return jsonify({"error": "Entidade de cadastro inválida."}), 404
        
    config = entity_map[entity]
    table_name = config['table']
    key_column = config.get('key', 'id')

    try:
        if request.method == 'GET':
            resp = supabase.table(table_name).select('*').order('nome' if 'nome' in config['req'] else 'id').execute()
            return jsonify(handle_supabase_response(resp)), 200

        elif request.method == 'POST':
            data = request.json
            error, valid = validate_required_fields(data, config['req'])
            if not valid: return jsonify({"error": error}), 400
            
            # CORRIGIDO: para equipamentos, usar campo correto
            if entity in ['equipamentos', 'inventario']:
                data['status'] = 'DISPONÍVEL'
                # Mapear id_equipamento do frontend para equipamento_id do banco
                if 'id_equipamento' in data:
                    data['equipamento_id'] = data['id_equipamento']
                    del data['id_equipamento']
                
            resp = supabase.table(table_name).insert(data).execute()
            handle_supabase_response(resp)
            return jsonify({"message": f"{entity.capitalize()} cadastrado.", "id": resp.data[0]['id']}), 201

        elif request.method == 'DELETE' and item_id:
            # item_id pode ser ID (int) ou abreviacao (string) para disciplinas
            resp = supabase.table(table_name).delete().eq(key_column, item_id).execute()
            handle_supabase_response(resp)
            return jsonify({"message": f"{entity.capitalize()} excluído."}), 200
        
    except Exception as e:
        logging.exception(f"Erro na rota /api/{entity}: {e}")
        return jsonify({"error": str(e)}), 500

# Mapeando rotas de atalho para a função genérica (GET, POST, DELETE)
for ent in ['disciplinas', 'eletivas', 'clubes', 'inventario', 'equipamentos']:
    # Rotas POST específicas do JS (Ex: /api/cadastrar_disciplina)
    @cadastro_bp.route(f'/api/cadastrar_{ent}', methods=['POST'])
    def cadastrar_generico(ent=ent): return api_cadastro_generic_crud(ent)
    
    # Rotas DELETE/GET mapeadas para a função genérica
    @cadastro_bp.route(f'/api/{ent}', methods=['GET'])
    def get_generico(ent=ent): return api_cadastro_generic_crud(ent)
    
    @cadastro_bp.route(f'/api/{ent}/<item_id>', methods=['DELETE'])
    def delete_generico(ent=ent, item_id=None): return api_cadastro_generic_crud(ent, item_id)


# =========================================================
# ROTAS DE CADASTRO DE ALUNOS (d_alunos)
# =========================================================

# ROTA: /api/alunos (GET - Lista com nomes de Sala e Tutor para o frontend)
@cadastro_bp.route('/api/alunos', methods=['GET'])
def api_get_alunos():
    try:
        # Busca d_alunos com JOINs implícitos (usando Supabase Foreign Key Joins)
        # CORRIGIDO: usando campo 'sala' ao invés de 'nome_turma'
        resp = supabase.table('d_alunos').select('*, sala_id:d_salas(sala), tutor_id:d_funcionarios(nome)').order('nome').execute()
        alunos_raw = handle_supabase_response(resp)
        
        # Formata para o formato esperado pelo gestao_cadastro_aluno.html
        alunos_formatados = [
            {
                'id': a['id'],
                'ra': a['ra'],
                'nome': a['nome'],
                'sala_nome': a.get('sala_id', {}).get('sala', 'N/A'),  # CORRIGIDO: campo correto
                'tutor_nome': a.get('tutor_id', {}).get('nome', 'Não Vinculado')
            } for a in alunos_raw
        ]
        
        return jsonify(alunos_formatados), 200
    except Exception as e:
        logging.exception("Erro /api/alunos (GET)")
        return jsonify({"error": str(e)}), 500

# ROTA: /api/alunos/<int:aluno_id> (DELETE)
@cadastro_bp.route('/api/alunos/<int:aluno_id>', methods=['DELETE'])
def api_delete_aluno(aluno_id):
    try:
        resp = supabase.table('d_alunos').delete().eq('id', aluno_id).execute()
        handle_supabase_response(resp)
        return jsonify({"message": "Aluno excluído com sucesso."}), 200
    except Exception as e:
        logging.exception("Erro /api/alunos/<id> (DELETE)")
        return jsonify({"error": str(e)}), 500

# ROTA: /api/cadastrar_aluno (POST)
@cadastro_bp.route('/api/cadastrar_aluno', methods=['POST'])
def api_post_aluno():
    data = request.json
    required_fields = ['ra', 'nome', 'sala_id', 'tutor_id']
    error, valid = validate_required_fields(data, required_fields)
    if not valid: return jsonify({"error": error}), 400

    try:
        aluno_data = {
            'ra': data['ra'],
            'nome': data['nome'],
            'sala_id': int(data['sala_id']),
            'tutor_id': int(data['tutor_id']),
            'timestamp_cadastro': datetime.now().isoformat()
        }
        
        resp = supabase.table('d_alunos').insert(aluno_data).execute()
        handle_supabase_response(resp)
        return jsonify({"message": "Aluno cadastrado com sucesso.", "id": resp.data[0]['id']}), 201

    except Exception as e:
        logging.exception("Erro /api/cadastrar_aluno (POST)")
        return jsonify({"error": str(e)}), 500

# ROTA: /api/alunos_por_sala/<int:sala_id> (GET)
@cadastro_bp.route('/api/alunos_por_sala/<int:sala_id>', methods=['GET'])
def api_alunos_por_sala(sala_id):
    try:
        # Busca id, nome, e o tutor_id atual para fins de exibição na tela de vinculação
        resp = supabase.table('d_alunos').select('id, nome, tutor_id').eq('sala_id', sala_id).order('nome').execute()
        alunos = handle_supabase_response(resp)
        return jsonify(alunos), 200
    except Exception as e:
        logging.exception("Erro /api/alunos_por_sala")
        return jsonify({"error": str(e)}), 500
        
# ROTA: /api/alunos_por_tutor/<int:tutor_id> (GET)
# Necessário para carregar alunos já vinculados (gestao_cadastro_vinculacao_tutor_aluno.html)
@cadastro_bp.route('/api/alunos_por_tutor/<int:tutor_id>', methods=['GET'])
def api_alunos_por_tutor(tutor_id):
    try:
        resp = supabase.table('d_alunos').select('id, nome').eq('tutor_id', tutor_id).order('nome').execute()
        alunos = handle_supabase_response(resp)
        return jsonify(alunos), 200
    except Exception as e:
        logging.exception("Erro /api/alunos_por_tutor")
        return jsonify({"error": str(e)}), 500

# =========================================================
# ROTAS DE VINCULAÇÃO
# =========================================================

# --- VINCULAÇÃO TUTOR-ALUNO ---
@cadastro_bp.route('/api/vincular_tutor_aluno', methods=['POST'])
def api_vincular_tutor_aluno():
    data = request.json
    tutor_id = data.get('tutor_id')
    sala_id = data.get('sala_id')
    vinculos = data.get('vinculos', []) # Lista de alunos que DEVEM estar vinculados
    
    # IDs dos alunos que devem ser vinculados ao tutor selecionado
    alunos_a_vincular_ids = {int(v['aluno_id']) for v in vinculos}

    if not tutor_id or not sala_id:
        return jsonify({"error": "IDs de tutor e sala são obrigatórios."}), 400
    
    try:
        tutor_id_int = int(tutor_id)
        
        # 1. Busca TODOS os alunos da sala
        resp_alunos = supabase.table('d_alunos').select('id, nome, tutor_id').eq('sala_id', int(sala_id)).execute()
        alunos_sala = handle_supabase_response(resp_alunos)
        
        updates = []
        for aluno in alunos_sala:
            aluno_id = aluno['id']
            
            if aluno_id in alunos_a_vincular_ids:
                # 1.1. VINCULAR: Se está selecionado E não está vinculado a este tutor, ou está vinculado a outro.
                if aluno['tutor_id'] != tutor_id_int:
                    updates.append({'id': aluno_id, 'tutor_id': tutor_id_int})
            else:
                # 1.2. DESVINCULAR: Se NÃO está selecionado E está vinculado a ESTE tutor.
                if aluno['tutor_id'] == tutor_id_int:
                    updates.append({'id': aluno_id, 'tutor_id': None})
        
        if not updates:
            return jsonify({"message": "Nenhuma alteração de vínculo detectada."}), 200
            
        # 2. Executa a atualização em lote
        for update in updates:
            supabase.table('d_alunos').update({'tutor_id': update['tutor_id']}).eq('id', update['id']).execute()

        msg = f"Vínculos processados. Total de alterações: {len(updates)}."
        return jsonify({"message": msg}), 200

    except Exception as e:
        logging.exception("Erro /api/vincular_tutor_aluno (POST)")
        return jsonify({"error": str(e)}), 500


# --- VINCULAÇÃO DISCIPLINA-SALA --- CORRIGIDO

# ROTA: /api/vinculacoes_disciplinas/<int:sala_id> (GET)
@cadastro_bp.route('/api/vinculacoes_disciplinas/<int:sala_id>', methods=['GET'])
def api_get_vinculacoes_disciplinas(sala_id):
    try:
        # CORRIGIDO: tabela correta
        resp = supabase.table('vinculos_disciplina_sala').select('disciplina_id').eq('sala_id', sala_id).execute()
        
        # Retorna apenas o array de IDs (abreviações)
        disciplina_ids = [d['disciplina_id'] for d in handle_supabase_response(resp)]
        
        return jsonify({"disciplinas": disciplina_ids}), 200
    except Exception as e:
        logging.exception("Erro /api/vinculacoes_disciplinas")
        return jsonify({"error": str(e)}), 500

# ROTA: /api/vincular_disciplina_sala (POST)
@cadastro_bp.route('/api/vincular_disciplina_sala', methods=['POST'])
def api_vincular_disciplina_sala():
    data = request.json
    sala_id = data.get('sala_id')
    disciplina_ids = data.get('disciplinas', []) # Lista de IDs (abreviações) de disciplinas
    
    if not sala_id:
        return jsonify({"error": "ID da sala é obrigatório."}), 400
        
    try:
        # CORRIGIDO: tabela correta
        supabase.table('vinculos_disciplina_sala').delete().eq('sala_id', int(sala_id)).execute()
        
        if not disciplina_ids:
             return jsonify({"message": "Todos os vínculos de disciplina foram removidos com sucesso."}), 200

        # 2. Insere os novos vínculos
        novos_vinculos = [
            {'sala_id': int(sala_id), 'disciplina_id': disc_id}
            for disc_id in disciplina_ids
        ]
        
        # CORRIGIDO: tabela correta
        resp = supabase.table('vinculos_disciplina_sala').insert(novos_vinculos).execute()
        handle_supabase_response(resp)
        
        return jsonify({"message": f"{len(novos_vinculos)} disciplina(s) vinculada(s) à sala {sala_id} com sucesso."}), 201
        
    except Exception as e:
        logging.exception("Erro /api/vincular_disciplina_sala (POST)")
        return jsonify({"error": str(e)}), 500