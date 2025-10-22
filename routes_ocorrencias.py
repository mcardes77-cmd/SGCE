# routes_ocorrencias.py - ATUALIZADO
from flask import Blueprint, request, jsonify, send_file
from datetime import datetime
import logging
import json
from db_utils import get_supabase, handle_supabase_response
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
import os

ocorrencias_bp = Blueprint('ocorrencias', __name__)

# =========================================================
# ROTAS AUXILIARES PARA FORMULÁRIO DE OCORRÊNCIA
# =========================================================

@ocorrencias_bp.route('/api/ocorrencias/salas', methods=['GET'])
def api_get_salas_ocorrencias():
    """Busca salas para o formulário de ocorrências"""
    try:
        supabase = get_supabase()
        response = supabase.table('d_salas').select('id, sala').order('sala').execute()
        salas = response.data if response.data else []
        return jsonify(salas), 200
    except Exception as e:
        logging.error(f"Erro /api/ocorrencias/salas: {str(e)}")
        return jsonify({"error": f"Falha ao buscar salas: {str(e)}"}), 500

@ocorrencias_bp.route('/api/salas_com_ocorrencias', methods=['GET'])
def api_get_salas_com_ocorrencias():
    """Busca salas que possuem ocorrências"""
    try:
        supabase = get_supabase()
        response = supabase.table('d_salas').select('id, sala').order('sala').execute()
        salas = response.data if response.data else []
        return jsonify(salas), 200
    except Exception as e:
        logging.error(f"Erro /api/salas_com_ocorrencias: {str(e)}")
        return jsonify({"error": f"Falha ao buscar salas: {str(e)}"}), 500

@ocorrencias_bp.route('/api/alunos_com_ocorrencias_por_sala/<int:sala_id>', methods=['GET'])
def api_get_alunos_com_ocorrencias_por_sala(sala_id):
    """Busca alunos por sala que possuem ocorrências"""
    try:
        supabase = get_supabase()
        
        # Busca alunos da sala
        response = supabase.table('d_alunos').select(
            'id, nome, tutor_id'
        ).eq('sala_id', sala_id).order('nome').execute()
        
        alunos = response.data if response.data else []
        
        # Verifica quais alunos têm ocorrências
        alunos_com_ocorrencias = []
        for aluno in alunos:
            # Verifica se o aluno tem ocorrências
            ocorrencias_response = supabase.table('ocorrencias').select('id').eq('aluno_id', aluno['id']).limit(1).execute()
            if ocorrencias_response.data:
                alunos_com_ocorrencias.append(aluno)
        
        return jsonify(alunos_com_ocorrencias), 200
        
    except Exception as e:
        logging.error(f"Erro /api/alunos_com_ocorrencias_por_sala: {str(e)}")
        return jsonify({"error": f"Falha ao buscar alunos: {str(e)}"}), 500

@ocorrencias_bp.route('/api/ocorrencias_por_aluno/<int:aluno_id>', methods=['GET'])
def api_get_ocorrencias_por_aluno(aluno_id):
    """Busca ocorrências de um aluno específico"""
    try:
        supabase = get_supabase()
        response = supabase.table('ocorrencias').select('*').eq('aluno_id', aluno_id).order('data_hora', desc=True).execute()
        ocorrencias = response.data if response.data else []
        return jsonify(ocorrencias), 200
    except Exception as e:
        logging.error(f"Erro /api/ocorrencias_por_aluno: {str(e)}")
        return jsonify({"error": f"Falha ao buscar ocorrências do aluno: {str(e)}"}), 500

@ocorrencias_bp.route('/api/ocorrencias/tutor_por_aluno/<int:aluno_id>', methods=['GET'])
def api_get_tutor_por_aluno(aluno_id):
    """Busca informações do tutor por aluno"""
    try:
        supabase = get_supabase()
        
        # Busca aluno com informações do tutor
        response = supabase.table('d_alunos').select(
            'id, nome, tutor_id, d_funcionarios!d_alunos_tutor_id_fkey(id, nome)'
        ).eq('id', aluno_id).single().execute()
        
        if not response.data:
            return jsonify({"error": "Aluno não encontrado"}), 404
            
        aluno = response.data
        tutor_info = {
            "tutor_id": aluno['tutor_id'],
            "tutor_nome": aluno.get('d_funcionarios', {}).get('nome', '') if aluno.get('d_funcionarios') else '',
            "aluno_id": aluno['id'],
            "aluno_nome": aluno['nome']
        }
        
        return jsonify(tutor_info), 200
        
    except Exception as e:
        logging.error(f"Erro /api/ocorrencias/tutor_por_aluno: {str(e)}")
        return jsonify({"error": f"Falha ao buscar tutor do aluno: {str(e)}"}), 500

@ocorrencias_bp.route('/api/ocorrencias/professores', methods=['GET'])
def api_get_professores_ocorrencias():
    """Busca professores para ocorrências"""
    try:
        supabase = get_supabase()
        response = supabase.table('d_funcionarios').select('id, nome').order('nome').execute()
        professores = response.data if response.data else []
        return jsonify(professores), 200
    except Exception as e:
        logging.error(f"Erro /api/ocorrencias/professores: {str(e)}")
        return jsonify({"error": f"Falha ao buscar professores: {str(e)}"}), 500

# =========================================================
# ROTAS PRINCIPAIS DE OCORRÊNCIAS
# =========================================================

@ocorrencias_bp.route('/api/ocorrencias', methods=['GET'])
def api_get_ocorrencias():
    """Busca todas as ocorrências"""
    try:
        supabase = get_supabase()
        response = supabase.table('ocorrencias').select('*').order('data_hora', desc=True).execute()
        ocorrencias = response.data if response.data else []
        return jsonify(ocorrencias), 200
    except Exception as e:
        logging.error(f"Erro /api/ocorrencias: {str(e)}")
        return jsonify({"error": f"Falha ao buscar ocorrências: {str(e)}"}), 500

@ocorrencias_bp.route('/api/ocorrencias/abertas', methods=['GET'])
def api_get_ocorrencias_abertas():
    """Busca ocorrências em aberto"""
    try:
        supabase = get_supabase()
        response = supabase.table('ocorrencias').select('*').in_('status', ['AGUARDANDO ATENDIMENTO', 'EM ANDAMENTO']).order('data_hora', desc=True).execute()
        ocorrencias = response.data if response.data else []
        return jsonify(ocorrencias), 200
    except Exception as e:
        logging.error(f"Erro /api/ocorrencias/abertas: {str(e)}")
        return jsonify({"error": f"Falha ao buscar ocorrências abertas: {str(e)}"}), 500

@ocorrencias_bp.route('/api/ocorrencias/finalizadas', methods=['GET'])
def api_get_ocorrencias_finalizadas():
    """Busca ocorrências finalizadas"""
    try:
        supabase = get_supabase()
        response = supabase.table('ocorrencias').select('*').eq('status', 'FINALIZADA').order('data_hora', desc=True).execute()
        ocorrencias = response.data if response.data else []
        return jsonify(ocorrencias), 200
    except Exception as e:
        logging.error(f"Erro /api/ocorrencias/finalizadas: {str(e)}")
        return jsonify({"error": f"Falha ao buscar ocorrências finalizadas: {str(e)}"}), 500

@ocorrencias_bp.route('/api/ocorrencias', methods=['POST'])
def api_criar_ocorrencia():
    """Cria uma nova ocorrência"""
    data = request.json
    
    required_fields = ['descricao', 'aluno_id', 'tipo']
    missing = [field for field in required_fields if not data.get(field)]
    if missing:
        return jsonify({"error": f"Campos obrigatórios ausentes: {', '.join(missing)}"}), 400

    try:
        supabase = get_supabase()
        
        # Buscar próximo número de ocorrência
        max_response = supabase.table('ocorrencias').select('numero').order('numero', desc=True).limit(1).execute()
        max_numero = max_response.data[0]['numero'] + 1 if max_response.data and len(max_response.data) > 0 else 1
        
        ocorrencia_data = {
            "numero": max_numero,
            "descricao": data['descricao'],
            "tipo": data['tipo'],
            "aluno_id": data['aluno_id'],
            "aluno_nome": data.get('aluno_nome'),
            "tutor_id": data.get('tutor_id'),
            "professor_id": data.get('professor_id'),
            "sala_id": data.get('sala_id'),
            "atendimento_professor": data.get('atendimento_professor'),
            "solicitado_tutor": data.get('solicitado_tutor', 'NÃO'),
            "solicitado_coordenacao": data.get('solicitado_coordenacao', 'NÃO'),
            "solicitado_gestao": data.get('solicitado_gestao', 'NÃO'),
            "status": "AGUARDANDO ATENDIMENTO",
            "assinada": "NÃO",
            "impressao_pdf": "NÃO",  # Campo novo para controlar impressão
            "data_hora": datetime.now().isoformat()
        }
        
        response = supabase.table('ocorrencias').insert(ocorrencia_data).execute()
        
        if response.data:
            return jsonify({
                "message": "Ocorrência criada com sucesso",
                "numero": max_numero
            }), 201
        else:
            return jsonify({"error": "Falha ao criar ocorrência"}), 500

    except Exception as e:
        logging.error(f"Erro /api/ocorrencias POST: {str(e)}")
        return jsonify({"error": f"Falha ao criar ocorrência: {str(e)}"}), 500

@ocorrencias_bp.route('/api/ocorrencias/<int:ocorrencia_numero>', methods=['PUT'])
def api_atualizar_ocorrencia(ocorrencia_numero):
    """Atualiza uma ocorrência existente"""
    data = request.json
    
    try:
        supabase = get_supabase()
        
        update_data = {}
        campos_permitidos = [
            'descricao', 'tipo', 'status', 'atendimento_professor', 
            'atendimento_tutor', 'atendimento_coordenacao', 'atendimento_gestao',
            'solicitado_tutor', 'solicitado_coordenacao', 'solicitado_gestao',
            'dt_atendimento_tutor', 'dt_atendimento_coordenacao', 'dt_atendimento_gestao',
            'assinada', 'impressao_pdf'
        ]
        
        for campo in campos_permitidos:
            if campo in data:
                update_data[campo] = data[campo]
        
        if not update_data:
            return jsonify({"error": "Nenhum campo válido para atualização"}), 400
        
        response = supabase.table('ocorrencias').update(update_data).eq('numero', ocorrencia_numero).execute()
        
        if response.data:
            return jsonify({"message": "Ocorrência atualizada com sucesso"}), 200
        else:
            return jsonify({"error": "Falha ao atualizar ocorrência"}), 500

    except Exception as e:
        logging.error(f"Erro /api/ocorrencias PUT: {str(e)}")
        return jsonify({"error": f"Falha ao atualizar ocorrência: {str(e)}"}), 500

@ocorrencias_bp.route('/api/ocorrencias/<int:ocorrencia_numero>', methods=['GET'])
def api_get_ocorrencia(ocorrencia_numero):
    """Busca uma ocorrência específica"""
    try:
        supabase = get_supabase()
        response = supabase.table('ocorrencias').select('*').eq('numero', ocorrencia_numero).single().execute()
        
        if response.data:
            return jsonify(response.data), 200
        else:
            return jsonify({"error": "Ocorrência não encontrada"}), 404

    except Exception as e:
        logging.error(f"Erro /api/ocorrencias GET: {str(e)}")
        return jsonify({"error": f"Falha ao buscar ocorrência: {str(e)}"}), 500

# =========================================================
# ROTAS PARA IMPRESSÃO DE OCORRÊNCIAS
# =========================================================

@ocorrencias_bp.route('/api/gerar_pdf_ocorrencias', methods=['POST'])
def api_gerar_pdf_ocorrencias():
    """Gera PDF para múltiplas ocorrências selecionadas"""
    data = request.json
    
    if not data.get('numeros') or not isinstance(data['numeros'], list):
        return jsonify({"error": "Lista de números de ocorrência é obrigatória"}), 400

    try:
        ocorrencias_numeros = data['numeros']
        supabase = get_supabase()
        
        # Busca dados das ocorrências
        response = supabase.table('ocorrencias').select('*').in_('numero', ocorrencias_numeros).execute()
        
        if not response.data:
            return jsonify({"error": "Nenhuma ocorrência encontrada"}), 404
            
        ocorrencias = response.data
        
        # Busca informações do aluno (primeira ocorrência)
        aluno_id = ocorrencias[0]['aluno_id']
        aluno_response = supabase.table('d_alunos').select('nome').eq('id', aluno_id).single().execute()
        aluno_nome = aluno_response.data['nome'] if aluno_response.data else "Aluno Desconhecido"
        
        # Cria PDF com múltiplas ocorrências
        pdf_buffer = criar_pdf_multiplas_ocorrencias(ocorrencias, aluno_nome)
        
        # Marca todas como impressas no banco de dados
        for numero in ocorrencias_numeros:
            supabase.table('ocorrencias').update({
                "impressao_pdf": "SIM",
                "data_impressao": datetime.now().isoformat()
            }).eq('numero', numero).execute()
        
        # Retorna o PDF
        pdf_buffer.seek(0)
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=f"ocorrencias_{aluno_nome.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mimetype='application/pdf'
        )

    except Exception as e:
        logging.error(f"Erro /api/gerar_pdf_ocorrencias: {str(e)}")
        return jsonify({"error": f"Falha ao gerar PDF: {str(e)}"}), 500

def criar_pdf_multiplas_ocorrencias(ocorrencias, aluno_nome):
    """Cria PDF para múltiplas ocorrências"""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    for i, ocorrencia in enumerate(ocorrencias):
        if i > 0:  # Nova página para cada ocorrência (exceto a primeira)
            c.showPage()
        
        margin = 20 * mm
        current_y = height - margin
        
        # Cabeçalho
        c.setFont("Helvetica-Bold", 16)
        c.drawString(margin, current_y, "REGISTRO DE OCORRÊNCIA ESCOLAR")
        current_y -= 8 * mm
        
        c.setFont("Helvetica", 10)
        c.drawString(margin, current_y, f"Aluno: {aluno_nome}")
        current_y -= 5 * mm
        
        # Linha separadora
        c.line(margin, current_y, width - margin, current_y)
        current_y -= 10 * mm
        
        # Dados da ocorrência
        c.setFont("Helvetica-Bold", 10)
        
        dados = [
            (f"Número da Ocorrência: {ocorrencia['numero']}", f"Data: {formatar_data_hora(ocorrencia['data_hora'])}"),
            (f"Tipo: {ocorrencia['tipo']}", f"Status: {ocorrencia['status']}"),
            ("", ""),
            ("Descrição da Ocorrência:", "")
        ]
        
        for linha in dados:
            if linha[0]:
                c.drawString(margin, current_y, linha[0])
            if linha[1]:
                c.drawString(width/2, current_y, linha[1])
            current_y -= 6 * mm
        
        # Descrição
        c.setFont("Helvetica", 10)
        descricao = ocorrencia['descricao']
        descricao_lines = quebrar_texto(c, descricao, width - 2 * margin - 20 * mm, 10)
        
        for line in descricao_lines:
            if current_y < margin + 50:
                c.showPage()
                current_y = height - margin
                c.setFont("Helvetica", 10)
            
            c.drawString(margin + 10 * mm, current_y, line)
            current_y -= 4 * mm
        
        # Informações adicionais
        current_y -= 5 * mm
        c.setFont("Helvetica-Bold", 10)
        c.drawString(margin, current_y, "Encaminhamentos:")
        current_y -= 5 * mm
        
        c.setFont("Helvetica", 10)
        encaminhamentos = []
        if ocorrencia.get('solicitado_tutor') == 'SIM':
            encaminhamentos.append("• Tutor")
        if ocorrencia.get('solicitado_coordenacao') == 'SIM':
            encaminhamentos.append("• Coordenação")
        if ocorrencia.get('solicitado_gestao') == 'SIM':
            encaminhamentos.append("• Gestão")
        
        if encaminhamentos:
            for enc in encaminhamentos:
                if current_y < margin + 30:
                    c.showPage()
                    current_y = height - margin
                    c.setFont("Helvetica", 10)
                c.drawString(margin + 10 * mm, current_y, enc)
                current_y -= 4 * mm
        else:
            c.drawString(margin + 10 * mm, current_y, "• Nenhum encaminhamento solicitado")
            current_y -= 4 * mm
        
        # Rodapé com assinatura
        current_y = margin + 40 * mm
        c.line(margin, current_y, width - margin, current_y)
        current_y -= 10 * mm
        
        c.drawString(margin, current_y, "Assinatura do Responsável: _________________________")
        current_y -= 5 * mm
        c.drawString(margin, current_y, "Data: ___/___/_______")
        current_y -= 5 * mm
        c.drawString(margin, current_y, "Observações: ______________________________________")
    
    c.save()
    return buffer

def quebrar_texto(canvas, texto, max_width, font_size):
    """Quebra texto em múltiplas linhas baseado na largura máxima"""
    words = texto.split()
    lines = []
    current_line = ""
    
    for word in words:
        test_line = current_line + word + " "
        if canvas.stringWidth(test_line, "Helvetica", font_size) <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line.strip())
            current_line = word + " "
    
    if current_line:
        lines.append(current_line.strip())
    
    return lines

def formatar_data_hora(data_hora_str):
    """Formata data/hora para exibição"""
    try:
        if data_hora_str:
            dt = datetime.fromisoformat(data_hora_str.replace('Z', '+00:00'))
            return dt.strftime('%d/%m/%Y %H:%M')
    except:
        pass
    return data_hora_str

# =========================================================
# ROTAS PARA DADOS AUXILIARES
# =========================================================

@ocorrencias_bp.route('/api/ocorrencias/tipos', methods=['GET'])
def api_get_tipos_ocorrencia():
    """Retorna os tipos de ocorrência"""
    tipos = [
        {"value": "COMPORTAMENTO", "label": "Comportamento"},
        {"value": "DESEMPENHO", "label": "Desempenho Acadêmico"},
        {"value": "FREQUENCIA", "label": "Frequência"},
        {"value": "CONVIVENCIA", "label": "Convivência"},
        {"value": "OUTROS", "label": "Outros"}
    ]
    return jsonify(tipos), 200

@ocorrencias_bp.route('/api/ocorrencias/status', methods=['GET'])
def api_get_status_ocorrencia():
    """Retorna os status disponíveis"""
    status = [
        {"value": "AGUARDANDO ATENDIMENTO", "label": "Aguardando Atendimento"},
        {"value": "EM ANDAMENTO", "label": "Em Andamento"},
        {"value": "FINALIZADA", "label": "Finalizada"}
    ]
    return jsonify(status), 200
