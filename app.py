import os
import logging
from dotenv import load_dotenv
# IMPORTS CONSOLIDADOS (INCLUINDO PDF)
from flask import Flask, render_template, request, jsonify, send_file
from supabase import create_client, Client
import json
from datetime import datetime
from calendar import monthrange
import io
from fpdf import FPDF
import logging
from flask import jsonify, request

# =========================================================
# CONFIGURAÇÕES INICIAIS
# =========================================================

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
load_dotenv()

SUPABASE_URL: str = os.environ.get("SUPABASE_URL")
SUPABASE_KEY: str = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    # Aviso: Em ambiente de produção (Canvas), estas variáveis são injetadas.
    # Em desenvolvimento local sem .env, o erro abaixo será levantado.
    # Alterado para lançar ValueError, conforme o código original.
    raise ValueError("As variáveis SUPABASE_URL e SUPABASE_KEY devem ser configuradas no arquivo .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask(__name__, template_folder='templates')


# =========================================================
# LOG DE REQUISIÇÕES (para debug)
# =========================================================
@app.before_request
def log_request():
    print(f"[LOG] Rota acessada: {request.path}")

# =========================================================
# FUNÇÕES AUXILIARES
# =========================================================

def handle_supabase_response(response):
    if not response:
        return []
    if hasattr(response, "data"):
        return response.data or []
    if isinstance(response, dict) and "data" in response:
        return response.get("data") or []
    return []

def formatar_data_hora(data_str):
    if not data_str:
        return 'N/A'
    try:
        dt_obj = datetime.fromisoformat(data_str.replace('Z', '+00:00'))
        return dt_obj.strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        return data_str

def _to_bool(value):
    if value is True or value == 1:
        return True
    if value is False or value == 0 or value is None:
        return False
    s = str(value).strip().lower()
    if s in ('true', '1', 't', 'y', 'yes', 'sim'):
        return True
    if s in ('false', '0', 'f', 'n', 'no', 'nao', 'não'):
        return False
    # Tratamento para colunas TEXT no Supabase com "SIM" / "NÃO"
    if s in ('sim', 's'):
        return True
    return False

def calcular_dias_resposta(dt_abertura, dt_fechamento_str):
    """Calcula a diferença em dias entre a abertura e o fechamento da ocorrência."""
    if not dt_fechamento_str or not dt_abertura:
        return None
    try:
        dt_fechamento = datetime.fromisoformat(dt_fechamento_str.replace('Z', '+00:00'))
        dt_abertura = datetime.fromisoformat(dt_abertura.replace('Z', '+00:00'))
        
        diff = dt_fechamento - dt_abertura
        # Retorna o número de dias arredondado para cima (mínimo 1 dia se fechado no dia seguinte)
        return diff.days + (1 if diff.seconds > 0 else 0) 
    except Exception:
        return None

DEFAULT_AUTOTEXT = "ATENDIMENTO NÃO SOLICITADO PELO RESPONSÁVEL DA OCORRÊNCIA"

def safe_pdf_text(text):
    """Garante que o texto seja compatível com a codificação Latin-1/Cp1252 do FPDF."""
    if not text:
        return ''
    # Força a codificação para Latin-1 (comum em FPDF) e decodifica, 
    # substituindo caracteres incompatíveis para evitar o erro \ufffd.
    return str(text).encode('latin-1', 'replace').decode('latin-1')


# =========================================================
# ROTAS DE PÁGINA PRINCIPAIS (Renderiza templates)
# =========================================================

@app.route('/')
def home():
    return render_template('home.html')  

@app.route('/gestao_aulas')
def gestao_aulas():
    return render_template('gestao_aulas.html')

@app.route('/gestao_agenda')
def gestao_agenda():
    return render_template('gestao_agenda.html')

@app.route('/gestao_plano_aula')
def gestao_plano_aula():
    return render_template('gestao_plano_aula.html')

@app.route('/gestao_guia_aprendizagem')
def gestao_guia_aprendizagem():
    return render_template('gestao_guia_aprendizagem.html')

@app.route('/gestao_ocorrencia')
def gestao_ocorrencia():
    return render_template('gestao_ocorrencia.html')

@app.route('/gestao_ocorrencia_nova')
def gestao_ocorrencia_nova():
    return render_template('gestao_ocorrencia_nova.html')
    
@app.route("/gestao_ocorrencia_abertas")
def gestao_ocorrencia_abertas():
    return render_template("gestao_ocorrencia_abertas.html")

@app.route("/gestao_ocorrencia_editar")
def gestao_ocorrencia_editar():
    return render_template("gestao_ocorrencia_editar.html")

@app.route('/gestao_ocorrencia_finalizadas')
def gestao_ocorrencia_finalizadas():
    return render_template('gestao_ocorrencia_finalizadas.html')

@app.route('/gestao_relatorio_estatistico')
def gestao_relatorio_estatistico():
    return render_template('gestao_relatorio_estatistico.html')

@app.route('/gestao_relatorio_frequencia')
def gestao_relatorio_frequencia():
    return render_template('gestao_relatorio_frequencia.html')  

@app.route('/gestao_relatorio_impressao')
def gestao_relatorio_impressao():
    return render_template('gestao_relatorio_impressao.html')

@app.route('/gestao_relatorio_tutoria')
def gestao_relatorio_tutoria():
    return render_template('gestao_relatorio_tutoria.html')

@app.route('/gestao_frequencia')
def gestao_frequencia():
    return render_template('gestao_frequencia.html')

@app.route('/gestao_frequencia_registro')
def gestao_frequencia_registro():
    return render_template('gestao_frequencia_registro.html')

@app.route('/gestao_frequencia_atraso')
def gestao_frequencia_atraso():
    return render_template('gestao_frequencia_atraso.html')

@app.route('/gestao_frequencia_saida')
def gestao_frequencia_saida():
    return render_template('gestao_frequencia_saida.html')

@app.route('/gestao_tutoria')
def gestao_tutoria():
    return render_template('gestao_tutoria.html')

@app.route('/gestao_tutoria_agendamento')
def gestao_tutoria_agendamento():
    return render_template('gestao_tutoria_agendamento.html')

@app.route("/gestao_tutoria_ficha")
def ficha_tutoria():
    return render_template(
        "gestao_tutoria_ficha.html",
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_anon=os.getenv("SUPABASE_ANON_KEY")
    )

@app.route('/gestao_tutoria_registro')
def gestao_tutoria_registro():
    return render_template('gestao_tutoria_registro.html')

@app.route('/gestao_tutoria_notas')
def gestao_tutoria_notas():
    return render_template('gestao_tutoria_notas.html')

@app.route('/gestao_tecnologia')
def gestao_tecnologia():
    return render_template('gestao_tecnologia.html')

@app.route('/gestao_tecnologia_agendamento')
def gestao_tecnologia_agendamento():
    return render_template('gestao_tecnologia_agendamento.html')

@app.route('/gestao_tecnologia_ocorrencia')
def gestao_tecnologia_ocorrencia():
    return render_template('gestao_tecnologia_ocorrencia.html')

@app.route('/gestao_tecnologia_historico')
def gestao_tecnologia_historico():
    return render_template('gestao_tecnologia_historico.html')

@app.route('/gestao_tecnologia_retirada')
def gestao_tecnologia_retirada():
    return render_template('gestao_tecnologia_retirada.html')

@app.route('/gestao_cadastro')
def gestao_cadastro():
    return render_template('gestao_cadastro.html')

@app.route('/gestao_cadastro_salas')
def gestao_cadastro_salas():
    return render_template('gestao_cadastro_sala.html')

@app.route('/gestao_cadastro_tutores')
def gestao_cadastro_tutores():
    return render_template('gestao_cadastro_tutor.html')

@app.route('/gestao_cadastro_alunos')
def gestao_cadastro_alunos():
    return render_template('gestao_cadastro_aluno.html')

@app.route('/gestao_cadastro_disciplinas')
def gestao_cadastro_disciplinas():
    return render_template('gestao_cadastro_disciplinas.html')

@app.route('/gestao_cadastro_eletivas')
def gestao_cadastro_eletivas():
    return render_template('gestao_cadastro_eletiva.html')

@app.route('/gestao_cadastro_clubes')
def gestao_cadastro_clubes():
    return render_template('gestao_cadastro_clube.html')

@app.route('/gestao_cadastro_professores')
def gestao_cadastro_professores():
    return render_template('gestao_cadastro_professor_funcionario.html')

@app.route('/gestao_cadastro_equipamentos')
def gestao_cadastro_equipamentos():
    return render_template('gestao_cadastro_equipamento.html')

@app.route('/gestao_cadastro_vincular_tutor_aluno')
def gestao_cadastro_vincular_tutor_aluno():
    return render_template('gestao_cadastro_vinculacao_tutor_aluno.html')

@app.route('/gestao_cadastro_vincular_disciplina_sala')
def gestao_cadastro_vincular_disciplina_sala():
    return render_template('gestao_cadastro_vinculacao_disciplina_sala.html')


# =========================================================
# ROTAS DE API (DADOS) - CONSOLIDADAS
# =========================================================

# --- ROTAS DE TUTORIA (CORRIGIDAS/SOLICITADAS) ---

@app.route("/api/tutores")
def api_tutores():
    """Busca tutores (d_tutores)."""
    resp = supabase.table("d_tutores").select("id,nome").execute()
    if resp.error:
        return jsonify({"error": resp.error.message}), 500
    return jsonify(resp.data)

@app.route("/api/alunos")
def api_alunos():
    """Busca alunos filtrando por tutor_id (d_alunos)."""
    tutor_id = request.args.get("tutor_id")
    if not tutor_id:
        return jsonify({"error": "tutor_id é obrigatório"}), 400

    resp = supabase.table("d_alunos").select("id,nome").eq("tutor_id", tutor_id).execute()
    if resp.error:
        return jsonify({"error": resp.error.message}), 500
    return jsonify(resp.data)

@app.route("/api/agendamentos")
def api_agendamentos():
    """Busca agendamentos/histórico por aluno_id (f_frequencia)."""
    aluno_id = request.args.get("aluno_id")
    if not aluno_id:
        return jsonify({"error": "aluno_id é obrigatório"}), 400

    resp = supabase.table("f_frequencia").select("*").eq("aluno_id", aluno_id).order("data_registro", {"ascending": True}).execute()
    if resp.error:
        return jsonify({"error": resp.error.message}), 500
    return jsonify(resp.data)


@app.route("/api/agendamentos/novo", methods=["POST"])
def api_agendamento_novo():
    """Cria um novo agendamento de tutoria (f_frequencia)."""
    data = request.json
    required_fields = ["aluno_id", "tutor_id", "tipo_atendimento", "descricao_atendimento"]
    for f in required_fields:
        if f not in data:
            return jsonify({"error": f"{f} é obrigatório"}), 400

    record = {
        "aluno_id": data["aluno_id"],
        "tutor_id": data["tutor_id"],
        "tipo_atendimento": data["tipo_atendimento"],
        "descricao_atendimento": data["descricao_atendimento"],
        "status_agendamento": "pendente",
        "data_registro": data.get("data_registro", datetime.now().isoformat())
    }

    resp = supabase.table("f_frequencia").insert(record).execute()
    if resp.error:
        return jsonify({"error": resp.error.message}), 500
    return jsonify(resp.data)

# --- ROTAS DE FREQUÊNCIA (CORRIGIDAS/SOLICITADAS) ---

@app.route("/api/detalhe_frequencia")
def api_detalhe_frequencia():
    """Busca detalhe de frequência por aluno e data (f_frequencia)."""
    aluno_id = request.args.get("aluno_id")
    data = request.args.get("data")
    sala_id = request.args.get("sala_id") 
    mes = request.args.get("mes") 

    if not all([aluno_id, data, sala_id, mes]):
        return jsonify({"erro": "Parâmetros obrigatórios ausentes"}), 400

    try:
        # Consulta detalhada da frequência (usando data_registro como filtro de data)
        resp = supabase.table("f_frequencia").select("*").eq("aluno_id", aluno_id).eq("data_registro", data).execute()
        
        if resp.error:
            return jsonify({"erro": resp.error.message}), 500

        if not resp.data:
            return jsonify({"erro": "Registro não encontrado"}), 404

        registro = resp.data[0]

        # Inclui nome do aluno
        aluno_resp = supabase.table("d_alunos").select("nome").eq("id", aluno_id).execute()
        registro["nome"] = aluno_resp.data[0]["nome"] if aluno_resp.data else "Desconhecido"

        return jsonify(registro)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

# --- Rotas de Atendimento e Cadastro (Preservadas) ---

@app.route('/api/funcionarios', methods=['GET'])
def api_get_funcionarios():
    try:
        response = supabase.table('d_funcionarios').select('id, nome, funcao, is_tutor, email').order('nome').execute()
        funcionarios = [{"id": str(f['id']), "nome": f['nome'], "funcao": f.get('funcao', ''), "is_tutor": f.get('is_tutor', False), "email": f.get('email', '')} for f in handle_supabase_response(response)]
        return jsonify(funcionarios)
    except Exception as e:
        return jsonify({"error": f"Erro ao buscar funcionários: {e}", "status": 500}), 500

@app.route("/api/registrar_atendimento/<int:ocorrencia_id>", methods=["POST"])
def registrar_atendimento(ocorrencia_id):
    """Rota para registrar atendimento de ocorrência (Tutor/Coordenação/Gestão)."""
    try:
        data = request.get_json()
        if data is None:
            return jsonify({"error": "Corpo da requisição vazio ou JSON inválido."}), 400

        nivel = data.get("nivel")
        texto = data.get("texto") # Esperado pelo frontend corrigido
        
        if not nivel or not texto:
            return jsonify({"error": "Dados incompletos: Nível ou texto ausente."}), 400

        campos = {
            "professor": ("atendimento_professor", "dt_atendimento_professor"),
            "tutor": ("atendimento_tutor", "dt_atendimento_tutor"),
            "coordenacao": ("atendimento_coordenacao", "dt_atendimento_coordenacao"),
            "gestao": ("atendimento_gestao", "dt_atendimento_gestao"),
        }

        if nivel not in campos:
            return jsonify({"error": f"Nível de atendimento inválido: {nivel}"}), 400

        campo_texto, campo_data = campos[nivel]
        
        agora = datetime.utcnow().isoformat(timespec='milliseconds') + "Z"

        # 1. ATUALIZA OS CAMPOS DE ATENDIMENTO E DATA
        update_data = {
            campo_texto: texto,
            campo_data: agora
        }
        
        update_result = supabase.table("ocorrencias").update(update_data).eq("numero", ocorrencia_id).execute()

        # 2. REAVALIA O STATUS (Busca os dados *após* a atualização)
        resp = supabase.table('ocorrencias').select(
            "solicitado_tutor, solicitado_coordenacao, solicitado_gestao, "
            "atendimento_tutor, atendimento_coordenacao, atendimento_gestao, status"
        ).eq("numero", ocorrencia_id).single().execute()

        if not resp.data:
            return jsonify({"error": "Ocorrência não encontrada"}), 404

        occ = resp.data
        
        st = _to_bool(occ.get('solicitado_tutor'))
        sc = _to_bool(occ.get('solicitado_coordenacao'))
        sg = _to_bool(occ.get('solicitado_gestao'))

        at_tutor = (occ.get('atendimento_tutor') or "").strip()
        at_coord = (occ.get('atendimento_coordenacao') or "").strip()
        at_gest = (occ.get('atendimento_gestao') or "").strip()

        # Verifica pendência, desconsiderando DEFAULT_AUTOTEXT como "atendido"
        pendente_tutor = st and (at_tutor == "" or at_tutor == DEFAULT_AUTOTEXT)
        pendente_coord = sc and (at_coord == "" or at_coord == DEFAULT_AUTOTEXT)
        pendente_gestao = sg and (at_gest == "" or at_gest == DEFAULT_AUTOTEXT)

        novo_status = "Aberta"
        
        if not (pendente_tutor or pendente_coord or pendente_gestao):
            novo_status = "Finalizada"

        if novo_status == "Finalizada" and occ.get('status') != "Finalizada":
            supabase.table("ocorrencias").update({"status": novo_status}).eq("numero", ocorrencia_id).execute()
        
        return jsonify({"success": True, "novo_status": novo_status}), 200

    except Exception as e:
        logging.exception(f"Erro ao registrar atendimento {ocorrencia_id}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/ocorrencia_detalhes')
def ocorrencia_detalhes():
    numero = request.args.get('numero')
    if not numero:
        return jsonify({'error': 'Número da ocorrência não fornecido'}), 400

    try:
        # Função segura para converter valores em booleanos
        def _to_bool(value):
            if value in [True, 'true', 'True', 1, '1', 'SIM', 'Sim', 'sim']:
                return True
            return False

        # Consulta ao Supabase
        select_query_detail = (
            "numero, data_hora, descricao, atendimento_professor, "
            "atendimento_tutor, atendimento_coordenacao, atendimento_gestao, "
            "dt_atendimento_tutor, dt_atendimento_coordenacao, dt_atendimento_gestao, "
            "aluno_nome, tutor_nome, professor_id(nome), sala_id(sala), "
            "status, solicitado_tutor, solicitado_coordenacao, solicitado_gestao"
        )

        resp = supabase.table('ocorrencias').select(select_query_detail).eq('numero', numero).single().execute()

        occ = resp.data
        if occ is None:
            return jsonify({'error': 'Ocorrência não encontrada'}), 404

        professor_nome = occ.get('professor_id', {}).get('nome', 'N/A')
        sala_nome = occ.get('sala_id', {}).get('sala', 'N/A')

        # Sempre retorna JSON, mesmo em erros
        return jsonify({
            'numero': occ.get('numero'),
            'aluno_nome': occ.get('aluno_nome'),
            'sala_nome': sala_nome,
            'tutor_nome': occ.get('tutor_nome'),
            'professor_nome': professor_nome,
            'status': occ.get('status'),
            'descricao': occ.get('descricao'),
            'atendimento_professor': occ.get('atendimento_professor'),
            'atendimento_tutor': occ.get('atendimento_tutor'),
            'atendimento_coordenacao': occ.get('atendimento_coordenacao'),
            'atendimento_gestao': occ.get('atendimento_gestao'),
            'solicitado_tutor': _to_bool(occ.get('solicitado_tutor')),
            'solicitado_coordenacao': _to_bool(occ.get('solicitado_coordenacao')),
            'solicitado_gestao': _to_bool(occ.get('solicitado_gestao')),
        }), 200

    except Exception as e:
        logging.exception(f"Erro ao consultar Supabase para detalhes da ocorrência {numero}")
        return jsonify({'error': f'Erro ao consultar Supabase: {str(e)}'}), 500
@app.route('/api/ocorrencias_finalizadas', methods=['GET'])
def api_ocorrencias_finalizadas():
    try:
        sala = request.args.get('sala')
        aluno_nome_filtro = request.args.get('aluno') # Filtro de aluno é feito por nome/string

        q = supabase.table('ocorrencias').select(
            "numero, data_hora, status, aluno_nome, tutor_nome, solicitado_tutor, solicitado_coordenacao, solicitado_gestao, atendimento_tutor, atendimento_coordenacao, atendimento_gestao, professor_id(nome), sala_id(sala), aluno_id"
        ).order('data_hora', desc=True)
        
        # Filtro por sala (ID)
        if sala:
            try:
                q = q.eq('sala_id', int(sala))
            except ValueError:
                logging.warning(f"Filtro de sala inválido: {sala}")
        
        resp = q.execute()
        items = resp.data or []
        finalizadas = []

        for item in items:
            # Lógica de atualização de status (mantida)
            st = _to_bool(item.get('solicitado_tutor'))
            sc = _to_bool(item.get('solicitado_coordenacao'))
            sg = _to_bool(item.get('solicitado_gestao'))
            at_tutor = (item.get('atendimento_tutor') or "").strip()
            at_coord = (item.get('atendimento_coordenacao') or "").strip()
            at_gest = (item.get('atendimento_gestao') or "").strip()
            pendente_tutor = st and (at_tutor == "" or at_tutor == DEFAULT_AUTOTEXT)
            pendente_coord = sc and (at_coord == "" or at_coord == DEFAULT_AUTOTEXT)
            pendente_gestao = sg and (at_gest == "" or at_gest == DEFAULT_AUTOTEXT)
            novo_status = "Aberta" if (pendente_tutor or pendente_coord or pendente_gestao) else "Finalizada"

            if item.get('status') != novo_status:
                # Lógica de atualização de status
                supabase.table('ocorrencias').update({'status': novo_status}).eq('numero', item.get('numero')).execute()

            if novo_status == "Finalizada":
                professor_nome = (item.get('professor_id') or {}).get('nome', 'N/A')
                sala_nome = (item.get('sala_id') or {}).get('sala', 'N/A')

                finalizadas.append({
                    "numero": item.get('numero'),
                    "data_hora": formatar_data_hora(item.get('data_hora')),
                    "aluno_nome": item.get('aluno_nome', 'N/A'),
                    "tutor_nome": item.get('tutor_nome', 'N/A'),
                    "professor_nome": professor_nome,
                    "sala_nome": sala_nome,
                    "status": novo_status,
                    "solicitado_tutor": st,
                    "solicitado_coordenacao": sc,
                    "solicitado_gestao": sg,
                    "atendimento_tutor": at_tutor,
                    "atendimento_coordenacao": at_coord,
                    "atendimento_gestao": at_gest,
                    "aluno_id": item.get('aluno_id'), # Adicionando o ID para filtro no JS
                })

        # Filtragem por aluno_nome (se fornecido)
        # O filtro de aluno é mais efetivo se for feito no JS pelo ID do aluno selecionado
        # Vou manter a lógica de filtro por nome aqui, mas o frontend usará o ID para o filtro.
        if aluno_nome_filtro:
             finalizadas = [f for f in finalizadas if aluno_nome_filtro.lower() in f['aluno_nome'].lower()]


        return jsonify(finalizadas), 200

    except Exception as e:
        logging.exception("Erro /api/ocorrencias_finalizadas")
        return jsonify({"error": str(e)}), 500

@app.route('/api/registrar_ocorrencia', methods=['POST'])
def api_registrar_ocorrencia():
    data = request.json
    try:
        prof_id_bigint = int(data.get('prof_id')) if data.get('prof_id') and str(data.get('prof_id')).isdigit() else None
        aluno_id_bigint = int(data.get('aluno_id')) if data.get('aluno_id') and str(data.get('aluno_id')).isdigit() else None
        sala_id_bigint = int(data.get('sala_id')) if data.get('sala_id') and str(data.get('sala_id')).isdigit() else None
    except ValueError:
        prof_id_bigint, aluno_id_bigint, sala_id_bigint = None, None, None
        
    descricao = data.get('descricao')
    atendimento_professor = data.get('atendimento_professor')
    
    if not all([prof_id_bigint, aluno_id_bigint, sala_id_bigint, descricao, atendimento_professor]):
        return jsonify({"error": "Dados obrigatórios (Professor, Aluno, Sala, Descrição e Atendimento Professor) são necessários. Verifique se os IDs de Professor, Aluno e Sala são válidos.", "status": 400}), 400
    
    try:
        tutor_id_resp = supabase.table('d_alunos').select('tutor_id').eq('id', aluno_id_bigint).single().execute()
        tutor_id = tutor_id_resp.data.get('tutor_id') if tutor_id_resp.data else None
        
        tutor_nome = 'Tutor Não Encontrado'
        if tutor_id:
            tutor_nome_resp = supabase.table('d_funcionarios').select('nome').eq('id', tutor_id).single().execute()
            tutor_nome = tutor_nome_resp.data.get('nome') if tutor_nome_resp and tutor_nome_resp.data else 'Tutor Não Encontrado'
        
        nova_ocorrencia = {
            "professor_id": prof_id_bigint,
            "aluno_id": aluno_id_bigint,
            "sala_id": sala_id_bigint,
            "data_hora": datetime.now().isoformat(),
            "descricao": descricao,
            "atendimento_professor": atendimento_professor,
            "aluno_nome": data.get('aluno_nome'),
            "tutor_nome": tutor_nome,
            "tutor_id": tutor_id,
            "tipo": data.get('tipo', 'Comportamental'),
            "status": "Aberta",
            "solicitado_tutor": 'SIM' if _to_bool(data.get('solicitar_tutor')) else 'NÃO',
            "solicitado_coordenacao": 'SIM' if _to_bool(data.get('solicitar_coordenacao')) else 'NÃO',
            "solicitado_gestao": 'SIM' if _to_bool(data.get('solicitar_gestao')) else 'NÃO',
        }
        
        response = supabase.table('ocorrencias').insert(nova_ocorrencia).execute()
        handle_supabase_response(response)
        
        logging.info(f"Ocorrência registrada para Aluno ID {aluno_id_bigint}")
        
        return jsonify({"message": "Ocorrência registrada com sucesso! Aguardando atendimento.", "status": 201}), 201
    
    except Exception as e:
        logging.exception(f"Erro no Supabase ao registrar ocorrência: {e}")
        return jsonify({"error": f"Falha ao registrar ocorrência: {e}", "status": 500}), 500

@app.route('/api/ocorrencias_abertas', methods=['GET'])
def api_ocorrencias_abertas():
    try:
        # Consulta principal, buscando todos os campos necessários
        resp = supabase.table('ocorrencias').select(
            "numero, data_hora, status, aluno_nome, tutor_nome, solicitado_tutor, solicitado_coordenacao, solicitado_gestao, atendimento_tutor, atendimento_coordenacao, atendimento_gestao, professor_id(nome), sala_id(sala)"
        ).order('data_hora', desc=True).execute()

        items = resp.data or []
        abertas = []

        for item in items:
            numero = item.get('numero')
            update_fields = {}

            st = _to_bool(item.get('solicitado_tutor'))
            sc = _to_bool(item.get('solicitado_coordenacao'))
            sg = _to_bool(item.get('solicitado_gestao'))

            at_tutor = (item.get('atendimento_tutor') or "").strip()
            at_coord = (item.get('atendimento_coordenacao') or "").strip()
            at_gest = (item.get('atendimento_gestao') or "").strip()

            # Preenche atendimento automático quando não solicitado
            if not st and at_tutor == "":
                at_tutor = DEFAULT_AUTOTEXT
                update_fields['atendimento_tutor'] = at_tutor
            if not sc and at_coord == "":
                at_coord = DEFAULT_AUTOTEXT
                update_fields['atendimento_coordenacao'] = at_coord
            if not sg and at_gest == "":
                at_gest = DEFAULT_AUTOTEXT
                update_fields['atendimento_gestao'] = at_gest

            pendente_tutor = st and (at_tutor == "" or at_tutor == DEFAULT_AUTOTEXT)
            pendente_coord = sc and (at_coord == "" or at_coord == DEFAULT_AUTOTEXT)
            pendente_gestao = sg and (at_gest == "" or at_gest == DEFAULT_AUTOTEXT)

            # Cálculo de status 
            novo_status = "Aberta" if (pendente_tutor or pendente_coord or pendente_gestao) else "Finalizada"

            # Atualiza status automaticamente no Supabase se necessário
            if item.get('status') != novo_status:
                update_fields['status'] = novo_status
                try:
                    supabase.table('ocorrencias').update(update_fields).eq('numero', numero).execute()
                    logging.info(f"[OCORRÊNCIA] Nº {numero} atualizada → {novo_status}")
                except Exception as e:
                    logging.error(f"Falha ao atualizar ocorrência {numero}: {e}")

            if novo_status == "Aberta":
                # Extração segura dos nomes referenciados
                professor_nome = (item.get('professor_id') or {}).get('nome', 'N/A')
                sala_nome = (item.get('sala_id') or {}).get('sala', 'N/A')
                
                abertas.append({
                    "numero": numero,
                    "data_hora": formatar_data_hora(item.get('data_hora')),
                    "aluno_nome": item.get('aluno_nome', 'N/A'),
                    "tutor_nome": item.get('tutor_nome', 'N/A'),
                    "professor_nome": professor_nome,
                    "sala_nome": sala_nome,
                    "status": novo_status,
                    "solicitado_tutor": st,
                    "solicitado_coordenacao": sc,
                    "solicitado_gestao": sg,
                    "atendimento_tutor": at_tutor,
                    "atendimento_coordenacao": at_coord,
                    "atendimento_gestao": at_gest
                })

        return jsonify(abertas), 200

    except Exception as e:
        logging.exception("Erro /api/ocorrencias_abertas")
        return jsonify({"error": str(e)}), 500


@app.route('/api/ocorrencias_todas')
def api_ocorrencias_todas():
    try:
        response = supabase.table('ocorrencias').select('*').order('data_hora', desc=True).execute()
        return jsonify(handle_supabase_response(response))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/salas_com_ocorrencias')
def get_salas_com_ocorrencias():
    try:
        # Busca todas as salas que aparecem em alguma ocorrência
        ocorrencias = supabase.table('ocorrencias').select('sala_id').execute()
        sala_ids = list({o['sala_id'] for o in ocorrencias.data if o.get('sala_id')})
        
        # Busca detalhes das salas
        salas = supabase.table('d_salas').select('id, sala').in_('id', sala_ids).execute()
        
        # O frontend espera: [{"id": 1, "sala": "Nome Sala"}, ...]
        salas_formatadas = [{"id": s['id'], "sala": s['sala']} for s in handle_supabase_response(salas)]
        
        return jsonify(salas_formatadas)
    except Exception as e:
        logging.exception("Erro ao buscar salas com ocorrências")
        return jsonify({"error": str(e)}), 500

@app.route('/api/alunos_com_ocorrencias_por_sala/<int:sala_id>')
def get_alunos_com_ocorrencias_por_sala(sala_id):
    try:
        # Busca todos os alunos que aparecem em ocorrências daquela sala
        ocorrencias = supabase.table('ocorrencias').select('aluno_id').eq('sala_id', sala_id).execute()
        aluno_ids = list({o['aluno_id'] for o in ocorrencias.data if o.get('aluno_id')})
        
        # Busca detalhes dos alunos
        alunos = supabase.table('d_alunos').select('id, nome').in_('id', aluno_ids).execute()
        
        # O frontend espera: [{"id": 1, "nome": "Nome Aluno"}, ...]
        alunos_formatados = [{"id": a['id'], "nome": a['nome']} for a in handle_supabase_response(alunos)]
        
        return jsonify(alunos_formatados)
    except Exception as e:
        logging.exception(f"Erro ao buscar alunos com ocorrências na sala {sala_id}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/relatorio_ocorrencias')
def get_relatorio_ocorrencias():
    try:
        sala_id = request.args.get('salaId')
        aluno_id = request.args.get('alunoId')
        data_inicial = request.args.get('dataInicial')
        data_final = request.args.get('dataFinal')
        query = supabase.table('ocorrencias').select('*, aluno_id(nome)').order('data_hora')
        if sala_id:
            query = query.eq('sala_id', int(sala_id))
        if aluno_id:
            query = query.eq('aluno_id', int(aluno_id))
        if data_inicial:
            query = query.gte('data_hora', data_inicial)
        if data_final:
            query = query.lte('data_hora', data_final)
        resp = query.execute()
        return jsonify(handle_supabase_response(resp))
    except Exception as e:
        logging.exception("Erro ao gerar relatório de ocorrências")
        return jsonify({"error": f"Erro ao gerar relatório de ocorrências: {e}"}), 500

@app.route('/api/ocorrencias', methods=['GET'])
@app.route('/api/ocorrencias/<ocorrencia_id>', methods=['GET'])
def api_get_ocorrencias(ocorrencia_id=None):
    try:
        select_query_detail = "numero, data_hora, descricao, atendimento_professor, atendimento_tutor, atendimento_coordenacao, atendimento_gestao, dt_atendimento_tutor, dt_atendimento_coordenacao, dt_atendimento_gestao, aluno_nome, tutor_nome, professor_id(nome), sala_id(sala)"
        if ocorrencia_id:
            response = supabase.table('ocorrencias').select(select_query_detail).eq('numero', int(ocorrencia_id)).single().execute()
            data = handle_supabase_response(response)
            if data and isinstance(data, dict):
                data['id'] = data.get('numero')
                data['professor_nome'] = data.get('professor_id', {}).get('nome', 'N/A')
                data['sala_nome'] = data.get('sala_id', {}).get('sala', 'N/A')
                if 'professor_id' in data:
                    del data['professor_id']
                if 'sala_id' in data:
                    del data['sala_id']
            return jsonify(data), 200
        else:
            response = supabase.table('ocorrencias').select('*').order('data_hora', desc=True).execute()
            return jsonify(handle_supabase_response(response)), 200
    except Exception as e:
        logging.error(f"Erro ao buscar ocorrência de detalhe: {e}")
        return jsonify({"error": f"Falha ao buscar detalhes: {e}", "status": 500}), 500

@app.route('/api/vinculacoes_disciplinas/<sala_id>', methods=['GET'])
def api_get_vinculacoes_disciplinas(sala_id):
    try:
        sala_id_bigint = int(sala_id)
        response = supabase.table('vinculos_disciplina_sala').select('disciplina_id').eq('sala_id', sala_id_bigint).execute()
        vinculos_raw = handle_supabase_response(response)
        disciplinas_ids = [v['disciplina_id'] for v in vinculos_raw]
        return jsonify({"sala_id": sala_id, "disciplinas": disciplinas_ids})
    except Exception as e:
        return jsonify({"error": f"Erro ao buscar vínculos de disciplinas: {e}", "status": 500}), 500

@app.route('/api/horarios_fixos/<nivel_ensino>', methods=['GET'])
def api_get_horarios_fixos(nivel_ensino):
    try:
        response = supabase.table('d_horarios_fixos').select('*').eq('nivel_ensino', nivel_ensino).order('dia_semana').execute()
        horarios = handle_supabase_response(response)
        return jsonify(horarios)
    except Exception as e:
        return jsonify({"error": f"Erro ao buscar horários fixos: {e}", "status": 500}), 500

@app.route('/api/agenda_semanal', methods=['GET'])
def api_get_agenda_semanal():
    sala_id = request.args.get('sala_id')
    data_referencia = request.args.get('data_referencia')
    if not sala_id or not data_referencia:
        return jsonify({"error": "Parâmetros sala_id e data_referencia são obrigatórios.", "status": 400}), 400
    try:
        response = supabase.table('f_agenda_aulas').select('id, dia_semana, ordem_aula, tema_aula, tipo_aula, disciplina_id, professor_id').eq('sala_id', int(sala_id)).eq('data_referencia', data_referencia).execute()
        agenda_raw = handle_supabase_response(response)
        agenda = []
        for item in agenda_raw:
            disc_nome = None
            prof_nome = None
            if item.get('disciplina_id'):
                dresp = supabase.table('d_disciplinas').select('nome').eq('id', item['disciplina_id']).single().execute()
                ddata = handle_supabase_response(dresp)
                disc_nome = ddata.get('nome') if isinstance(ddata, dict) else None
            if item.get('professor_id'):
                presp = supabase.table('d_funcionarios').select('nome').eq('id', item['professor_id']).single().execute()
                pdata = handle_supabase_response(presp)
                prof_nome = pdata.get('nome') if isinstance(pdata, dict) else None
            agenda.append({
                "id": str(item.get('id')),
                "dia_semana": item.get('dia_semana'),
                "ordem_aula": item.get('ordem_aula'),
                "tema_aula": item.get('tema_aula'),
                "tipo_aula": item.get('tipo_aula'),
                "disciplina_nome": disc_nome,
                "professor_nome": prof_nome
            })
        return jsonify(agenda)
    except Exception as e:
        return jsonify({"error": f"Erro ao buscar agenda semanal: {e}", "status": 500}), 500

@app.route('/api/guia_aprendizagem', methods=['GET'])
def api_get_guia_aprendizagem():
    disciplina_id = request.args.get('disciplina_id')
    bimestre = request.args.get('bimestre')
    serie = request.args.get('serie')
    if not disciplina_id or not bimestre or not serie:
        return jsonify({"error": "Parâmetros disciplina, bimestre e série são obrigatórios.", "status": 400}), 400
    try:
        response = supabase.table('f_guia_aprendizagem').select('*').eq('disciplina_id', disciplina_id).eq('bimestre', int(bimestre)).eq('serie', serie).execute()
        guia = handle_supabase_response(response)
        if guia and isinstance(guia, list) and guia[0].get('habilidades_planejadas'):
            try:
                guia[0]['habilidades_planejadas'] = json.dumps(guia[0]['habilidades_planejadas'])
            except:
                pass 
        return jsonify(guia)
    except Exception as e:
        return jsonify({"error": f"Erro ao buscar Guia de Aprendizagem: {e}", "status": 500}), 500


@app.route('/api/salvar_agenda', methods=['POST'])
def api_salvar_agenda():
    data = request.json
    registros = data.get('registros')
    if not registros or not isinstance(registros, list):
        return jsonify({"error": "Nenhum registro de agenda válido enviado.", "status": 400}), 400
    try:
        registros_a_salvar = []
        for item in registros:
            disciplina_id = item['disciplina_id']
            registros_a_salvar.append({
                "sala_id": int(item['sala_id']),
                "professor_id": int(item['professor_id']),
                "data_referencia": item['data_referencia'],
                "dia_semana": item['dia_semana'],
                "ordem_aula": int(item['ordem_aula']),
                "disciplina_id": disciplina_id,
                "tema_aula": item['tema_aula'],
                "tipo_aula": item['tipo_aula'],
            })
        response = supabase.table('f_agenda_aulas').upsert(registros_a_salvar, on_conflict='sala_id, data_referencia, dia_semana, ordem_aula').execute()
        handle_supabase_response(response)
        return jsonify({"message": f"{len(registros_a_salvar)} registros de agenda salvos/atualizados com sucesso!", "status": 200}), 200
    except Exception as e:
        logging.error(f"Erro ao salvar agenda: {e}")
        return jsonify({"error": f"Falha ao salvar agenda: {e}", "status": 500}), 500


@app.route('/api/salvar_frequencia', methods=['POST'])
def api_salvar_frequencia_massa():
    """Salva a frequência P/F em massa, utilizando UPSERT para evitar duplicatas."""
    data_list = request.json
    if not data_list or not isinstance(data_list, list):
        return jsonify({"error": "Dados inválidos: Esperado uma lista de registros."}, 400)
        
    registros_a_salvar = []
    
    for item in data_list:
        try:
            aluno_id_bigint = int(item['aluno_id'])
            sala_id_bigint = int(item['sala_id'])
            data = item['data']
            status = item['status']
            
            # Garante que só P e F podem ser inseridos aqui, para não sobrescrever PA/PS/PAS
            if status not in ['P', 'F']:
                logging.warning(f"Status inválido {status} na frequência em massa. Ignorando.")
                continue

            registro = {
                "aluno_id": aluno_id_bigint,
                "sala_id": sala_id_bigint,
                "data": data,
                "status": status,
                # Chaves de conflito para UPSERT:
                "data": data, 
                "aluno_id": aluno_id_bigint
            }
            registros_a_salvar.append(registro)
        except (ValueError, KeyError, TypeError):
            continue
            
    if not registros_a_salvar:
        return jsonify({"error": "Nenhum registro válido foi encontrado para salvar."}, 400)
        
    try:
        # Usa UPSERT (on_conflict na PK) para atualizar se já existir ou inserir se for novo.
        response = supabase.table("f_frequencia").upsert(payload, on_conflict=["aluno_id", "data"]).execute()
        handle_supabase_response(response)
        return jsonify({"message": f"{len(registros_a_salvar)} registros de frequência salvos/atualizados com sucesso!", "status": 201}), 201
    except Exception as e:
        logging.error(f"Erro no Supabase ao salvar frequência em massa: {e}")
        return jsonify({"error": f"Erro interno do servidor: {e}", "status": 500}), 500

@app.route('/api/salvar_atraso', methods=['POST'])
def salvar_atraso():
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({"error": "Nenhum dado recebido"}), 400

        payload = {
            "aluno_id": aluno_id,
            "sala_id": sala_id,
            "data": registro_data,
            "hora_atraso": data['hora'],
            "motivo_atraso": data['motivo'],
            "responsavel_atraso": data.get('responsavel'),
            "telefone_atraso": data.get('telefone'),
            "status": novo_status
        }

        response = supabase.table("f_frequencia").upsert(payload).execute()

        if not response or not getattr(response, "data", None):
            return jsonify({"error": "Falha ao salvar no Supabase"}), 500

        return jsonify({"message": "Entrada Atrasada salva com sucesso."}), 200

    except Exception as e:
        print(f"[ERROR] Erro no Supabase ao salvar saída antecipada: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/salvar_saida_antecipada', methods=['POST'])
def salvar_saida_antecipada():
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({"error": "Nenhum dado recebido"}), 400

        payload = {
            "aluno_id": dados.get("aluno_id"),
            "sala_id": dados.get("sala_id"),
            "data": dados.get("data"),
            "hora_saida": dados.get("hora"),
            "motivo_saida": dados.get("motivo"),
            "responsavel_saida": dados.get("responsavel"),
            "telefone_saida": dados.get("telefone"),
            "status": "PSA"  # saída antecipada
        }

        response = supabase.table("f_frequencia").upsert(payload).execute()

        if not response or not getattr(response, "data", None):
            return jsonify({"error": "Falha ao salvar no Supabase"}), 500

        return jsonify({"message": "Saída antecipada salva com sucesso."}), 200

    except Exception as e:
        print(f"[ERROR] Erro no Supabase ao salvar saída antecipada: {e}")
        return jsonify({"error": str(e)}), 500
        
@app.route('/api/relatorio_frequencia_detalhada', methods=['GET'])
def api_relatorio_frequencia_detalhada():
    """Gera o relatório de frequência detalhada por sala e mês/ano."""
    try:
        sala_id = request.args.get('sala_id')
        mes_ano_str = request.args.get('mes_ano') # Formato 'YYYY-MM'

        if not sala_id or not mes_ano_str:
            return jsonify({"error": "Filtros Sala e Mês/Ano são obrigatórios."}), 400

        ano, mes = map(int, mes_ano_str.split('-'))
        dias_no_mes = monthrange(ano, mes)[1]
        data_inicio = f"{ano}-{mes:02d}-01"
        data_fim = f"{ano}-{mes:02d}-{dias_no_mes:02d}"
        
        sala_id_int = int(sala_id)

        # 1. Busca todos os alunos da sala
        resp_alunos = supabase.table('d_alunos').select('id, nome').eq('sala_id', sala_id_int).order('nome').execute()
        alunos = handle_supabase_response(resp_alunos)
        
        aluno_ids = [a['id'] for a in alunos]
        
        if not aluno_ids:
            return jsonify({"error": "Nenhum aluno encontrado nesta sala."}), 404

        # 2. Busca todos os registros de frequência para esses alunos no período
        resp_frequencia = supabase.table('f_frequencia').select('*').in_('aluno_id', aluno_ids).gte('data', data_inicio).lte('data', data_fim).execute()
        frequencia_raw = handle_supabase_response(resp_frequencia)

        # Mapeia registros por (aluno_id, data)
        frequencia_map = {}
        for reg in frequencia_raw:
            key = (reg['aluno_id'], reg['data'])
            frequencia_map[key] = reg

        # 3. Monta a matriz de relatório
        relatorio = []
        
        # Gera a lista completa de datas no mês para a coluna do relatório
        dias_uteis = [datetime(ano, mes, d).strftime('%Y-%m-%d') for d in range(1, dias_no_mes + 1)]

        for aluno in alunos:
            aluno_row = {'id': aluno['id'], 'nome': aluno['nome'], 'dias': []}
            
            for data in dias_uteis:
                key = (aluno['id'], data)
                registro = frequencia_map.get(key)
                
                status_final = '?' # Não registrado / Fim de semana, etc.
                detalhes = None

                if registro:
                    status_final = registro['status']
                    if status_final in ['PA', 'PS', 'PAS']:
                        # Coleta os detalhes para o modal
                        detalhes = {
                            'hora_atraso': registro.get('hora_atraso'),
                            'motivo_atraso': registro.get('motivo_atraso'),
                            'responsavel_atraso': registro.get('responsavel_atraso'),
                            'telefone_atraso': registro.get('telefone_atraso'),
                            'hora_saida': registro.get('hora_saida'),
                            'motivo_saida': registro.get('motivo_saida'),
                            'responsavel_saida': registro.get('responsavel_saida'),
                            'telefone_saida': registro.get('telefone_saida'),
                        }

                aluno_row['dias'].append({'data': data, 'status': status_final, 'detalhes': detalhes})
            
            relatorio.append(aluno_row)
        
        return jsonify({
            'dias_mes': dias_no_mes,
            'relatorio': relatorio,
            'dias_uteis': dias_uteis # Lista de datas YYYY-MM-DD
        }), 200

    except Exception as e:
        logging.exception("Erro ao gerar relatório de frequência detalhada")
        return jsonify({"error": f"Erro ao gerar relatório: {e}"}), 500



      
@app.route('/api/relatorio_frequencia')
def api_relatorio_frequencia():
    # Simulação de dados para a rota de relatório
    try:
        sala_id = request.args.get('salaId')
        aluno_id = request.args.get('alunoId')
        data_inicial = request.args.get('dataInicial')
        data_final = request.args.get('dataFinal')
        return jsonify({
            'presencas_percentual': 92,
            'faltas_totais': 5,
            'atrasos_totais': 2,
            'saidas_antecipadas_totais': 1
        })
    except Exception as e:
        return jsonify({"error": f"Erro ao gerar relatório de frequência: {e}", "status": 500}), 500

@app.route('/api/frequencia/datas_registradas_por_sala/<int:sala_id>')
def api_datas_registradas(sala_id):
    try:
        resp = supabase.table('f_frequencia').select('data').eq('sala_id', sala_id).order('data').execute()
        datas = sorted(list({r['data'] for r in handle_supabase_response(resp)}))
        return jsonify(datas)
    except Exception as e:
        return jsonify({"error": f"Erro ao buscar datas: {e}", "status": 500}), 500

@app.route('/api/alunos_por_tutor/<tutor_id>')
def get_alunos_por_tutor(tutor_id):
    try:
        # Nota: Esta rota é redundante com /api/alunos, mas é mantida por causa do código original.
        data = supabase.table('alunos').select('id, nome').eq('tutor_id', tutor_id).execute()
        return jsonify(data.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/disciplinas', methods=['GET'])
def api_get_disciplinas():
    try:
        response = supabase.table('d_disciplinas').select('id, nome').order('nome').execute()
        disciplinas = handle_supabase_response(response)
        return jsonify(disciplinas)
    except Exception as e:
        return jsonify({"error": f"Erro ao buscar disciplinas: {e}", "status": 500}), 500

@app.route('/api/clubes', methods=['GET'])
def api_get_clubes():
    try:
        response = supabase.table('d_clubes').select('id, nome, semestre').order('semestre, nome').execute()
        clubes = handle_supabase_response(response)
        return jsonify(clubes)
    except Exception as e:
        return jsonify({"error": f"Erro ao buscar clubes: {e}", "status": 500}), 500

@app.route('/api/eletivas', methods=['GET'])
def api_get_eletivas():
    try:
        response = supabase.table('d_eletivas').select('id, nome, semestre').order('semestre, nome').execute()
        eletivas = handle_supabase_response(response)
        return jsonify(eletivas)
    except Exception as e:
        return jsonify({"error": f"Erro ao buscar eletivas: {e}", "status": 500}), 500

@app.route('/api/inventario', methods=['GET'])
def api_get_inventario():
    try:
        response = supabase.table('d_inventario_equipamentos').select('id, colmeia, equipamento_id, status').order('colmeia, equipamento_id').execute()
        inventario = handle_supabase_response(response)
        return jsonify(inventario)
    except Exception as e:
        return jsonify({"error": f"Erro ao buscar inventário: {e}", "status": 500}), 500

@app.route('/api/agendamentos_pendentes/<professor_id>', methods=['GET'])
def api_get_agendamentos_pendentes(professor_id):
    try:
        professor_id_bigint = int(professor_id)
        response = supabase.table('reservas_equipamentos').select('id, sala_id, data_uso, periodo_uso, status, professor_id').eq('professor_id', professor_id_bigint).neq('status', 'FINALIZADO').execute()
        agendamentos_raw = handle_supabase_response(response)
        agendamentos = []
        for ag in agendamentos_raw:
            agendamentos.append({
                "id": str(ag['id']),
                "sala_id": str(ag.get('sala_id')),
                "data_uso": str(ag.get('data_uso')),
                "periodo_uso": ag.get('periodo_uso'),
                "status": ag.get('status')
            })
        return jsonify(agendamentos)
    except Exception as e:
        return jsonify({"error": f"Erro ao buscar agendamentos pendentes: {e}", "status": 500}), 500

@app.route('/api/cadastrar_sala', methods=['POST'])
def api_cadastrar_sala():
    data = request.json
    sala = data.get('sala')
    nivel_ensino = data.get('nivel_ensino')
    if not sala or not nivel_ensino:
        return jsonify({"error": "Nome da sala e nível de ensino são obrigatórios.", "status": 400}), 400
    try:
        nova_sala = {"sala": sala, "nivel_ensino": nivel_ensino}
        response = supabase.table('d_salas').insert(nova_sala).execute()
        handle_supabase_response(response)
        return jsonify({"message": f"Sala {sala} cadastrada com sucesso!", "status": 201}), 201
    except Exception as e:
        if "unique constraint" in str(e):
            return jsonify({"error": f"Erro: A sala '{sala}' já existe. Não foi cadastrada.", "status": 409}), 409
        logging.error(f"Erro no Supabase durante o cadastro de sala: {e}")
        return jsonify({"error": f"Erro interno do servidor: {e}", "status": 500}), 500

@app.route('/api/cadastrar_funcionario', methods=['POST'])
def api_cadastrar_funcionario():
    data = request.json
    nome = data.get('nome')
    funcao = data.get('funcao')
    is_tutor = data.get('is_tutor', False)
    email_base = f"{nome.lower().replace(' ', '.').replace('prof.', 'p')[:15].strip('.')}"
    email = data.get('email', f"{email_base}@{os.urandom(4).hex()}.escola.com.br")

    if not nome or not funcao:
        return jsonify({"error": "Nome e função são obrigatórios.", "status": 400}), 400
    try:
        novo_funcionario = {
            "nome": nome,
            "email": email,
            "funcao": funcao,
            "is_tutor": is_tutor,
            "hobby": data.get('hobby', None),
        }
        if 'id' in data and data['id'] is not None:
            novo_funcionario['id'] = data['id']
            
        response = supabase.table('d_funcionarios').insert(novo_funcionario).execute()
        handle_supabase_response(response)
        return jsonify({"message": f"{nome} ({funcao}) cadastrado com sucesso!", "status": 201}), 201
    except Exception as e:
        if "unique constraint" in str(e):
            return jsonify({"error": "Erro: Já existe um funcionário com um nome similar/ID cadastrado.", "status": 409}), 409
        logging.error(f"Erro no Supabase durante o cadastro de funcionário: {e}")
        return jsonify({"error": f"Erro interno do servidor: {e}", "status": 500}), 500

@app.route('/api/cadastrar_disciplina', methods=['POST'])
def api_cadastrar_disciplina():
    data = request.json
    nome = data.get('nome')
    abreviacao = data.get('abreviacao')
    if not nome or not abreviacao:
        return jsonify({"error": "Nome e abreviação são obrigatórios.", "status": 400}), 400
    try:
        nova_disciplina = {
            "id": abreviacao.upper(),
            "nome": nome,
            "area_conhecimento": data.get('area_conhecimento', 'Geral')
        }
        response = supabase.table('d_disciplinas').insert(nova_disciplina).execute()
        handle_supabase_response(response)
        return jsonify({"message": f"Disciplina '{nome}' cadastrada com sucesso!", "status": 201}), 201
    except Exception as e:
        if "unique constraint" in str(e):
            return jsonify({"error": f"Erro: A abreviação '{abreviacao}' ou o nome já existe.", "status": 409}), 409
        return jsonify({"error": f"Falha ao cadastrar disciplina: {e}", "status": 500}), 500

@app.route('/api/cadastrar_clube', methods=['POST'])
def api_cadastrar_clube():
    data = request.json
    nome = data.get('nome')
    semestre = data.get('semestre')
    if not nome or not semestre:
        return jsonify({"error": "Nome do clube e semestre são obrigatórios.", "status": 400}), 400
    try:
        novo_clube = {"nome": nome, "semestre": semestre}
        response = supabase.table('d_clubes').insert(novo_clube).execute()
        handle_supabase_response(response)
        return jsonify({"message": f"Clube '{nome}' cadastrado com sucesso!", "status": 201}), 201
    except Exception as e:
        if "unique constraint" in str(e):
            return jsonify({"error": f"Erro: Clube '{nome}' já existe neste semestre.", "status": 409}), 409
        return jsonify({"error": f"Falha ao cadastrar clube: {e}", "status": 500}), 500

@app.route('/api/cadastrar_eletiva', methods=['POST'])
def api_cadastrar_eletiva():
    data = request.json
    nome = data.get('nome')
    semestre = data.get('semestre')
    if not nome or not semestre:
        return jsonify({"error": "Nome da eletiva e semestre são obrigatórios.", "status": 400}), 400
    try:
        nova_eletiva = {"nome": nome, "semestre": semestre}
        response = supabase.table('d_eletivas').insert(nova_eletiva).execute()
        handle_supabase_response(response)
        return jsonify({"message": f"Eletiva '{nome}' cadastrada com sucesso!", "status": 201}), 201
    except Exception as e:
        if "unique constraint" in str(e):
            return jsonify({"error": f"Erro: Eletiva '{nome}' já existe neste semestre.", "status": 409}), 409
        return jsonify({"error": f"Falha ao cadastrar eletiva: {e}", "status": 500}), 500

@app.route('/api/cadastrar_equipamento', methods=['POST'])
def api_cadastrar_equipamento():
    data = request.json
    colmeia = data.get('colmeia')
    equipamento_id = data.get('equipamento_id')
    if not colmeia or not equipamento_id:
        return jsonify({"error": "Colmeia e ID do equipamento são obrigatórios.", "status": 400}), 400
    try:
        novo_equipamento = {"colmeia": colmeia, "equipamento_id": int(equipamento_id), "status": "DISPONÍVEL"}
        response = supabase.table('d_inventario_equipamentos').insert(novo_equipamento).execute()
        handle_supabase_response(response)
        return jsonify({"message": f"Equipamento {equipamento_id} da {colmeia} cadastrado com sucesso!", "status": 201}), 201
    except Exception as e:
        if "unique constraint" in str(e):
            return jsonify({"error": f"Erro: O Equipamento {equipamento_id} na {colmeia} já existe.", "status": 409}), 409
        return jsonify({"error": f"Falha ao cadastrar equipamento: {e}", "status": 500}), 500

@app.route('/api/cadastrar_aluno', methods=['POST'])
def api_cadastrar_aluno():
    data = request.json
    ra = data.get('ra')
    nome = data.get('nome')
    sala_id = data.get('sala_id')
    tutor_id = data.get('tutor_id')
    if not ra or not nome or not sala_id or not tutor_id:
        return jsonify({"error": "RA, Nome, Sala e Tutor são obrigatórios.", "status": 400}), 400
    try:
        sala_id_bigint = int(sala_id)
        tutor_id_bigint = int(tutor_id)
        novo_aluno = {"ra": ra, "nome": nome, "sala_id": sala_id_bigint, "tutor_id": tutor_id_bigint}
        response = supabase.table('d_alunos').insert(novo_aluno).execute()
        handle_supabase_response(response)
        return jsonify({"message": f"Aluno(a) {nome} (RA: {ra}) cadastrado com sucesso!", "status": 201}), 201
    except Exception as e:
        if "unique constraint" in str(e):
            return jsonify({"error": f"Erro: O RA '{ra}' já está cadastrado no sistema.", "status": 409}), 409
        logging.error(f"Erro no Supabase durante o cadastro de aluno: {e}")
        return jsonify({"error": f"Erro interno do servidor: {e}", "status": 500}), 500

@app.route('/api/vincular_disciplina_sala', methods=['POST'])
def api_vincular_disciplina_sala():
    data = request.json
    sala_id = data.get('sala_id')
    disciplinas_ids = data.get('disciplinas')
    if not sala_id:
        return jsonify({"error": "ID da sala é obrigatório.", "status": 400}), 400
    try:
        sala_id_bigint = int(sala_id)
        # Limpa todos os vínculos existentes para esta sala
        supabase.table('vinculos_disciplina_sala').delete().eq('sala_id', sala_id_bigint).execute()
        if disciplinas_ids:
            # Insere os novos vínculos
            registros = [{"sala_id": sala_id_bigint, "disciplina_id": d_id} for d_id in disciplinas_ids]
            supabase.table('vinculos_disciplina_sala').insert(registros).execute()
        return jsonify({"message": f"Vínculos da sala {sala_id} atualizados com sucesso.", "status": 200}), 200
    except Exception as e:
        logging.error(f"Erro ao salvar vínculos de disciplina: {e}")
        return jsonify({"error": f"Falha ao salvar vínculos de disciplina: {e}", "status": 500}), 500

@app.route('/api/vincular_tutor_aluno', methods=['POST'])
def api_vincular_tutor_aluno():
    data = request.json
    tutor_id = data.get('tutor_id')
    vinculos = data.get('vinculos')
    sala_id = data.get('sala_id')
    
    if not tutor_id or not sala_id:
        return jsonify({"error": "ID do tutor e ID da sala são obrigatórios.", "status": 400}), 400
    
    try:
        tutor_id_bigint = int(tutor_id)
        sala_id_bigint = int(sala_id)
        
        alunos_a_vincular_ids = [int(v['aluno_id']) for v in vinculos if 'aluno_id' in v]
        
        # 1. Desvincula o tutor de todos os alunos da sala que atualmente estão vinculados ao tutor_id passado
        alunos_na_sala_raw = supabase.table('d_alunos').select('id').eq('sala_id', sala_id_bigint).eq('tutor_id', tutor_id_bigint).execute()
        alunos_na_sala_ids = [int(a['id']) for a in handle_supabase_response(alunos_na_sala_raw)]
        
        # Alunos que estavam vinculados a este tutor e foram desmarcados
        alunos_a_desvincular_ids = [a_id for a_id in alunos_na_sala_ids if a_id not in alunos_a_vincular_ids]
        
        if alunos_a_desvincular_ids:
            logging.info(f"Desvinculando alunos: {alunos_a_desvincular_ids} da sala {sala_id_bigint} do tutor {tutor_id_bigint}")
            supabase.table('d_alunos').update({'tutor_id': None}).in_('id', alunos_a_desvincular_ids).execute()
        
        # 2. Vincula o tutor aos alunos selecionados
        if alunos_a_vincular_ids:
            for aluno_id in alunos_a_vincular_ids:
                supabase.table('d_alunos').update({'tutor_id': tutor_id_bigint}).eq('id', aluno_id).execute()
                
        return jsonify({"message": "Vínculos atualizados com sucesso.", "status": 200}), 200
    except Exception as e:
        logging.error(f"Erro ao vincular tutor/aluno: {e}")
        return jsonify({"error": f"Falha ao vincular tutor/aluno: {e}", "status": 500}), 500

       
@app.route('/api/salvar_parametros', methods=['POST'])
def api_salvar_parametros():
    data = request.json
    if not data:
        return jsonify({"error": "Nenhum parâmetro enviado.", "status": 400}), 400
    try:
        updates = []
        for key, value in data.items():
            updates.append({"parametro": key, "valor": value})
        response = supabase.table('cfg_parametros').upsert(updates, on_conflict='parametro').execute()
        handle_supabase_response(response)
        return jsonify({"message": "Parâmetros de configuração salvos com sucesso!", "status": 200}), 200
    except Exception as e:
        return jsonify({"error": f"Falha ao salvar configurações: {e}", "status": 500}), 500

@app.route('/api/atualizar_ocorrencia/<ocorrencia_id>', methods=['PUT'])
def api_atualizar_ocorrencia(ocorrencia_id):
    data = request.json
    if not data:
        return jsonify({"error": "Nenhum dado de atualização enviado.", "status": 400}), 400
    try:
        ocorrencia_id_bigint = int(ocorrencia_id)
        response = supabase.table('ocorrencias').update(data).eq('numero', ocorrencia_id_bigint).execute()
        handle_supabase_response(response)
        return jsonify({"message": "Ocorrência atualizada com sucesso.", "status": 200}), 200
    except Exception as e:
        return jsonify({"error": f"Falha ao atualizar ocorrência: {e}", "status": 500}), 500

@app.route('/api/finalizar_retirada_equipamento', methods=['POST'])
def api_finalizar_retirada_equipamento():
    data = request.json
    agendamento_id = data.get('agendamento_id')
    vinculacoes = data.get('vinculacoes')
    status_agendamento = data.get('status_agendamento')
    if not agendamento_id or not status_agendamento:
        return jsonify({"error": "ID do agendamento e Status são obrigatórios.", "status": 400}), 400
    try:
        update_data = {"status": status_agendamento, "data_retirada_geral": data.get('data_retirada_geral'), "termo_aceite_registro": data.get('termo_aceite_registro')}
        supabase.table('reservas_equipamentos').update(update_data).eq('id', agendamento_id).execute()
        if vinculacoes:
            registros = []
            for v in vinculacoes:
                registros.append({
                    "agendamento_id": int(agendamento_id),
                    "aluno_id": int(v['aluno_id']),
                    "equipamento_id": v['equipamento_id'],
                    "data_retirada": v['data_retirada']
                })
            if registros:
                supabase.table('rastreamento_equipamento').insert(registros).execute()
        return jsonify({"message": f"Retirada do agendamento {agendamento_id} finalizada e equipamentos vinculados!", "status": 200}), 200
    except Exception as e:
        logging.error(f"Erro ao finalizar retirada: {e}")
        return jsonify({"error": f"Erro interno ao finalizar retirada: {e}", "status": 500}), 500

@app.route('/api/finalizar_devolucao_equipamento', methods=['POST'])
def api_finalizar_devolucao_equipamento():
    data = request.json
    agendamento_id = data.get('agendamento_id')
    if not agendamento_id:
        return jsonify({"error": "ID do agendamento é obrigatório.", "status": 400}), 400
    try:
        update_data = {"status": "FINALIZADO", "data_devolucao": data.get('data_devolucao', datetime.now().isoformat())}
        supabase.table('reservas_equipamentos').update(update_data).eq('id', agendamento_id).execute()
        return jsonify({"message": f"Devolução do agendamento {agendamento_id} finalizada com sucesso!", "status": 200}), 200
    except Exception as e:
        logging.error(f"Erro ao finalizar devolução: {e}")
        return jsonify({"error": f"Erro interno ao finalizar devolução: {e}", "status": 500}), 500

@app.route('/api/relatorio_estatistico', methods=['GET'])
def api_relatorio_estatistico():
    """Gera o JSON de estatísticas de ocorrências."""
    try:
        # 1. Obter todas as ocorrências detalhadas
        resp_occ = supabase.table('ocorrencias').select(
            "numero, data_hora, status, tipo, tutor_id, sala_id, "
            "solicitado_tutor, solicitado_coordenacao, solicitado_gestao, "
            "atendimento_tutor, atendimento_coordenacao, atendimento_gestao, "
            "dt_atendimento_gestao" # Usamos o dt_atendimento_gestao como data de fechamento final
        ).execute()
        ocorrencias = handle_supabase_response(resp_occ)
        
        # 2. Obter mapeamentos de Sala e Tutor
        resp_salas = supabase.table('d_salas').select('id, sala').execute()
        salas_map = {str(s['id']): s['sala'] for s in handle_supabase_response(resp_salas)}
        
        resp_tutores = supabase.table('d_funcionarios').select('id, nome').eq('is_tutor', True).execute()
        tutores_map = {str(t['id']): t['nome'] for t in handle_supabase_response(resp_tutores)}

        # 3. Agregação de dados
        total = len(ocorrencias)
        abertas = 0
        finalizadas = 0
        
        tipos_count = {}
        salas_stats = {} # Por Sala: {total, menos_7d, mais_7d, nao_respondidas}
        tutores_stats = {} # Por Tutor: {total, finalizadas, abertas, tempos_resposta: []}
        tempo_resposta_faixas = {
            '1-7 dias': 0, '8-30 dias': 0, 'mais de 30 dias': 0, 'não finalizadas': 0
        }
        ocorrencias_por_mes = {} # {mes_ano: count}
        
        hoje = datetime.now()
        
        for occ in ocorrencias:
            occ_status = occ.get('status')
            occ_data_hora = occ.get('data_hora')
            occ_tipo = occ.get('tipo', 'Outros')
            sala_id_str = str(occ.get('sala_id'))
            tutor_id_str = str(occ.get('tutor_id')) if occ.get('tutor_id') else None
            
            # 3.1. Totais e Tipos
            if occ_status == 'Aberta':
                abertas += 1
            elif occ_status == 'Finalizada':
                finalizadas += 1
            
            tipos_count[occ_tipo] = tipos_count.get(occ_tipo, 0) + 1
            
            # 3.2. Por Mês
            if occ_data_hora:
                try:
                    dt = datetime.fromisoformat(occ_data_hora.replace('Z', '+00:00'))
                    mes_ano_key = dt.strftime("%Y-%m")
                    ocorrencias_por_mes[mes_ano_key] = ocorrencias_por_mes.get(mes_ano_key, 0) + 1
                except Exception:
                    logging.warning(f"Data de ocorrência inválida: {occ_data_hora}")
            
            # 3.3. Estatísticas por Sala
            if sala_id_str in salas_map:
                sala_name = salas_map[sala_id_str]
                if sala_id_str not in salas_stats:
                    salas_stats[sala_id_str] = {'sala': sala_name, 'total': 0, 'menos_7d': 0, 'mais_7d': 0, 'nao_respondidas': 0}
                salas_stats[sala_id_str]['total'] += 1
                
                if occ_status == 'Aberta' and occ_data_hora:
                    try:
                        dt_abertura = datetime.fromisoformat(occ_data_hora.replace('Z', '+00:00'))
                        dias_aberta = (hoje - dt_abertura).days
                        
                        if dias_aberta <= 7:
                            salas_stats[sala_id_str]['menos_7d'] += 1
                        else:
                            salas_stats[sala_id_str]['mais_7d'] += 1
                            
                        # Verifica se é "Não Respondida"
                        solicitado = (_to_bool(occ.get('solicitado_tutor')) or 
                                      _to_bool(occ.get('solicitado_coordenacao')) or 
                                      _to_bool(occ.get('solicitado_gestao')))
                        
                        atendimento_tutor = occ.get('atendimento_tutor')
                        atendimento_coord = occ.get('atendimento_coordenacao')
                        atendimento_gestao = occ.get('atendimento_gestao')
                        
                        respondido = (
                            (atendimento_tutor and atendimento_tutor != DEFAULT_AUTOTEXT) or
                            (atendimento_coord and atendimento_coord != DEFAULT_AUTOTEXT) or
                            (atendimento_gestao and atendimento_gestao != DEFAULT_AUTOTEXT)
                        )
                        
                        if solicitado and not respondido:
                            salas_stats[sala_id_str]['nao_respondidas'] += 1
                    except Exception:
                        logging.warning(f"Erro no cálculo de dias abertas para ocorrência {occ.get('numero')}")


            # 3.4. Estatísticas por Tutor
            if tutor_id_str and tutor_id_str in tutores_map:
                tutor_name = tutores_map[tutor_id_str]
                if tutor_id_str not in tutores_stats:
                    tutores_stats[tutor_id_str] = {'tutor': tutor_name, 'total': 0, 'finalizadas': 0, 'abertas': 0, 'tempos_resposta': []}
                
                tutores_stats[tutor_id_str]['total'] += 1
                if occ_status == 'Finalizada':
                    tutores_stats[tutor_id_str]['finalizadas'] += 1
                    
                    # Calcula o tempo de resposta
                    dias_resp = calcular_dias_resposta(occ_data_hora, occ.get('dt_atendimento_gestao'))
                    if dias_resp is not None:
                        tutores_stats[tutor_id_str]['tempos_resposta'].append(dias_resp)
                        
                        if dias_resp <= 7:
                            tempo_resposta_faixas['1-7 dias'] += 1
                        elif dias_resp <= 30:
                            tempo_resposta_faixas['8-30 dias'] += 1
                        else:
                            tempo_resposta_faixas['mais de 30 dias'] += 1
                else:
                    tutores_stats[tutor_id_str]['abertas'] += 1
                    tempo_resposta_faixas['não finalizadas'] += 1

        # 4. Finalização dos cálculos e formatação
        
        # Média de dias de resposta por tutor
        final_tutores = []
        for t_id, t_data in tutores_stats.items():
            t_data['media_dias_resposta'] = sum(t_data['tempos_resposta']) / len(t_data['tempos_resposta']) if t_data['tempos_resposta'] else 0
            # Formatação para o JS
            final_tutores.append({
                'tutor': t_data['tutor'],
                'total': t_data['total'],
                'finalizadas': t_data['finalizadas'],
                'abertas': t_data['abertas'],
                'media_dias_resposta': round(t_data['media_dias_resposta'], 1) if t_data['media_dias_resposta'] else 0
            })
            
        # Formatação do Tempo de Resposta para Gráfico
        tempo_resp_grafico = {
            'labels': list(tempo_resposta_faixas.keys()),
            'valores': list(tempo_resposta_faixas.values())
        }
        
        # Formatação Ocorrências por Mês para Gráfico
        meses_ordenados = sorted(ocorrencias_por_mes.keys())
        ocorrencias_por_mes_grafico = {
            'labels': [datetime.strptime(m, "%Y-%m").strftime("%b/%y") for m in meses_ordenados],
            'valores': [ocorrencias_por_mes[m] for m in meses_ordenados]
        }

        # 5. Retorno do JSON final
        return jsonify({
            'total': total,
            'abertas': abertas,
            'finalizadas': finalizadas,
            'tipos': tipos_count,
            'por_sala': list(salas_stats.values()),
            'por_tutor': final_tutores,
            'tempo_resposta': tempo_resp_grafico,
            'ocorrencias_por_mes': ocorrencias_por_mes_grafico
        }), 200

    except Exception as e:
        logging.exception("Erro ao gerar relatório estatístico")
        # Retorna um JSON de erro válido
        return jsonify({"error": f"Erro interno ao gerar relatório: {e}"}), 500

def safe_pdf_text(text):
    """Garante que a string é tratada corretamente pelo FPDF, prevenindo erros de codificação."""
    if text is None:
        return "N/A"
    return str(text).encode('latin-1', 'replace').decode('latin-1')

@app.route('/api/gerar_pdf_ocorrencias', methods=['POST'])
def gerar_pdf_ocorrencias():
    dados = request.get_json()
    numeros = dados.get('numeros', [])

    if not numeros:
        return jsonify({"error": "Nenhuma ocorrência selecionada"}), 400

    try:
        # Buscar ocorrências no Supabase
        resp = supabase.table('ocorrencias').select(
            "numero, data_hora, descricao, status, aluno_nome, sala_id, tutor_nome, atendimento_professor, atendimento_tutor, atendimento_coordenacao, atendimento_gestao, impressao_pdf"
        ).in_('numero', numeros).order('data_hora', desc=True).execute()

        ocorrencias = resp.data

        if not ocorrencias:
            return jsonify({"error": "Nenhuma ocorrência encontrada"}), 404

        # 1. Configuração do PDF (A4 com margens em mm)
        pdf = FPDF(unit="mm", format="A4")
        pdf.set_margins(left=15, top=15, right=15)
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Largura útil para o texto (210mm - 15mm - 15mm = 180mm)
        w_total = 180 
        x_inicial = 15 # Margem esquerda

        # 2. Cabeçalho Principal
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 8, safe_pdf_text("RELATÓRIO DE REGISTRO DE OCORRÊNCIAS"), ln=True, align='C')
        
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 5, safe_pdf_text("E.E. PEI PROFESSOR IRENE DIAS RIBEIRO"), ln=True, align='C')
        pdf.ln(5)

        # 3. Cabeçalho do Aluno (usando primeira ocorrência)
        aluno_nome = ocorrencias[0].get("aluno_nome", "Aluno Desconhecido")
        sala = ocorrencias[0].get("sala_id", "Indefinida")
        tutor = ocorrencias[0].get("tutor_nome", "Indefinido") 
        
        pdf.set_fill_color(220, 220, 220) # Cinza claro para o cabeçalho
        pdf.set_font("Arial", "B", 10)
        pdf.cell(w_total * 0.5, 6, safe_pdf_text(f"Aluno: {aluno_nome}"), border=1, ln=False, fill=True)
        pdf.cell(w_total * 0.25, 6, safe_pdf_text(f"Sala: {sala}"), border=1, ln=False, fill=True)
        pdf.cell(w_total * 0.25, 6, safe_pdf_text(f"Tutor: {tutor}"), border=1, ln=True, fill=True)
        pdf.ln(5)
        
        pdf.set_font("Arial", "", 10)

        # 4. Loop pelas Ocorrências
        for i, o in enumerate(ocorrencias):
            # Adiciona quebra de página se não houver espaço suficiente para a próxima ocorrência
            if pdf.get_y() > 260 and i < len(ocorrencias) - 1:
                pdf.add_page()
                pdf.set_font("Arial", "", 10)

            pdf.set_font("Arial", "B", 11)
            pdf.set_text_color(255, 0, 0) # Cor de destaque para o número da ocorrência
            pdf.cell(0, 6, safe_pdf_text(f"Registro de Ocorrência nº: {o.get('numero')} - Status: {o.get('status', 'N/A')}"), ln=True)
            pdf.set_text_color(0, 0, 0) # Volta ao preto
            
            pdf.set_font("Arial", "", 10)
            data_hora = o.get('data_hora', '')
            data, hora = 'N/A', 'N/A'
            if data_hora:
                try:
                    dt = datetime.fromisoformat(data_hora.replace('Z', '+00:00'))
                    data = dt.strftime("%d/%m/%Y")
                    hora = dt.strftime("%H:%M:%S")
                except:
                    pass

            pdf.cell(w_total, 5, safe_pdf_text(f"Data/Hora: {data} às {hora}"), ln=True)

            # --- DESCRIÇÃO DA OCORRÊNCIA (Usa multi_cell para quebrar a linha) ---
            pdf.set_font("Arial", "B", 10)
            pdf.cell(w_total, 5, safe_pdf_text("1. Descrição do Evento:"), ln=True)
            pdf.set_font("Arial", "", 10)
            pdf.multi_cell(w=w_total, h=5, txt=safe_pdf_text(o.get('descricao', 'N/A')), border=1)
            pdf.ln(2) # Espaçamento

            # --- ATENDIMENTOS (Usa multi_cell para quebrar a linha) ---
            
            # ATENDIMENTO PROFESSOR
            professor_atendimento = o.get('atendimento_professor', 'N/A')
            pdf.set_font("Arial", "B", 10)
            pdf.cell(w_total, 5, safe_pdf_text("2. Atendimento Professor/Escolar:"), ln=True)
            pdf.set_font("Arial", "", 10)
            pdf.multi_cell(w=w_total, h=5, txt=safe_pdf_text(professor_atendimento), border=1)
            pdf.ln(2) # Espaçamento

            # ATENDIMENTO TUTOR
            tutor_atendimento = o.get('atendimento_tutor', 'N/A')
            pdf.set_font("Arial", "B", 10)
            pdf.cell(w_total, 5, safe_pdf_text("3. Atendimento Tutor (se realizado):"), ln=True)
            pdf.set_font("Arial", "", 10)
            pdf.multi_cell(w=w_total, h=5, txt=safe_pdf_text(tutor_atendimento), border=1)
            pdf.ln(2) # Espaçamento

            # ATENDIMENTO COORDENAÇÃO
            coordenacao_atendimento = o.get('atendimento_coordenacao', 'N/A')
            pdf.set_font("Arial", "B", 10)
            pdf.cell(w_total, 5, safe_pdf_text("4. Atendimento Coordenação (se realizado):"), ln=True)
            pdf.set_font("Arial", "", 10)
            pdf.multi_cell(w=w_total, h=5, txt=safe_pdf_text(coordenacao_atendimento), border=1)
            pdf.ln(2) # Espaçamento

            # ATENDIMENTO GESTÃO
            gestao_atendimento = o.get('atendimento_gestao', 'N/A')
            pdf.set_font("Arial", "B", 10)
            pdf.cell(w_total, 5, safe_pdf_text("5. Atendimento Gestão (se realizado):"), ln=True)
            pdf.set_font("Arial", "", 10)
            pdf.multi_cell(w=w_total, h=5, txt=safe_pdf_text(gestao_atendimento), border=1)
            pdf.ln(5) # Espaçamento final
            
            # Linha separadora entre ocorrências
            if i < len(ocorrencias) - 1:
                 pdf.set_draw_color(150, 150, 150) # Cinza
                 pdf.line(x_inicial, pdf.get_y(), x_inicial + w_total, pdf.get_y())
                 pdf.ln(5)


        # 5. Seção de Assinatura (No final da última página)
        pdf.ln(10)
        
        # Linhas de Assinatura
        y_assinatura = pdf.get_y()
        w_linha = w_total / 2 - 10 # 5mm de margem entre as linhas
        
        pdf.set_y(y_assinatura)
        pdf.set_font("Arial", "B", 10)
        
        # Linha 1: Assinatura
        pdf.set_x(x_inicial)
        pdf.cell(w_linha, 5, "___________________________________", ln=False, align='C')
        pdf.set_x(x_inicial + w_total / 2 + 5)
        pdf.cell(w_linha, 5, "___________________________________", ln=True, align='C')

        # Linha 2: Títulos
        pdf.set_x(x_inicial)
        pdf.cell(w_linha, 5, safe_pdf_text("Professor(a)/Responsável pelo Atendimento"), ln=False, align='C')
        pdf.set_x(x_inicial + w_total / 2 + 5)
        pdf.cell(w_linha, 5, safe_pdf_text("Diretor(a)/Coordenador(a)"), ln=True, align='C')
        
        pdf.ln(5)
        pdf.set_x(x_inicial)
        pdf.cell(w_total, 5, safe_pdf_text(f"Data de Impressão: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"), ln=True, align='R')


        # 6. Finalização e Envio
        pdf_buffer = io.BytesIO()
        pdf.output(pdf_buffer)
        pdf_buffer.seek(0)
        
        # LÓGICA DE ATUALIZAÇÃO NO SUPABASE APÓS SUCESSO DO PDF
        if pdf_buffer.getbuffer().nbytes > 0:
            update_data = {"impressao_pdf": True}
            supabase.table('ocorrencias').update(update_data).in_('numero', numeros).execute()
            logging.info(f"Ocorrências {numeros} marcadas como impressas (impressao_pdf=True).")


        nome_arquivo = aluno_nome.replace(' ', '_') + "_relatorio_ocorrencias.pdf"
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=nome_arquivo,
            mimetype='application/pdf'
        )

    except Exception as e:
        # Garante que o log de erro seja útil
        logging.exception(f"Falha fatal ao gerar PDF ou atualizar status de impressão: {str(e)}")
        return jsonify({"error": f"Falha ao gerar PDF: {str(e)}"}), 500
# --- ROTAS/ENDPOINTS CORRIGIDOS (FREQUÊNCIA e TUTORIA) ---

# /api/salas -> retorna id e sala (nome)
@app.route("/api/salas", methods=["GET"])
def api_salas():
    try:
        resp = supabase.table("d_salas").select("id, sala").order("sala").execute()
        salas = handle_supabase_response(resp)
        # Normaliza chave para o frontend que usa .sala
        salas_norm = [{"id": s.get("id"), "sala": s.get("sala")} for s in salas]
        return jsonify(salas_norm), 200
    except Exception as e:
        logging.exception("Erro /api/salas")
        return jsonify({"error": str(e)}), 500


# /api/alunos_por_sala/<sala_id> -> retorna id, nome, tutor_id, tutor_nome
@app.route('/api/alunos_por_sala/<int:sala_id>', methods=['GET'])
def api_get_alunos_por_sala(sala_id):
    try:
        resp_alunos = supabase.table('d_alunos').select('id, nome, tutor_id').eq('sala_id', sala_id).order('nome').execute()
        alunos_raw = handle_supabase_response(resp_alunos)

        # Recupera tutores uma vez
        resp_tutores = supabase.table('d_funcionarios').select('id,nome').eq('is_tutor', True).execute()
        tutores = handle_supabase_response(resp_tutores)
        tutores_map = {str(t['id']): t['nome'] for t in tutores}

        alunos = []
        for a in alunos_raw:
            tutor_id = a.get('tutor_id')
            alunos.append({
                "id": a.get('id'),
                "nome": a.get('nome'),
                "tutor_id": tutor_id,
                "tutor_nome": tutores_map.get(str(tutor_id), "Tutor Não Definido")
            })
        return jsonify(alunos), 200
    except Exception as e:
        logging.exception("Erro api_get_alunos_por_sala")
        return jsonify({"error": str(e)}), 500


# /api/frequencia?sala=<id>&mes=<num>&ano=<yyyy (opcional)>
# Retorna lista de alunos da sala e, para cada aluno, um objeto "frequencia" com chaves "YYYY-MM-DD" -> status
@app.route("/api/frequencia", methods=["GET"])
def api_frequencia():
    try:
        sala_id = request.args.get("sala")
        mes = request.args.get("mes")
        ano = request.args.get("ano") or str(datetime.now().year)

        if not sala_id or not mes:
            return jsonify({"error":"sala e mes são obrigatórios"}), 400
        sala_id_int = int(sala_id)
        mes_int = int(mes)
        ano_int = int(ano)

        # 1) lista alunos da sala
        resp_alunos = supabase.table('d_alunos').select('id, nome').eq('sala_id', sala_id_int).order('nome').execute()
        alunos = handle_supabase_response(resp_alunos)
        aluno_ids = [a['id'] for a in alunos] if alunos else []

        if not aluno_ids:
            # retorna estrutura padrão vazia
            return jsonify([]), 200

        # 2) busca registros f_frequencia para esses alunos no mês/ano
        inicio = f"{ano_int}-{mes_int:02d}-01"
        fim = f"{ano_int}-{mes_int:02d}-{monthrange(ano_int, mes_int)[1]:02d}"

        resp_freq = supabase.table('f_frequencia').select('*')\
            .in_('aluno_id', aluno_ids)\
            .gte('data', inicio).lte('data', fim).order('aluno_id').execute()
        freq_raw = handle_supabase_response(resp_freq)

        # 3) monta mapa (aluno_id, data) -> registro
        freq_map = {}
        for r in freq_raw:
            key = (r.get('aluno_id'), r.get('data'))
            freq_map[key] = r

        resultado = []
        for a in alunos:
            aid = a['id']
            resultado.append({
                "id": aid,
                "nome": a['nome'],
                "frequencia": {}  # preenchido abaixo no frontend
            })
            # Preenchimento detalhado fica a cargo do frontend, mas vamos retornar registros encontrados:
        # Para conveniência retornamos também freq_raw agrupado
        return jsonify({
            "alunos": resultado,
            "registros": freq_raw
        }), 200

    except Exception as e:
        logging.exception("Erro /api/frequencia")
        return jsonify({"error": str(e)}), 500


# /api/frequencia/status?sala_id=<>&data=YYYY-MM-DD
@app.route('/api/frequencia/status', methods=['GET'])
def api_frequencia_status():
    try:
        sala_id = request.args.get('sala_id')
        data = request.args.get('data')
        if not sala_id or not data:
            return jsonify({"error":"sala_id e data obrigatórios"}), 400
        resp = supabase.table('f_frequencia').select('id').eq('sala_id', int(sala_id)).eq('data', data).limit(1).execute()
        registrada = bool(handle_supabase_response(resp))
        return jsonify({"registrada": registrada}), 200
    except Exception as e:
        logging.exception("Erro api_frequencia_status")
        return jsonify({"error": str(e)}), 500


# /api/frequencia/detalhes?aluno_id=&data=
@app.route('/api/frequencia/detalhes', methods=['GET'])
def api_frequencia_detalhes():
    try:
        aluno_id = request.args.get('aluno_id')
        data = request.args.get('data')
        if not aluno_id or not data:
            return jsonify({"error":"aluno_id e data obrigatórios"}), 400
        resp = supabase.table('f_frequencia').select('*').eq('aluno_id', int(aluno_id)).eq('data', data).maybe_single().execute()
        if not resp.data:
            return jsonify({"error":"Registro não encontrado"}), 404
        return jsonify(resp.data), 200
    except Exception as e:
        logging.exception("Erro api_frequencia_detalhes")
        return jsonify({"error": str(e)}), 500


# FICHA DE TUTORIA - usa tutoria_geral conforme informado
@app.route('/api/ficha_tutoria/<int:aluno_id>', methods=['GET'])
def get_ficha_tutoria(aluno_id):
    try:
        resp = supabase.table('tutoria_geral').select('*').eq('aluno_id', aluno_id).order('data_registro', desc=True).limit(1).maybe_single().execute()
        if not resp.data:
            return jsonify({}), 200
        return jsonify(resp.data), 200
    except Exception as e:
        logging.exception("Erro get_ficha_tutoria")
        return jsonify({"error": str(e)}), 500


# AGENDAR TUTORIA -> grava em tutoria_geral
@app.route('/api/agendar_tutoria', methods=['POST'])
def api_agendar_tutoria():
    data = request.json
    if not data or not all(data.get(k) for k in ('tutor_id', 'aluno_id', 'data_agendamento', 'hora_agendamento')):
        return jsonify({"error":"Dados de agendamento incompletos"}), 400
    try:
        registro = {
            "tutor_id": int(data['tutor_id']),
            "aluno_id": int(data['aluno_id']),
            "data_agendamento": data['data_agendamento'],
            "hora_agendamento": data['hora_agendamento'],
            "status": data.get('status', 'AGENDADO'),
            "data_registro": datetime.now().isoformat()
        }
        resp = supabase.table('tutoria_geral').insert(registro).execute()
        handle_supabase_response(resp)
        return jsonify({"message":"Agendamento criado", "status":201}), 201
    except Exception as e:
        logging.exception("Erro api_agendar_tutoria")
        return jsonify({"error": str(e)}), 500


# SALVAR ATENDIMENTO: usa tabela ocorrencias e campo 'numero' como chave
@app.route("/api/salvar_atendimento", methods=["POST"])
def salvar_atendimento():
    data = request.get_json()
    try:
        numero = data.get("id")
        nivel = data.get("nivel")
        texto = data.get("texto")
        if not numero or not nivel or texto is None:
            return jsonify({"error": "Dados incompletos."}), 400
        campo = f"atendimento_{nivel}"
        response = supabase.table("ocorrencias").update({campo: texto}).eq("numero", numero).execute()
        if response and getattr(response, "data", None):
            return jsonify({"message": "Atendimento salvo com sucesso!"}), 200
        else:
            return jsonify({"error": "Falha ao atualizar ocorrência."}), 500
    except Exception as e:
        logging.exception("Erro salvar_atendimento")
        return jsonify({"error": str(e)}), 500

@app.route('/api/ocorrencias_por_aluno/<int:aluno_id>')
def ocorrencias_por_aluno(aluno_id):
    try:
        select_query = (
            "numero, data_hora, descricao, status, "
            "atendimento_professor, atendimento_tutor, atendimento_coordenacao, atendimento_gestao, "
            "professor_id(nome), tutor_nome, sala_id(sala), aluno_nome"
        )

        # Busca todas as ocorrências do aluno no Supabase
        resp = supabase.table('ocorrencias').select(select_query).eq('aluno_id', aluno_id).execute()

        ocorrencias = resp.data or []

        # Retorna sempre JSON
        return jsonify(ocorrencias), 200

    except Exception as e:
        logging.exception(f"Erro ao buscar ocorrências do aluno {aluno_id}")
        return jsonify({'error': f'Erro ao consultar Supabase: {str(e)}'}), 500


# =========================================================
# EXECUÇÃO
# =========================================================

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))









