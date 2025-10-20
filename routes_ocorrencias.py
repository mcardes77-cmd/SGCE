from flask import Blueprint, request, jsonify, send_file
import io
import json
from datetime import datetime
import logging
from fpdf import FPDF

# Importa as utilidades do banco de dados e funções auxiliares
from db_utils import (
    supabase, handle_supabase_response, formatar_data_hora, 
    _to_bool, DEFAULT_AUTOTEXT, calcular_dias_resposta, safe_pdf_text
)

# Define o Blueprint para as rotas de Ocorrências
ocorrencias_bp = Blueprint('ocorrencias', __name__)


# =========================================================
# FUNÇÕES DEDICADAS DE CONSULTA E PROCESSAMENTO (OCORRÊNCIAS)
# =========================================================

# ROTA: /api/salas (CORRIGIDA - Retorna 'nome' em vez de 'sala')
@ocorrencias_bp.route("/api/salas", methods=["GET"])
def api_salas():
    try:
        resp = supabase.table("d_salas").select("id, sala").order("sala").execute()
        salas = handle_supabase_response(resp)
        # CORREÇÃO: Altera a chave 'sala' para 'nome' para compatibilidade com o frontend
        salas_norm = [{"id": s.get("id"), "nome": s.get("sala")} for s in salas]
        return jsonify(salas_norm), 200
    except Exception as e:
        logging.exception("Erro /api/salas")
        return jsonify({"error": str(e)}), 500


# ROTA: /api/alunos_por_sala/<sala_id> (Mantida a lógica de busca do tutor)
@ocorrencias_bp.route('/api/alunos_por_sala/<int:sala_id>', methods=['GET'])
def api_get_alunos_por_sala(sala_id):
    from db_utils import get_alunos_por_sala_data # Importa a função centralizada
    try:
        alunos = get_alunos_por_sala_data(sala_id)
        return jsonify(alunos), 200
    except Exception as e:
        logging.exception("Erro api_get_alunos_por_sala")
        return jsonify({"error": str(e)}), 500


# ROTA: /api/funcionarios (Usada para Professor Responsável)
@ocorrencias_bp.route('/api/funcionarios', methods=['GET'])
def api_get_funcionarios():
    try:
        response = supabase.table('d_funcionarios').select('id, nome, funcao, is_tutor, email').order('nome').execute()
        funcionarios = [{"id": str(f['id']), "nome": f['nome'], "funcao": f.get('funcao', ''), "is_tutor": f.get('is_tutor', False), "email": f.get('email', '')} for f in handle_supabase_response(response)]
        return jsonify(funcionarios)
    except Exception as e:
        return jsonify({"error": f"Erro ao buscar funcionários: {e}", "status": 500}), 500


# ROTA: /api/registrar_ocorrencia
@ocorrencias_bp.route('/api/registrar_ocorrencia', methods=['POST'])
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


# ROTA: /api/ocorrencias_abertas
@ocorrencias_bp.route('/api/ocorrencias_abertas', methods=['GET'])
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


# ROTA: /api/ocorrencia_detalhes
@ocorrencias_bp.route('/api/ocorrencia_detalhes')
def ocorrencia_detalhes():
    numero = request.args.get('numero')
    if not numero:
        return jsonify({'error': 'Número da ocorrência não fornecido'}), 400

    try:
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


# ROTA: /api/registrar_atendimento/<ocorrencia_id>
@ocorrencias_bp.route("/api/registrar_atendimento/<int:ocorrencia_id>", methods=["POST"])
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
        
        supabase.table("ocorrencias").update(update_data).eq("numero", ocorrencia_id).execute()

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


# ROTA: /api/ocorrencias_finalizadas
@ocorrencias_bp.route('/api/ocorrencias_finalizadas', methods=['GET'])
def api_ocorrencias_finalizadas():
    try:
        sala = request.args.get('sala')
        aluno_nome_filtro = request.args.get('aluno') 

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
                    "aluno_id": item.get('aluno_id'), 
                })

        if aluno_nome_filtro:
             finalizadas = [f for f in finalizadas if aluno_nome_filtro.lower() in f['aluno_nome'].lower()]


        return jsonify(finalizadas), 200

    except Exception as e:
        logging.exception("Erro /api/ocorrencias_finalizadas")
        return jsonify({"error": str(e)}), 500


# ROTA: /api/ocorrencias_por_aluno/<aluno_id>
@ocorrencias_bp.route('/api/ocorrencias_por_aluno/<int:aluno_id>')
def ocorrencias_por_aluno(aluno_id):
    try:
        select_query = (
            "numero, data_hora, descricao, status, "
            "atendimento_professor, atendimento_tutor, atendimento_coordenacao, atendimento_gestao, "
            "professor_id(nome), tutor_nome, sala_id(sala), aluno_nome"
        )

        resp = supabase.table('ocorrencias').select(select_query).eq('aluno_id', aluno_id).execute()

        ocorrencias = resp.data or []

        return jsonify(ocorrencias), 200

    except Exception as e:
        logging.exception(f"Erro ao buscar ocorrências do aluno {aluno_id}")
        return jsonify({'error': f'Erro ao consultar Supabase: {str(e)}'}), 500


# ROTA: /api/gerar_pdf_ocorrencias (Mantida a lógica de PDF)
@ocorrencias_bp.route('/api/gerar_pdf_ocorrencias', methods=['POST'])
def gerar_pdf_ocorrencias():
    dados = request.get_json()
    numeros = dados.get('numeros', [])

    if not numeros:
        return jsonify({"error": "Nenhuma ocorrência selecionada"}), 400

    try:
        resp = supabase.table('ocorrencias').select(
            "numero, data_hora, descricao, status, aluno_nome, sala_id, tutor_nome, atendimento_professor, atendimento_tutor, atendimento_coordenacao, atendimento_gestao, impressao_pdf"
        ).in_('numero', numeros).order('data_hora', desc=True).execute()

        ocorrencias = resp.data

        if not ocorrencias:
            return jsonify({"error": "Nenhuma ocorrência encontrada"}), 404

        pdf = FPDF(unit="mm", format="A4")
        pdf.set_margins(left=15, top=15, right=15)
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        w_total = 180 
        x_inicial = 15 

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
        
        pdf.set_fill_color(220, 220, 220) 
        pdf.set_font("Arial", "B", 10)
        pdf.cell(w_total * 0.5, 6, safe_pdf_text(f"Aluno: {aluno_nome}"), border=1, ln=False, fill=True)
        pdf.cell(w_total * 0.25, 6, safe_pdf_text(f"Sala: {sala}"), border=1, ln=False, fill=True)
        pdf.cell(w_total * 0.25, 6, safe_pdf_text(f"Tutor: {tutor}"), border=1, ln=True, fill=True)
        pdf.ln(5)
        
        pdf.set_font("Arial", "", 10)

        # 4. Loop pelas Ocorrências
        for i, o in enumerate(ocorrencias):
            if pdf.get_y() > 260 and i < len(ocorrencias) - 1:
                pdf.add_page()
                pdf.set_font("Arial", "", 10)

            pdf.set_font("Arial", "B", 11)
            pdf.set_text_color(255, 0, 0) 
            pdf.cell(0, 6, safe_pdf_text(f"Registro de Ocorrência nº: {o.get('numero')} - Status: {o.get('status', 'N/A')}"), ln=True)
            pdf.set_text_color(0, 0, 0) 
            
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
            pdf.ln(2) 

            # --- ATENDIMENTOS (Usa multi_cell para quebrar a linha) ---
            
            # ATENDIMENTO PROFESSOR
            professor_atendimento = o.get('atendimento_professor', 'N/A')
            pdf.set_font("Arial", "B", 10)
            pdf.cell(w_total, 5, safe_pdf_text("2. Atendimento Professor/Escolar:"), ln=True)
            pdf.set_font("Arial", "", 10)
            pdf.multi_cell(w=w_total, h=5, txt=safe_pdf_text(professor_atendimento), border=1)
            pdf.ln(2) 

            # ATENDIMENTO TUTOR
            tutor_atendimento = o.get('atendimento_tutor', 'N/A')
            pdf.set_font("Arial", "B", 10)
            pdf.cell(w_total, 5, safe_pdf_text("3. Atendimento Tutor (se realizado):"), ln=True)
            pdf.set_font("Arial", "", 10)
            pdf.multi_cell(w=w_total, h=5, txt=safe_pdf_text(tutor_atendimento), border=1)
            pdf.ln(2) 

            # ATENDIMENTO COORDENAÇÃO
            coordenacao_atendimento = o.get('atendimento_coordenacao', 'N/A')
            pdf.set_font("Arial", "B", 10)
            pdf.cell(w_total, 5, safe_pdf_text("4. Atendimento Coordenação (se realizado):"), ln=True)
            pdf.set_font("Arial", "", 10)
            pdf.multi_cell(w=w_total, h=5, txt=safe_pdf_text(coordenacao_atendimento), border=1)
            pdf.ln(2) 

            # ATENDIMENTO GESTÃO
            gestao_atendimento = o.get('atendimento_gestao', 'N/A')
            pdf.set_font("Arial", "B", 10)
            pdf.cell(w_total, 5, safe_pdf_text("5. Atendimento Gestão (se realizado):"), ln=True)
            pdf.set_font("Arial", "", 10)
            pdf.multi_cell(w=w_total, h=5, txt=safe_pdf_text(gestao_atendimento), border=1)
            pdf.ln(5) 
            
            # Linha separadora entre ocorrências
            if i < len(ocorrencias) - 1:
                pdf.set_draw_color(150, 150, 150) 
                pdf.line(x_inicial, pdf.get_y(), x_inicial + w_total, pdf.get_y())
                pdf.ln(5)


        # 5. Seção de Assinatura (No final da última página)
        pdf.ln(10)
        
        y_assinatura = pdf.get_y()
        w_linha = w_total / 2 - 10 
        
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
        logging.exception(f"Falha fatal ao gerar PDF ou atualizar status de impressão: {str(e)}")
        return jsonify({"error": f"Falha ao gerar PDF: {str(e)}"}), 500


# ROTA: /api/relatorio_estatistico
@ocorrencias_bp.route('/api/relatorio_estatistico', methods=['GET'])
def api_relatorio_estatistico():
    try:
        # 1. Obter todas as ocorrências detalhadas
        resp_occ = supabase.table('ocorrencias').select(
            "numero, data_hora, status, tipo, tutor_id, sala_id, "
            "solicitado_tutor, solicitado_coordenacao, solicitado_gestao, "
            "atendimento_tutor, atendimento_coordenacao, atendimento_gestao, "
            "dt_atendimento_gestao" 
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
        salas_stats = {} 
        tutores_stats = {} 
        tempo_resposta_faixas = {
            '1-7 dias': 0, '8-30 dias': 0, 'mais de 30 dias': 0, 'não finalizadas': 0
        }
        ocorrencias_por_mes = {} 
        
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
        
        final_tutores = []
        for t_id, t_data in tutores_stats.items():
            t_data['media_dias_resposta'] = sum(t_data['tempos_resposta']) / len(t_data['tempos_resposta']) if t_data['tempos_resposta'] else 0
            
            final_tutores.append({
                'tutor': t_data['tutor'],
                'total': t_data['total'],
                'finalizadas': t_data['finalizadas'],
                'abertas': t_data['abertas'],
                'media_dias_resposta': round(t_data['media_dias_resposta'], 1) if t_data['media_dias_resposta'] else 0
            })
            
        tempo_resp_grafico = {
            'labels': list(tempo_resposta_faixas.keys()),
            'valores': list(tempo_resposta_faixas.values())
        }
        
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
        return jsonify({"error": f"Erro interno ao gerar relatório: {e}"}), 500


# ROTA: /api/salas_com_ocorrencias (Usado para filtro em relatórios)
@ocorrencias_bp.route('/api/salas_com_ocorrencias')
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

# ROTA: /api/alunos_com_ocorrencias_por_sala/<sala_id> (Usado para filtro em relatórios)
@ocorrencias_bp.route('/api/alunos_com_ocorrencias_por_sala/<int:sala_id>')
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

# ROTA: /api/relatorio_ocorrencias (Usado para relatório de impressão)
@ocorrencias_bp.route('/api/relatorio_ocorrencias')
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