from flask import Blueprint, request, jsonify
from datetime import datetime
from calendar import monthrange
import logging
from db_utils import get_supabase, handle_supabase_response

# Define o Blueprint para as rotas de Frequência
frequencia_bp = Blueprint('frequencia', __name__)

# =========================================================
# ROTAS DE REGISTRO DIÁRIO DE FREQUÊNCIA
# =========================================================

# ROTA: /api/frequencia/status (Verifica se a frequência já foi registrada para a sala/data)
@frequencia_bp.route('/api/frequencia/status', methods=['GET'])
def api_frequencia_status():
    sala_id = request.args.get('sala_id')
    data = request.args.get('data')

    if not sala_id or not data:
        return jsonify({"error": "Parâmetros sala_id e data são obrigatórios."}), 400

    try:
        supabase = get_supabase()
        if not supabase:
            return jsonify({"error": "Serviço de banco de dados indisponível"}), 503

        # Busca qualquer registro de frequência para a combinação sala/data
        resp = supabase.table('t_frequencia').select("id").eq('sala_id', int(sala_id)).eq('data', data).limit(1).execute()
        
        registrada = len(resp.data) > 0
        
        return jsonify({"registrada": registrada}), 200

    except Exception as e:
        logging.exception("Erro /api/frequencia/status")
        return jsonify({"error": str(e)}), 500

# ROTA: /api/salvar_frequencia (Salva o registro diário de Presença/Falta (P/F))
@frequencia_bp.route('/api/salvar_frequencia', methods=['POST'])
def api_salvar_frequencia():
    registros = request.json
    
    if not isinstance(registros, list) or not registros:
        return jsonify({"error": "O corpo da requisição deve ser uma lista não vazia de registros."}), 400
        
    try:
        supabase = get_supabase()
        if not supabase:
            return jsonify({"error": "Serviço de banco de dados indisponível"}), 503

        # Assume que todos os registros são para a mesma sala e data (baseado no frontend)
        primeiro_registro = registros[0]
        sala_id = primeiro_registro.get('sala_id')
        data = primeiro_registro.get('data')

        if not sala_id or not data:
             return jsonify({"error": "Dados de sala e data obrigatórios ausentes nos registros."}), 400

        # Verifica se já foi registrada (evita duplicidade)
        resp_status = supabase.table('t_frequencia').select("id").eq('sala_id', int(sala_id)).eq('data', data).limit(1).execute()
        if len(resp_status.data) > 0:
             return jsonify({"error": "Frequência para esta sala e data já foi registrada."}), 409

        # Prepara os dados para inserção
        dados_a_inserir = []
        for reg in registros:
            # Garante que apenas status P ou F sejam inseridos via esta rota
            if reg.get('status') in ['P', 'F']:
                 dados_a_inserir.append({
                    "aluno_id": int(reg.get('aluno_id')),
                    "sala_id": int(reg.get('sala_id')),
                    "data": reg.get('data'),
                    "status": reg.get('status'),
                    "timestamp_registro": datetime.now().isoformat()
                })
            
        if not dados_a_inserir:
            return jsonify({"error": "Nenhum registro de Presença/Falta (P/F) válido para salvar."}), 400

        response = supabase.table('t_frequencia').insert(dados_a_inserir).execute()
        handle_supabase_response(response)
        
        return jsonify({"message": f"Frequência de {len(dados_a_inserir)} alunos registrada com sucesso.", "status": 201}), 201

    except Exception as e:
        logging.exception("Erro /api/salvar_frequencia")
        return jsonify({"error": f"Falha ao salvar a frequência: {e}"}), 500

# =========================================================
# ROTAS DE REGISTRO DE EVENTOS (ATRASO/SAÍDA)
# =========================================================

# ROTA: /api/salvar_atraso (Salva o registro de entrada com Atraso - PA/PSA)
@frequencia_bp.route('/api/salvar_atraso', methods=['POST'])
def api_salvar_atraso():
    data = request.json
    
    aluno_id = data.get('aluno_id')
    sala_id = data.get('sala_id')
    data_dia = data.get('data')
    hora_atraso = data.get('hora_atraso')
    
    if not all([aluno_id, sala_id, data_dia, hora_atraso]):
        return jsonify({"error": "Dados obrigatórios de aluno, sala, data e hora de atraso ausentes."}), 400

    try:
        supabase = get_supabase()
        if not supabase:
            return jsonify({"error": "Serviço de banco de dados indisponível"}), 503

        aluno_id = int(aluno_id)
        sala_id = int(sala_id)
        
        # 1. ATUALIZA/CRIA REGISTRO NA t_frequencia (PA)
        resp_freq = supabase.table('t_frequencia').select("status").eq('aluno_id', aluno_id).eq('data', data_dia).limit(1).execute()
        
        status_atual = resp_freq.data[0]['status'] if resp_freq.data else None
        
        novo_status = 'PA' 
        if status_atual in ['PS', 'PSA']:
            # Se já tinha saída antecipada (PS), o novo status será PSA
            novo_status = 'PSA'

        # Lógica de atualização ou inserção na t_frequencia
        if status_atual:
            # Atualiza o status
            supabase.table('t_frequencia').update({'status': novo_status, 'timestamp_registro': datetime.now().isoformat()}).eq('aluno_id', aluno_id).eq('data', data_dia).execute()
        else:
            # Cria um novo registro
            supabase.table('t_frequencia').insert({
                "aluno_id": aluno_id,
                "sala_id": sala_id,
                "data": data_dia,
                "status": novo_status,
                "timestamp_registro": datetime.now().isoformat()
            }).execute()

        # 2. INSERE/ATUALIZA REGISTRO NA t_atrasos_saidas (Detalhes)
        registro_detalhe = {
            "aluno_id": aluno_id,
            "sala_id": sala_id,
            "data": data_dia,
            "hora_atraso": hora_atraso,
            "motivo": data.get('motivo_atraso'),
            "responsavel": data.get('responsavel_atraso'),
            "telefone": data.get('telefone_atraso'),
            "tipo_registro": 'ATRASO'
        }
        
        # Tenta buscar detalhe de atraso existente
        resp_detalhe = supabase.table('t_atrasos_saidas').select("*").eq('aluno_id', aluno_id).eq('data', data_dia).eq('tipo_registro', 'ATRASO').limit(1).execute()
        
        if resp_detalhe.data:
             # Se o detalhe já existe, atualiza (impede duplicação de detalhes)
             supabase.table('t_atrasos_saidas').update(registro_detalhe).eq('id', resp_detalhe.data[0]['id']).execute()
        else:
             supabase.table('t_atrasos_saidas').insert(registro_detalhe).execute()

        return jsonify({"message": f"Atraso registrado com sucesso. Status atualizado para {novo_status}.", "status": 200}), 200

    except Exception as e:
        logging.exception("Erro /api/salvar_atraso")
        return jsonify({"error": f"Falha ao salvar atraso: {e}"}), 500

# ROTA: /api/salvar_saida_antecipada (Salva o registro de Saída Antecipada - PS/PSA)
@frequencia_bp.route('/api/salvar_saida_antecipada', methods=['POST'])
def api_salvar_saida_antecipada():
    data = request.json
    
    aluno_id = data.get('aluno_id')
    sala_id = data.get('sala_id')
    data_dia = data.get('data')
    hora_saida = data.get('hora_saida')
    
    if not all([aluno_id, sala_id, data_dia, hora_saida]):
        return jsonify({"error": "Dados obrigatórios de aluno, sala, data e hora de saída ausentes."}), 400

    try:
        supabase = get_supabase()
        if not supabase:
            return jsonify({"error": "Serviço de banco de dados indisponível"}), 503

        aluno_id = int(aluno_id)
        sala_id = int(sala_id)
        
        # 1. ATUALIZA/CRIA REGISTRO NA t_frequencia (PS)
        resp_freq = supabase.table('t_frequencia').select("status").eq('aluno_id', aluno_id).eq('data', data_dia).limit(1).execute()
        
        status_atual = resp_freq.data[0]['status'] if resp_freq.data else None
        
        novo_status = 'PS'
        if status_atual in ['PA', 'PSA']:
            # Se já tinha atraso (PA), o novo status será PSA
            novo_status = 'PSA'

        # Lógica de atualização ou inserção na t_frequencia
        if status_atual:
            # Atualiza o status
            supabase.table('t_frequencia').update({'status': novo_status, 'timestamp_registro': datetime.now().isoformat()}).eq('aluno_id', aluno_id).eq('data', data_dia).execute()
        else:
            # Cria um novo registro
            supabase.table('t_frequencia').insert({
                "aluno_id": aluno_id,
                "sala_id": sala_id,
                "data": data_dia,
                "status": novo_status,
                "timestamp_registro": datetime.now().isoformat()
            }).execute()

        # 2. INSERE/ATUALIZA REGISTRO NA t_atrasos_saidas (Detalhes)
        registro_detalhe = {
            "aluno_id": aluno_id,
            "sala_id": sala_id,
            "data": data_dia,
            "hora_saida": hora_saida,
            "motivo": data.get('motivo_saida'),
            "responsavel": data.get('responsavel_saida'),
            "telefone": data.get('telefone_saida'),
            "tipo_registro": 'SAIDA'
        }
        
        # Tenta buscar detalhe de saída existente
        resp_detalhe = supabase.table('t_atrasos_saidas').select("*").eq('aluno_id', aluno_id).eq('data', data_dia).eq('tipo_registro', 'SAIDA').limit(1).execute()
        
        if resp_detalhe.data:
             # Se o detalhe já existe, atualiza (impede duplicação de detalhes)
             supabase.table('t_atrasos_saidas').update(registro_detalhe).eq('id', resp_detalhe.data[0]['id']).execute()
        else:
             supabase.table('t_atrasos_saidas').insert(registro_detalhe).execute()

        return jsonify({"message": f"Saída antecipada registrada com sucesso. Status atualizado para {novo_status}.", "status": 200}), 200

    except Exception as e:
        logging.exception("Erro /api/salvar_saida_antecipada")
        return jsonify({"error": f"Falha ao salvar saída antecipada: {e}"}), 500


# =========================================================
# ROTA DE RELATÓRIO MENSAL
# =========================================================

# ROTA: /api/frequencia?sala=<id>&mes=<mes> (Relatório mensal de frequência)
@frequencia_bp.route('/api/frequencia', methods=['GET'])
def api_relatorio_frequencia():
    sala_id = request.args.get('sala')
    mes = request.args.get('mes')

    if not sala_id or not mes:
        return jsonify({"error": "Parâmetros sala e mes são obrigatórios."}), 400

    try:
        supabase = get_supabase()
        if not supabase:
            return jsonify({"error": "Serviço de banco de dados indisponível"}), 503

        sala_id = int(sala_id)
        mes = int(mes)
        ano_atual = datetime.now().year
        
        # 1. Busca todos os alunos da sala
        resp_alunos = supabase.table('d_alunos').select("id, nome").eq('sala_id', sala_id).order('nome').execute()
        alunos_sala = handle_supabase_response(resp_alunos)
        
        aluno_ids = [a['id'] for a in alunos_sala]
        
        if not aluno_ids:
             return jsonify([]), 200
             
        # 2. Define o período de busca (apenas o mês selecionado)
        # Calcula o número de dias no mês
        _, num_dias = monthrange(ano_atual, mes)
        
        # Formato de data para a query do Supabase (YYYY-MM-DD)
        data_inicio = f"{ano_atual}-{str(mes).zfill(2)}-01"
        data_fim = f"{ano_atual}-{str(mes).zfill(2)}-{str(num_dias).zfill(2)}"

        # 3. Busca os registros de frequência para todos os alunos no mês
        resp_freq = supabase.table('t_frequencia').select("aluno_id, data, status").in_('aluno_id', aluno_ids).gte('data', data_inicio).lte('data', data_fim).execute()
        registros = handle_supabase_response(resp_freq)

        # 4. Processa e Agrupa os dados por aluno
        frequencia_por_aluno = {}
        for reg in registros:
            aluno_id = reg['aluno_id']
            # Mapeia a data para o status (YYYY-MM-DD: Status)
            if aluno_id not in frequencia_por_aluno:
                frequencia_por_aluno[aluno_id] = {}
            frequencia_por_aluno[aluno_id][reg['data']] = reg['status']
            
        # 5. Formata a saída para o frontend (Lista de objetos {nome: ..., frequencia: {...}})
        relatorio_final = []
        for aluno in alunos_sala:
            relatorio_final.append({
                "id": aluno['id'],
                "nome": aluno['nome'],
                "frequencia": frequencia_por_aluno.get(aluno['id'], {})
            })

        return jsonify(relatorio_final), 200

    except ValueError:
        return jsonify({"error": "Os parâmetros sala_id e mes devem ser números inteiros."}), 400
    except Exception as e:
        logging.exception("Erro /api/frequencia")
        return jsonify({"error": f"Falha ao gerar relatório de frequência: {e}"}), 500