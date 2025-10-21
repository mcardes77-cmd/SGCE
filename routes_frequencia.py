# routes_frequencia.py - CORRIGIDO
from flask import Blueprint, request, jsonify
from datetime import datetime
from calendar import monthrange
import logging
from db_utils import get_supabase, handle_supabase_response

frequencia_bp = Blueprint('frequencia', __name__)

# =========================================================
# ROTAS AUXILIARES (PARA CARREGAMENTO DE DADOS)
# =========================================================

@frequencia_bp.route('/api/frequencia/salas', methods=['GET'])
def api_get_salas_frequencia():
    """Busca salas para o módulo de frequência"""
    try:
        supabase = get_supabase()
        response = supabase.table('d_salas').select('id, sala').order('sala').execute()
        salas = handle_supabase_response(response)
        return jsonify(salas), 200
    except Exception as e:
        logging.error(f"Erro /api/frequencia/salas: {str(e)}")
        return jsonify({"error": f"Falha ao buscar salas: {str(e)}"}), 500

@frequencia_bp.route('/api/frequencia/alunos_por_sala/<int:sala_id>', methods=['GET'])
def api_get_alunos_por_sala_frequencia(sala_id):
    """Busca alunos por sala para frequência"""
    try:
        supabase = get_supabase()
        response = supabase.table('d_alunos').select('id, nome, matricula').eq('sala_id', sala_id).order('nome').execute()
        alunos = handle_supabase_response(response)
        return jsonify(alunos), 200
    except Exception as e:
        logging.error(f"Erro /api/frequencia/alunos_por_sala: {str(e)}")
        return jsonify({"error": f"Falha ao buscar alunos: {str(e)}"}), 500

# =========================================================
# ROTAS DE REGISTRO DIÁRIO DE FREQUÊNCIA (CORRIGIDAS)
# =========================================================

@frequencia_bp.route('/api/frequencia/status', methods=['GET'])
def api_frequencia_status():
    sala_id = request.args.get('sala_id')
    data = request.args.get('data')

    if not sala_id or not data:
        return jsonify({"error": "Parâmetros sala_id e data são obrigatórios."}), 400

    try:
        supabase = get_supabase()
        
        # Verifica se já existe registro para esta sala/data
        response = supabase.table('t_frequencia').select("id").eq('sala_id', sala_id).eq('data', data).execute()
        
        registrada = len(response.data) > 0 if response.data else False
        
        return jsonify({
            "registrada": registrada,
            "count": len(response.data) if response.data else 0
        }), 200

    except Exception as e:
        logging.error(f"Erro /api/frequencia/status: {str(e)}")
        return jsonify({"error": f"Falha ao verificar status: {str(e)}"}), 500

@frequencia_bp.route('/api/salvar_frequencia', methods=['POST'])
def api_salvar_frequencia():
    """Salva registro diário de frequência - CORRIGIDO"""
    try:
        data = request.get_json()
        if not data or not isinstance(data, list):
            return jsonify({"error": "Dados inválidos. Esperado uma lista de registros."}), 400

        supabase = get_supabase()
        
        # Verifica se já existe registro para evitar duplicação
        primeiro_registro = data[0]
        sala_id = primeiro_registro.get('sala_id')
        data_registro = primeiro_registro.get('data')
        
        if not sala_id or not data_registro:
            return jsonify({"error": "Dados de sala e data são obrigatórios."}), 400

        # Remove registros existentes para esta sala/data
        delete_response = supabase.table('t_frequencia').delete().eq('sala_id', sala_id).eq('data', data_registro).execute()
        
        # Prepara novos registros
        registros = []
        for registro in data:
            registros.append({
                "aluno_id": registro.get('aluno_id'),
                "sala_id": registro.get('sala_id'),
                "data": registro.get('data'),
                "status": registro.get('status', 'F'),  # Default para falta
                "timestamp_registro": datetime.now().isoformat()
            })
        
        # Insere novos registros
        insert_response = supabase.table('t_frequencia').insert(registros).execute()
        
        if insert_response.data:
            return jsonify({
                "message": f"Frequência de {len(registros)} alunos registrada com sucesso!",
                "registros": len(insert_response.data)
            }), 201
        else:
            return jsonify({"error": "Falha ao salvar registros"}), 500

    except Exception as e:
        logging.error(f"Erro /api/salvar_frequencia: {str(e)}")
        return jsonify({"error": f"Falha ao salvar frequência: {str(e)}"}), 500

# =========================================================
# ROTAS DE EVENTOS (ATRASO/SAÍDA) - CORRIGIDAS
# =========================================================

@frequencia_bp.route('/api/salvar_atraso', methods=['POST'])
def api_salvar_atraso():
    """Registra atraso do aluno - CORRIGIDO"""
    try:
        data = request.get_json()
        
        required_fields = ['aluno_id', 'sala_id', 'data', 'hora_atraso']
        missing = [field for field in required_fields if not data.get(field)]
        if missing:
            return jsonify({"error": f"Campos obrigatórios ausentes: {', '.join(missing)}"}), 400

        supabase = get_supabase()
        
        # Verifica/atualiza registro principal de frequência
        freq_response = supabase.table('t_frequencia').select('*').eq('aluno_id', data['aluno_id']).eq('data', data['data']).execute()
        
        if freq_response.data:
            # Atualiza registro existente
            update_data = {
                "status": 'PA',  # Presença com Atraso
                "timestamp_registro": datetime.now().isoformat()
            }
            supabase.table('t_frequencia').update(update_data).eq('aluno_id', data['aluno_id']).eq('data', data['data']).execute()
        else:
            # Cria novo registro
            novo_registro = {
                "aluno_id": data['aluno_id'],
                "sala_id": data['sala_id'],
                "data": data['data'],
                "status": 'PA',
                "timestamp_registro": datetime.now().isoformat()
            }
            supabase.table('t_frequencia').insert(novo_registro).execute()

        # Registra detalhes do atraso
        registro_atraso = {
            "aluno_id": data['aluno_id'],
            "data": data['data'],
            "hora_atraso": data['hora_atraso'],
            "motivo": data.get('motivo_atraso', ''),
            "responsavel": data.get('responsavel_atraso', ''),
            "telefone": data.get('telefone_atraso', ''),
            "tipo_registro": 'ATRASO',
            "timestamp": datetime.now().isoformat()
        }
        
        atraso_response = supabase.table('t_atrasos_saidas').insert(registro_atraso).execute()
        
        return jsonify({
            "message": "Atraso registrado com sucesso!",
            "status": "PA"
        }), 200

    except Exception as e:
        logging.error(f"Erro /api/salvar_atraso: {str(e)}")
        return jsonify({"error": f"Falha ao registrar atraso: {str(e)}"}), 500

@frequencia_bp.route('/api/salvar_saida_antecipada', methods=['POST'])
def api_salvar_saida_antecipada():
    """Registra saída antecipada do aluno - CORRIGIDO"""
    try:
        data = request.get_json()
        
        required_fields = ['aluno_id', 'sala_id', 'data', 'hora_saida']
        missing = [field for field in required_fields if not data.get(field)]
        if missing:
            return jsonify({"error": f"Campos obrigatórios ausentes: {', '.join(missing)}"}), 400

        supabase = get_supabase()
        
        # Verifica/atualiza registro principal de frequência
        freq_response = supabase.table('t_frequencia').select('*').eq('aluno_id', data['aluno_id']).eq('data', data['data']).execute()
        
        status_final = 'PS'  # Presença com Saída Antecipada
        
        if freq_response.data:
            status_atual = freq_response.data[0].get('status', '')
            if status_atual == 'PA':
                status_final = 'PSA'  # Presença com Atraso e Saída
            
            update_data = {
                "status": status_final,
                "timestamp_registro": datetime.now().isoformat()
            }
            supabase.table('t_frequencia').update(update_data).eq('aluno_id', data['aluno_id']).eq('data', data['data']).execute()
        else:
            # Cria novo registro
            novo_registro = {
                "aluno_id": data['aluno_id'],
                "sala_id": data['sala_id'],
                "data": data['data'],
                "status": status_final,
                "timestamp_registro": datetime.now().isoformat()
            }
            supabase.table('t_frequencia').insert(novo_registro).execute()

        # Registra detalhes da saída
        registro_saida = {
            "aluno_id": data['aluno_id'],
            "data": data['data'],
            "hora_saida": data['hora_saida'],
            "motivo": data.get('motivo_saida', ''),
            "responsavel": data.get('responsavel_saida', ''),
            "telefone": data.get('telefone_saida', ''),
            "tipo_registro": 'SAIDA',
            "timestamp": datetime.now().isoformat()
        }
        
        saida_response = supabase.table('t_atrasos_saidas').insert(registro_saida).execute()
        
        return jsonify({
            "message": "Saída antecipada registrada com sucesso!",
            "status": status_final
        }), 200

    except Exception as e:
        logging.error(f"Erro /api/salvar_saida_antecipada: {str(e)}")
        return jsonify({"error": f"Falha ao registrar saída: {str(e)}"}), 500

# =========================================================
# ROTAS DE RELATÓRIOS - CORRIGIDAS
# =========================================================

@frequencia_bp.route('/api/frequencia/relatorio', methods=['GET'])
def api_relatorio_frequencia():
    """Gera relatório mensal de frequência - CORRIGIDO"""
    try:
        sala_id = request.args.get('sala')
        mes = request.args.get('mes')
        ano = request.args.get('ano', datetime.now().year)

        if not sala_id or not mes:
            return jsonify({"error": "Parâmetros sala e mes são obrigatórios."}), 400

        supabase = get_supabase()
        
        # Busca alunos da sala
        alunos_response = supabase.table('d_alunos').select('id, nome, matricula').eq('sala_id', sala_id).order('nome').execute()
        alunos = alunos_response.data if alunos_response.data else []
        
        if not alunos:
            return jsonify([]), 200

        aluno_ids = [aluno['id'] for aluno in alunos]
        
        # Calcula período do mês
        mes_int = int(mes)
        ano_int = int(ano)
        _, num_dias = monthrange(ano_int, mes_int)
        
        data_inicio = f"{ano_int}-{mes_int:02d}-01"
        data_fim = f"{ano_int}-{mes_int:02d}-{num_dias:02d}"

        # Busca registros de frequência
        frequencia_response = supabase.table('t_frequencia').select('*').in_('aluno_id', aluno_ids).gte('data', data_inicio).lte('data', data_fim).execute()
        registros = frequencia_response.data if frequencia_response.data else []

        # Organiza dados por aluno
        frequencia_por_aluno = {}
        for registro in registros:
            aluno_id = registro['aluno_id']
            if aluno_id not in frequencia_por_aluno:
                frequencia_por_aluno[aluno_id] = {}
            frequencia_por_aluno[aluno_id][registro['data']] = registro['status']

        # Monta relatório final
        relatorio = []
        for aluno in alunos:
            relatorio.append({
                "id": aluno['id'],
                "nome": aluno['nome'],
                "matricula": aluno.get('matricula', ''),
                "frequencia": frequencia_por_aluno.get(aluno['id'], {})
            })

        return jsonify(relatorio), 200

    except Exception as e:
        logging.error(f"Erro /api/frequencia/relatorio: {str(e)}")
        return jsonify({"error": f"Falha ao gerar relatório: {str(e)}"}), 500
