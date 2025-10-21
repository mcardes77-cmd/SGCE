# routes_tutoria.py - CORRIGIDO
from flask import Blueprint, request, jsonify
from datetime import datetime
import logging
from db_utils import get_supabase, handle_supabase_response

tutoria_bp = Blueprint('tutoria', __name__)

# =========================================================
# ROTAS AUXILIARES (PARA CARREGAMENTO DE DADOS)
# =========================================================

@tutoria_bp.route('/api/tutoria/tutores', methods=['GET'])
def api_get_tutores_tutoria():
    """Busca tutores para o módulo de tutoria"""
    try:
        supabase = get_supabase()
        response = supabase.table('d_funcionarios').select('id, nome').eq('is_tutor', True).order('nome').execute()
        tutores = response.data if response.data else []
        return jsonify(tutores), 200
    except Exception as e:
        logging.error(f"Erro /api/tutoria/tutores: {str(e)}")
        return jsonify({"error": f"Falha ao buscar tutores: {str(e)}"}), 500

@tutoria_bp.route('/api/tutoria/alunos_por_tutor/<int:tutor_id>', methods=['GET'])
def api_alunos_por_tutor(tutor_id):
    """Busca alunos por tutor"""
    try:
        supabase = get_supabase()
        response = supabase.table('d_alunos').select('id, nome, matricula, sala_id').eq('tutor_id', tutor_id).order('nome').execute()
        alunos = response.data if response.data else []
        return jsonify(alunos), 200
    except Exception as e:
        logging.error(f"Erro /api/tutoria/alunos_por_tutor: {str(e)}")
        return jsonify({"error": f"Falha ao buscar alunos: {str(e)}"}), 500

@tutoria_bp.route('/api/tutoria/disciplinas', methods=['GET'])
def api_get_disciplinas_tutoria():
    """Busca disciplinas para o módulo de tutoria"""
    try:
        supabase = get_supabase()
        response = supabase.table('d_disciplinas').select('id, nome, codigo').order('nome').execute()
        disciplinas = response.data if response.data else []
        return jsonify(disciplinas), 200
    except Exception as e:
        logging.error(f"Erro /api/tutoria/disciplinas: {str(e)}")
        return jsonify({"error": f"Falha ao buscar disciplinas: {str(e)}"}), 500

# =========================================================
# ROTAS DE FICHA DE TUTORIA - CORRIGIDAS
# =========================================================

@tutoria_bp.route('/api/tutoria/ficha/<int:aluno_id>', methods=['GET'])
def api_ficha_tutoria(aluno_id):
    """Busca ficha completa do aluno - CORRIGIDO"""
    try:
        supabase = get_supabase()
        
        # Busca dados básicos do aluno
        aluno_response = supabase.table('d_alunos').select('*, d_salas(sala), d_funcionarios!d_alunos_tutor_id_fkey(nome)').eq('id', aluno_id).execute()
        
        if not aluno_response.data:
            return jsonify({"error": "Aluno não encontrado"}), 404
            
        aluno = aluno_response.data[0]
        
        # Busca atendimentos de tutoria
        atendimentos_response = supabase.table('t_tutoria_atendimentos').select('*').eq('aluno_id', aluno_id).order('data_atendimento', desc=True).execute()
        atendimentos = atendimentos_response.data if atendimentos_response.data else []
        
        # Busca notas do aluno
        notas_response = supabase.table('t_tutoria_notas').select('*').eq('aluno_id', aluno_id).execute()
        notas = notas_response.data[0] if notas_response.data else {}
        
        # Busca frequência do aluno (últimos 30 dias)
        data_limite = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        frequencia_response = supabase.table('t_frequencia').select('*').eq('aluno_id', aluno_id).gte('data', data_limite).order('data', desc=True).execute()
        frequencia = frequencia_response.data if frequencia_response.data else []
        
        # Monta ficha consolidada
        ficha = {
            "aluno": {
                "id": aluno['id'],
                "nome": aluno['nome'],
                "matricula": aluno.get('matricula', ''),
                "sala": aluno.get('d_salas', {}).get('sala', ''),
                "tutor": aluno.get('d_funcionarios', {}).get('nome', '')
            },
            "atendimentos": atendimentos,
            "notas": notas.get('notas', {}) if notas else {},
            "frequencia_recente": frequencia,
            "estatisticas": {
                "total_atendimentos": len(atendimentos),
                "atendimentos_30_dias": len([a for a in atendimentos if a.get('data_atendimento', '') >= data_limite]),
                "faltas_30_dias": len([f for f in frequencia if f.get('status') == 'F'])
            }
        }
        
        return jsonify(ficha), 200

    except Exception as e:
        logging.error(f"Erro /api/tutoria/ficha: {str(e)}")
        return jsonify({"error": f"Falha ao buscar ficha: {str(e)}"}), 500

# =========================================================
# ROTAS DE ATENDIMENTOS - CORRIGIDAS
# =========================================================

@tutoria_bp.route('/api/tutoria/atendimentos', methods=['GET'])
def api_get_atendimentos():
    """Busca atendimentos com filtros"""
    try:
        aluno_id = request.args.get('aluno_id')
        tutor_id = request.args.get('tutor_id')
        
        supabase = get_supabase()
        query = supabase.table('t_tutoria_atendimentos').select('*, d_alunos(nome), d_funcionarios(nome)')
        
        if aluno_id:
            query = query.eq('aluno_id', aluno_id)
        if tutor_id:
            query = query.eq('tutor_id', tutor_id)
            
        query = query.order('data_atendimento', desc=True)
        response = query.execute()
        
        atendimentos = response.data if response.data else []
        return jsonify(atendimentos), 200
        
    except Exception as e:
        logging.error(f"Erro /api/tutoria/atendimentos: {str(e)}")
        return jsonify({"error": f"Falha ao buscar atendimentos: {str(e)}"}), 500

@tutoria_bp.route('/api/tutoria/atendimentos', methods=['POST'])
def api_criar_atendimento():
    """Cria novo atendimento de tutoria - CORRIGIDO"""
    try:
        data = request.get_json()
        
        required_fields = ['aluno_id', 'tutor_id', 'tipo_atendimento', 'descricao']
        missing = [field for field in required_fields if not data.get(field)]
        if missing:
            return jsonify({"error": f"Campos obrigatórios ausentes: {', '.join(missing)}"}), 400

        supabase = get_supabase()
        
        atendimento_data = {
            "aluno_id": data['aluno_id'],
            "tutor_id": data['tutor_id'],
            "tipo_atendimento": data['tipo_atendimento'],
            "descricao": data['descricao'],
            "data_atendimento": data.get('data_atendimento', datetime.now().isoformat()),
            "status": data.get('status', 'REALIZADO'),
            "observacoes": data.get('observacoes', ''),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        response = supabase.table('t_tutoria_atendimentos').insert(atendimento_data).execute()
        
        if response.data:
            return jsonify({
                "message": "Atendimento registrado com sucesso!",
                "atendimento": response.data[0]
            }), 201
        else:
            return jsonify({"error": "Falha ao criar atendimento"}), 500

    except Exception as e:
        logging.error(f"Erro /api/tutoria/atendimentos POST: {str(e)}")
        return jsonify({"error": f"Falha ao criar atendimento: {str(e)}"}), 500

@tutoria_bp.route('/api/tutoria/atendimentos/<int:atendimento_id>', methods=['PUT'])
def api_atualizar_atendimento(atendimento_id):
    """Atualiza atendimento existente"""
    try:
        data = request.get_json()
        
        supabase = get_supabase()
        
        update_data = {
            "tipo_atendimento": data.get('tipo_atendimento'),
            "descricao": data.get('descricao'),
            "status": data.get('status'),
            "observacoes": data.get('observacoes'),
            "updated_at": datetime.now().isoformat()
        }
        
        # Remove campos vazios
        update_data = {k: v for k, v in update_data.items() if v is not None}
        
        response = supabase.table('t_tutoria_atendimentos').update(update_data).eq('id', atendimento_id).execute()
        
        if response.data:
            return jsonify({
                "message": "Atendimento atualizado com sucesso!",
                "atendimento": response.data[0]
            }), 200
        else:
            return jsonify({"error": "Falha ao atualizar atendimento"}), 500

    except Exception as e:
        logging.error(f"Erro /api/tutoria/atendimentos PUT: {str(e)}")
        return jsonify({"error": f"Falha ao atualizar atendimento: {str(e)}"}), 500

# =========================================================
# ROTAS DE NOTAS - CORRIGIDAS
# =========================================================

@tutoria_bp.route('/api/tutoria/notas/<int:aluno_id>', methods=['GET'])
def api_get_notas(aluno_id):
    """Busca notas do aluno"""
    try:
        supabase = get_supabase()
        response = supabase.table('t_tutoria_notas').select('*').eq('aluno_id', aluno_id).execute()
        
        if response.data:
            return jsonify(response.data[0]), 200
        else:
            return jsonify({"notas": {}, "aluno_id": aluno_id}), 200

    except Exception as e:
        logging.error(f"Erro /api/tutoria/notas GET: {str(e)}")
        return jsonify({"error": f"Falha ao buscar notas: {str(e)}"}), 500

@tutoria_bp.route('/api/tutoria/notas', methods=['POST'])
def api_salvar_notas():
    """Salva/atualiza notas do aluno - CORRIGIDO"""
    try:
        data = request.get_json()
        
        if not data.get('aluno_id') or not data.get('notas'):
            return jsonify({"error": "aluno_id e notas são obrigatórios"}), 400

        supabase = get_supabase()
        
        # Verifica se já existe registro
        existing_response = supabase.table('t_tutoria_notas').select('id').eq('aluno_id', data['aluno_id']).execute()
        
        notas_data = {
            "aluno_id": data['aluno_id'],
            "notas": data['notas'],
            "updated_at": datetime.now().isoformat()
        }
        
        if existing_response.data:
            # Atualiza existente
            response = supabase.table('t_tutoria_notas').update(notas_data).eq('aluno_id', data['aluno_id']).execute()
        else:
            # Cria novo
            notas_data["created_at"] = datetime.now().isoformat()
            response = supabase.table('t_tutoria_notas').insert(notas_data).execute()
        
        if response.data:
            return jsonify({
                "message": "Notas salvas com sucesso!",
                "notas": response.data[0]
            }), 200
        else:
            return jsonify({"error": "Falha ao salvar notas"}), 500

    except Exception as e:
        logging.error(f"Erro /api/tutoria/notas POST: {str(e)}")
        return jsonify({"error": f"Falha ao salvar notas: {str(e)}"}), 500

# =========================================================
# ROTAS DE RELATÓRIOS
# =========================================================

@tutoria_bp.route('/api/tutoria/relatorio/tutor/<int:tutor_id>', methods=['GET'])
def api_relatorio_tutor(tutor_id):
    """Gera relatório consolidado do tutor"""
    try:
        supabase = get_supabase()
        
        # Busca alunos do tutor
        alunos_response = supabase.table('d_alunos').select('id, nome').eq('tutor_id', tutor_id).execute()
        alunos = alunos_response.data if alunos_response.data else []
        
        relatorio = {
            "tutor_id": tutor_id,
            "total_alunos": len(alunos),
            "alunos": []
        }
        
        for aluno in alunos:
            # Busca dados consolidados do aluno
            ficha_response = supabase.table('t_tutoria_atendimentos').select('*').eq('aluno_id', aluno['id']).execute()
            atendimentos = ficha_response.data if ficha_response.data else []
            
            # Busca frequência recente
            frequencia_response = supabase.table('t_frequencia').select('*').eq('aluno_id', aluno['id']).gte('data', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')).execute()
            frequencia = frequencia_response.data if frequencia_response.data else []
            
            relatorio["alunos"].append({
                "id": aluno['id'],
                "nome": aluno['nome'],
                "total_atendimentos": len(atendimentos),
                "faltas_30_dias": len([f for f in frequencia if f.get('status') == 'F']),
                "ultimo_atendimento": max([a['data_atendimento'] for a in atendimentos]) if atendimentos else None
            })
        
        return jsonify(relatorio), 200

    except Exception as e:
        logging.error(f"Erro /api/tutoria/relatorio/tutor: {str(e)}")
        return jsonify({"error": f"Falha ao gerar relatório: {str(e)}"}), 500
