from flask import Blueprint, request, jsonify
import logging
from db_utils import supabase, handle_supabase_response

cadastro_bp = Blueprint('cadastro', __name__)

# =========================================================
# 1. ROTAS PARA FUNCIONÁRIOS/PROFESSORES
# =========================================================

@cadastro_bp.route('/api/funcionarios', methods=['GET'])
def api_get_funcionarios():
    """Busca todos os funcionários/professores"""
    try:
        response = supabase.table('d_funcionarios').select('*').order('nome').execute()
        funcionarios = handle_supabase_response(response)
        return jsonify(funcionarios), 200
    except Exception as e:
        logging.exception("Erro /api/funcionarios")
        return jsonify({"error": f"Falha ao buscar funcionários: {str(e)}"}), 500

@cadastro_bp.route('/api/funcionarios/<int:funcionario_id>', methods=['GET'])
def api_get_funcionario(funcionario_id):
    """Busca um funcionário específico"""
    try:
        response = supabase.table('d_funcionarios').select('*').eq('id', funcionario_id).single().execute()
        funcionario = handle_supabase_response(response)
        return jsonify(funcionario), 200
    except Exception as e:
        logging.exception("Erro /api/funcionarios/<id>")
        return jsonify({"error": f"Falha ao buscar funcionário: {str(e)}"}), 500

@cadastro_bp.route('/api/funcionarios', methods=['POST'])
def api_criar_funcionario():
    """Cria um novo funcionário/professor"""
    data = request.json
    
    required_fields = ['nome', 'funcao', 'is_tutor']
    missing = [field for field in required_fields if not data.get(field)]
    if missing:
        return jsonify({"error": f"Campos obrigatórios ausentes: {', '.join(missing)}"}), 400

    try:
        funcionario_data = {
            "nome": data['nome'],
            "funcao": data['funcao'],
            "is_tutor": data['is_tutor'],
            "email": data.get('email')
        }
        
        response = supabase.table('d_funcionarios').insert(funcionario_data).execute()
        result = handle_supabase_response(response)
        
        return jsonify({
            "message": "Funcionário criado com sucesso",
            "id": result[0]['id'] if result else None
        }), 201

    except Exception as e:
        logging.exception("Erro /api/funcionarios POST")
        return jsonify({"error": f"Falha ao criar funcionário: {str(e)}"}), 500

# =========================================================
# 2. ROTAS PARA ALUNOS
# =========================================================

@cadastro_bp.route('/api/alunos', methods=['GET'])
def api_get_alunos():
    """Busca todos os alunos"""
    try:
        response = supabase.table('d_alunos').select('*').order('nome').execute()
        alunos = handle_supabase_response(response)
        return jsonify(alunos), 200
    except Exception as e:
        logging.exception("Erro /api/alunos")
        return jsonify({"error": f"Falha ao buscar alunos: {str(e)}"}), 500

@cadastro_bp.route('/api/alunos/<int:aluno_id>', methods=['GET'])
def api_get_aluno(aluno_id):
    """Busca um aluno específico"""
    try:
        response = supabase.table('d_alunos').select('*').eq('id', aluno_id).single().execute()
        aluno = handle_supabase_response(response)
        return jsonify(aluno), 200
    except Exception as e:
        logging.exception("Erro /api/alunos/<id>")
        return jsonify({"error": f"Falha ao buscar aluno: {str(e)}"}), 500

@cadastro_bp.route('/api/alunos', methods=['POST'])
def api_criar_aluno():
    """Cria um novo aluno"""
    data = request.json
    
    required_fields = ['nome', 'sala_id']
    missing = [field for field in required_fields if not data.get(field)]
    if missing:
        return jsonify({"error": f"Campos obrigatórios ausentes: {', '.join(missing)}"}), 400

    try:
        aluno_data = {
            "nome": data['nome'],
            "sala_id": data['sala_id'],
            "tutor_id": data.get('tutor_id')
        }
        
        response = supabase.table('d_alunos').insert(aluno_data).execute()
        result = handle_supabase_response(response)
        
        return jsonify({
            "message": "Aluno criado com sucesso",
            "id": result[0]['id'] if result else None
        }), 201

    except Exception as e:
        logging.exception("Erro /api/alunos POST")
        return jsonify({"error": f"Falha ao criar aluno: {str(e)}"}), 500

# =========================================================
# 3. ROTAS PARA SALAS
# =========================================================

@cadastro_bp.route('/api/salas', methods=['GET'])
def api_get_salas():
    """Busca todas as salas"""
    try:
        response = supabase.table('d_salas').select('*').order('sala').execute()
        salas = handle_supabase_response(response)
        return jsonify(salas), 200
    except Exception as e:
        logging.exception("Erro /api/salas")
        return jsonify({"error": f"Falha ao buscar salas: {str(e)}"}), 500

@cadastro_bp.route('/api/salas/<int:sala_id>', methods=['GET'])
def api_get_sala(sala_id):
    """Busca uma sala específica"""
    try:
        response = supabase.table('d_salas').select('*').eq('id', sala_id).single().execute()
        sala = handle_supabase_response(response)
        return jsonify(sala), 200
    except Exception as e:
        logging.exception("Erro /api/salas/<id>")
        return jsonify({"error": f"Falha ao buscar sala: {str(e)}"}), 500

@cadastro_bp.route('/api/salas', methods=['POST'])
def api_criar_sala():
    """Cria uma nova sala"""
    data = request.json
    
    required_fields = ['sala', 'nivel_ensino']
    missing = [field for field in required_fields if not data.get(field)]
    if missing:
        return jsonify({"error": f"Campos obrigatórios ausentes: {', '.join(missing)}"}), 400

    try:
        sala_data = {
            "sala": data['sala'],
            "nivel_ensino": data['nivel_ensino']
        }
        
        response = supabase.table('d_salas').insert(sala_data).execute()
        result = handle_supabase_response(response)
        
        return jsonify({
            "message": "Sala criada com sucesso",
            "id": result[0]['id'] if result else None
        }), 201

    except Exception as e:
        logging.exception("Erro /api/salas POST")
        return jsonify({"error": f"Falha ao criar sala: {str(e)}"}), 500

# =========================================================
# 4. ROTAS PARA DISCIPLINAS
# =========================================================

@cadastro_bp.route('/api/disciplinas', methods=['GET'])
def api_get_disciplinas():
    """Busca todas as disciplinas"""
    try:
        response = supabase.table('d_disciplinas').select('*').order('nome').execute()
        disciplinas = handle_supabase_response(response)
        return jsonify(disciplinas), 200
    except Exception as e:
        logging.exception("Erro /api/disciplinas")
        return jsonify({"error": f"Falha ao buscar disciplinas: {str(e)}"}), 500

@cadastro_bp.route('/api/disciplinas/<disciplina_id>', methods=['GET'])
def api_get_disciplina(disciplina_id):
    """Busca uma disciplina específica"""
    try:
        response = supabase.table('d_disciplinas').select('*').eq('id', disciplina_id).single().execute()
        disciplina = handle_supabase_response(response)
        return jsonify(disciplina), 200
    except Exception as e:
        logging.exception("Erro /api/disciplinas/<id>")
        return jsonify({"error": f"Falha ao buscar disciplina: {str(e)}"}), 500

@cadastro_bp.route('/api/disciplinas', methods=['POST'])
def api_criar_disciplina():
    """Cria uma nova disciplina"""
    data = request.json
    
    required_fields = ['id', 'nome']
    missing = [field for field in required_fields if not data.get(field)]
    if missing:
        return jsonify({"error": f"Campos obrigatórios ausentes: {', '.join(missing)}"}), 400

    try:
        disciplina_data = {
            "id": data['id'],
            "nome": data['nome'],
            "area_conhecimento": data.get('area_conhecimento')
        }
        
        response = supabase.table('d_disciplinas').insert(disciplina_data).execute()
        result = handle_supabase_response(response)
        
        return jsonify({
            "message": "Disciplina criada com sucesso",
            "id": result[0]['id'] if result else None
        }), 201

    except Exception as e:
        logging.exception("Erro /api/disciplinas POST")
        return jsonify({"error": f"Falha ao criar disciplina: {str(e)}"}), 500

# =========================================================
# 5. ROTAS PARA VINCULAÇÕES
# =========================================================

@cadastro_bp.route('/api/vinculacao/tutor_aluno', methods=['POST'])
def api_vincular_tutor_aluno():
    """Vincula um tutor a um aluno"""
    data = request.json
    
    required_fields = ['aluno_id', 'tutor_id']
    missing = [field for field in required_fields if not data.get(field)]
    if missing:
        return jsonify({"error": f"Campos obrigatórios ausentes: {', '.join(missing)}"}), 400

    try:
        # Atualiza o tutor do aluno
        response = supabase.table('d_alunos').update({
            "tutor_id": data['tutor_id']
        }).eq('id', data['aluno_id']).execute()
        
        handle_supabase_response(response)
        
        return jsonify({"message": "Tutor vinculado ao aluno com sucesso"}), 200

    except Exception as e:
        logging.exception("Erro /api/vinculacao/tutor_aluno")
        return jsonify({"error": f"Falha ao vincular tutor: {str(e)}"}), 500

@cadastro_bp.route('/api/vinculacao/disciplina_sala', methods=['POST'])
def api_vincular_disciplina_sala():
    """Vincula uma disciplina a uma sala"""
    data = request.json
    
    required_fields = ['sala_id', 'disciplina_id']
    missing = [field for field in required_fields if not data.get(field)]
    if missing:
        return jsonify({"error": f"Campos obrigatórios ausentes: {', '.join(missing)}"}), 400

    try:
        vinculo_data = {
            "sala_id": data['sala_id'],
            "disciplina_id": data['disciplina_id']
        }
        
        response = supabase.table('vinculos_disciplina_sala').insert(vinculo_data).execute()
        handle_supabase_response(response)
        
        return jsonify({"message": "Disciplina vinculada à sala com sucesso"}), 201

    except Exception as e:
        logging.exception("Erro /api/vinculacao/disciplina_sala")
        return jsonify({"error": f"Falha ao vincular disciplina: {str(e)}"}), 500

# =========================================================
# 6. ROTAS AUXILIARES
# =========================================================

@cadastro_bp.route('/api/tutores', methods=['GET'])
def api_get_tutores():
    """Busca apenas os funcionários que são tutores"""
    try:
        response = supabase.table('d_funcionarios').select('*').eq('is_tutor', True).order('nome').execute()
        tutores = handle_supabase_response(response)
        return jsonify(tutores), 200
    except Exception as e:
        logging.exception("Erro /api/tutores")
        return jsonify({"error": f"Falha ao buscar tutores: {str(e)}"}), 500

@cadastro_bp.route('/api/alunos_por_sala/<int:sala_id>', methods=['GET'])
def api_get_alunos_por_sala(sala_id):
    """Busca alunos por sala"""
    try:
        response = supabase.table('d_alunos').select('*').eq('sala_id', sala_id).order('nome').execute()
        alunos = handle_supabase_response(response)
        return jsonify(alunos), 200
    except Exception as e:
        logging.exception("Erro /api/alunos_por_sala")
        return jsonify({"error": f"Falha ao buscar alunos da sala: {str(e)}"}), 500
