import os
import logging
import time
from datetime import datetime
from typing import Optional
from supabase import create_client, Client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Variáveis de ambiente
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

# Log das variáveis
if not SUPABASE_URL:
    logger.warning("SUPABASE_URL não encontrada nas variáveis de ambiente.")
if not SUPABASE_KEY:
    logger.warning("SUPABASE_KEY não encontrada nas variáveis de ambiente.")

_supabase_client: Optional[Client] = None

def _init_supabase_client(retries: int = 3, backoff: float = 1.0) -> Optional[Client]:
    global _supabase_client
    if _supabase_client:
        return _supabase_client

    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("Não é possível inicializar Supabase: SUPABASE_URL ou SUPABASE_KEY ausentes.")
        return None

    for attempt in range(1, retries + 1):
        try:
            logger.info(f"Tentando inicializar Supabase (tentativa {attempt}/{retries})...")
            _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
            
            # Testa a conexão com a tabela CORRETA d_funcionarios
            try:
                _supabase_client.table('d_funcionarios').select('*').limit(1).execute()
                logger.info("Conexão Supabase inicializada e testada com sucesso.")
            except Exception as test_error:
                logger.warning(f"Conexão estabelecida, mas teste falhou: {test_error}")
            
            return _supabase_client
        except Exception as e:
            logger.error(f"Falha ao criar client Supabase (tentativa {attempt}): {e}")
            if attempt < retries:
                time.sleep(backoff * attempt)
            else:
                logger.error("Não foi possível inicializar Supabase após várias tentativas.")
                return None

def get_supabase() -> Optional[Client]:
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = _init_supabase_client()
    return _supabase_client

# Instância global para compatibilidade
supabase = get_supabase()

def handle_supabase_response(response):
    try:
        if response is None:
            raise Exception("Resposta Supabase é None.")
        if isinstance(response, dict):
            if response.get("error"):
                raise Exception(f"Erro Postgrest: {response['error']}")
            return response.get("data", response)
        if hasattr(response, "error") and response.error:
            raise Exception(f"Erro Postgrest: {response.error}")
        if hasattr(response, "data"):
            return response.data
        return response
    except Exception:
        logger.exception("Erro ao tratar resposta Supabase.")
        raise

# ========== FUNÇÕES AUXILIARES PARA OCORRÊNCIAS ==========

DEFAULT_AUTOTEXT = "Não solicitado"

def _to_bool(value):
    """Converte vários formatos para booleano"""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes', 'sim', 's', 'y')
    return False

def formatar_data_hora(data_hora_str):
    """Formata data/hora para exibição"""
    if not data_hora_str:
        return ""
    try:
        dt = datetime.fromisoformat(data_hora_str.replace('Z', '+00:00'))
        return dt.strftime("%d/%m/%Y %H:%M")
    except:
        return data_hora_str

def calcular_dias_resposta(data_abertura, data_atendimento):
    """Calcula dias entre abertura e atendimento"""
    if not data_abertura or not data_atendimento:
        return None
    try:
        dt_abertura = datetime.fromisoformat(data_abertura.replace('Z', '+00:00'))
        dt_atendimento = datetime.fromisoformat(data_atendimento.replace('Z', '+00:00'))
        return (dt_atendimento - dt_abertura).days
    except:
        return None

def safe_pdf_text(texto):
    """Remove caracteres problemáticos para PDF"""
    if not texto:
        return ""
    return str(texto).replace('°', 'º').replace('ª', 'a').replace('º', 'o')

def get_alunos_por_sala_data(sala_id):
    """Busca alunos por sala com dados do tutor"""
    try:
        supabase = get_supabase()
        if not supabase:
            return []
            
        response = supabase.table('d_alunos').select(
            'id, nome, tutor_id, d_funcionarios!d_alunos_tutor_id_fkey(nome)'
        ).eq('sala_id', sala_id).execute()
        
        alunos = []
        for aluno in handle_supabase_response(response):
            alunos.append({
                'id': aluno['id'],
                'nome': aluno['nome'],
                'tutor_id': aluno.get('tutor_id'),
                'tutor_nome': aluno.get('d_funcionarios', [{}])[0].get('nome', 'Tutor Não Definido')
            })
        return alunos
    except Exception as e:
        logger.error(f"Erro ao buscar alunos da sala {sala_id}: {e}")
        return []

__all__ = [
    'supabase', 'get_supabase', 'handle_supabase_response', 
    'DEFAULT_AUTOTEXT', '_to_bool', 'formatar_data_hora', 
    'calcular_dias_resposta', 'safe_pdf_text', 'get_alunos_por_sala_data'
]

# ... código existente ...

# ========== FUNÇÕES AUXILIARES PARA TECNOLOGIA ==========

def get_equipamentos_por_sala(sala_id):
    """Busca equipamentos em uso por sala"""
    try:
        supabase = get_supabase()
        if not supabase:
            return []
            
        response = supabase.table('d_inventario_equipamentos').select(
            'id, colmeia, equipamento_id, status, aluno_id, d_alunos(nome, sala_id)'
        ).eq('d_alunos.sala_id', sala_id).eq('status', 'EM USO').execute()
        
        equipamentos = []
        for eq in handle_supabase_response(response):
            equipamentos.append({
                'id': eq['id'],
                'colmeia': eq['colmeia'],
                'equipamento_id': eq['equipamento_id'],
                'status': eq['status'],
                'aluno_nome': eq.get('d_alunos', [{}])[0].get('nome', 'N/A') if eq.get('d_alunos') else 'N/A'
            })
        return equipamentos
    except Exception as e:
        logger.error(f"Erro ao buscar equipamentos da sala {sala_id}: {e}")
        return []

def get_equipamentos_disponiveis():
    """Busca equipamentos disponíveis para reserva"""
    try:
        supabase = get_supabase()
        if not supabase:
            return []
            
        response = supabase.table('d_inventario_equipamentos').select(
            'id, colmeia, equipamento_id'
        ).eq('status', 'DISPONÍVEL').order('colmeia', 'equipamento_id').execute()
        
        return handle_supabase_response(response)
    except Exception as e:
        logger.error(f"Erro ao buscar equipamentos disponíveis: {e}")
        return []

# Atualizar o __all__
__all__ = [
    'supabase', 'get_supabase', 'handle_supabase_response', 
    'DEFAULT_AUTOTEXT', '_to_bool', 'formatar_data_hora', 
    'calcular_dias_resposta', 'safe_pdf_text', 'get_alunos_por_sala_data',
    'get_equipamentos_por_sala', 'get_equipamentos_disponiveis'  # ADICIONAR
]