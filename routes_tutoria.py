from flask import Blueprint, request, jsonify
from datetime import datetime
import logging
from db_utils import get_supabase, handle_supabase_response

# Define o Blueprint para as rotas de Tutoria
tutoria_bp = Blueprint('tutoria', __name__)

# =========================================================
# ROTAS DE LOOKUP (TUTORES E ALUNOS)
# =========================================================

# ROTA: /api/tutores (Busca todos os professores que são tutores)
@tutoria_bp.route('/api/tutores', methods=['GET'])
def api_get_tutores():
    try:
        supabase = get_supabase()
        if not supabase:
            return jsonify({"error": "Serviço de banco de dados indisponível"}), 503

        # Busca no Dicionário de Tutores (d_tutores)
        resp = supabase.table('d_tutores').select('id, nome').order('nome').execute()
        tutores = handle_supabase_response(resp)
        return jsonify(tutores), 200
    except Exception as e:
        logging.exception("Erro /api/tutores")
        return jsonify({"error": str(e)}), 500

# ROTA: /api/alunos_por_tutor/<int:tutor_id> (Busca alunos tutelados)
@tutoria_bp.route('/api/alunos_por_tutor/<int:tutor_id>', methods=['GET'])
def api_alunos_por_tutor(tutor_id):
    try:
        supabase = get_supabase()
        if not supabase:
            return jsonify({"error": "Serviço de banco de dados indisponível"}), 503

        # Busca alunos no Dicionário de Alunos (d_alunos)
        resp = supabase.table('d_alunos').select('id, nome, sala_id').eq('tutor_id', tutor_id).order('nome').execute()
        alunos = handle_supabase_response(resp)
        return jsonify(alunos), 200
    except Exception as e:
        logging.exception("Erro /api/alunos_por_tutor")
        return jsonify({"error": str(e)}), 500

# =========================================================
# ROTA DE FICHA DE TUTORIA (CONSOLIDADO)
# =========================================================

# ROTA: /api/tutoria/ficha/<int:aluno_id> (Ficha Completa)
@tutoria_bp.route('/api/tutoria/ficha/<int:aluno_id>', methods=['GET'])
def api_ficha_tutoria(aluno_id):
    try:
        supabase = get_supabase()
        if not supabase:
            return jsonify({"error": "Serviço de banco de dados indisponível"}), 503

        # Busca a ficha consolidada (Frequência, Notas, Histórico)
        resp = supabase.table('tutoria_geral').select('*').eq('aluno_id', aluno_id).single().execute()
        
        # Como é single, precisamos tratar a falta de dados
        ficha = handle_supabase_response(resp)
        if not ficha:
             # Retorna um objeto vazio (ou com valores default) se não encontrar a ficha
             return jsonify({}), 200

        return jsonify(ficha), 200
    except Exception as e:
        # Tratamento de erro 406 (single not found) ou outros erros
        if 'PostgrestError' in str(e) and 'not found' in str(e):
             return jsonify({"error": "Ficha de tutoria não encontrada para este aluno."}), 404
             
        logging.exception("Erro /api/tutoria/ficha")
        return jsonify({"error": f"Falha ao buscar ficha: {e}"}), 500

# =========================================================
# ROTAS DE REGISTRO E LANÇAMENTO
# =========================================================

# ROTA: /api/tutoria/agendamento (Salva/Atualiza Registro de Atendimento/Agendamento)
@tutoria_bp.route('/api/tutoria/agendamento', methods=['POST'])
def api_salvar_agendamento():
    data = request.json
    
    aluno_id = data.get('aluno_id')
    tutor_id = data.get('tutor_id')
    tipo_atendimento = data.get('tipo_atendimento')
    descricao = data.get('descricao_atendimento')
    
    if not all([aluno_id, tutor_id, tipo_atendimento, descricao]):
        return jsonify({"error": "Dados obrigatórios (aluno, tutor, tipo, descrição) ausentes."}), 400

    try:
        supabase = get_supabase()
        if not supabase:
            return jsonify({"error": "Serviço de banco de dados indisponível"}), 503

        registro = {
            "aluno_id": int(aluno_id),
            "tutor_id": int(tutor_id),
            "tipo_atendimento": tipo_atendimento,
            "descricao_atendimento": descricao,
            "status_agendamento": data.get('status_agendamento', 'pendente'),
            "data_registro": datetime.now().isoformat()
        }
        
        # Insere um novo registro de atendimento
        response = supabase.table('f_tutoria_atendimentos').insert(registro).execute()
        handle_supabase_response(response)

        return jsonify({"message": "Agendamento/Atendimento registrado com sucesso.", "status": 201}), 201
        
    except Exception as e:
        logging.exception("Erro /api/tutoria/agendamento")
        return jsonify({"error": f"Falha ao salvar agendamento: {e}"}), 500

# ROTA: /api/tutoria/notas (Upsert/Salva Notas Bimestrais)
@tutoria_bp.route('/api/tutoria/notas', methods=['POST'])
def api_salvar_notas():
    data = request.json
    aluno_id = data.get('aluno_id')
    notas = data.get('notas') # Esperado um dicionário complexo: { disciplina: {B1: x, B2: y, ...} }

    if not aluno_id or not notas:
        return jsonify({"error": "IDs de aluno e notas são obrigatórios."}), 400

    try:
        supabase = get_supabase()
        if not supabase:
            return jsonify({"error": "Serviço de banco de dados indisponível"}), 503

        aluno_id = int(aluno_id)
        
        # 1. Busca as notas existentes (para mergear os bimestres não alterados)
        resp_antiga = supabase.table('f_tutoria_notas').select('id, notas').eq('aluno_id', aluno_id).single().execute()
        
        notas_antigas = handle_supabase_response(resp_antiga)
        notas_existentes = notas_antigas.get('notas', {}) if notas_antigas else {}
        registro_id = notas_antigas.get('id') if notas_antigas else None

        # 2. Executa o UPSERT
        novo_registro = {
            "aluno_id": aluno_id,
            "notas": notas, # O front-end deve enviar o objeto de notas completo/mergeado
            "updated_at": datetime.now().isoformat()
        }
        
        # Se for um UPDATE (registro_id existe)
        if registro_id:
             response = supabase.table('f_tutoria_notas').update(novo_registro).eq('id', registro_id).execute()
        else:
             # Se for um INSERT (registro_id não existe)
             response = supabase.table('f_tutoria_notas').insert(novo_registro).execute()
             
        handle_supabase_response(response)
        
        return jsonify({"message": "Notas salvas/atualizadas com sucesso.", "status": 200}), 200

    except Exception as e:
        logging.exception("Erro /api/tutoria/notas")
        return jsonify({"error": f"Falha ao salvar notas: {e}"}), 500