import os
import logging
from supabase import create_client, Client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Variáveis de ambiente
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# Inicialização simples sem teste de tabela
try:
    if SUPABASE_URL and SUPABASE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Supabase inicializado com sucesso")
    else:
        logger.error("Variáveis de ambiente do Supabase não encontradas")
        supabase = None
except Exception as e:
    logger.error(f"Erro ao inicializar Supabase: {e}")
    supabase = None

def handle_supabase_response(response):
    """Trata a resposta do Supabase"""
    try:
        if hasattr(response, 'error') and response.error:
            raise Exception(f"Erro Supabase: {response.error}")
        return getattr(response, 'data', response)
    except Exception as e:
        logger.error(f"Erro ao processar resposta: {e}")
        raise

# Exportações para evitar erros de importação
__all__ = ['supabase', 'handle_supabase_response', 'SUPABASE_URL', 'SUPABASE_KEY']
