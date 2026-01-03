"""
Módulo de backup e redundância em tempo real para operações críticas do CRM FinanFlow.
Registra todas as operações de modificação (CREATE, UPDATE, DELETE) em arquivo JSON Lines.
"""

import json
import threading
from datetime import datetime
from functools import wraps
from flask import request, session
import os

# Lock para garantir thread-safety na escrita do arquivo
_file_lock = threading.Lock()
BACKUP_FILE = 'finanflow_backup.jsonl'


def _write_log_entry(log_data: dict):
    """
    Função thread-safe para escrever uma entrada de log no arquivo JSON Lines.
    
    Args:
        log_data: Dicionário contendo os dados do log (timestamp, user_id, action, entity, changes)
    
    Raises:
        Exception: Qualquer erro na escrita é capturado e suprimido para não travar a aplicação
    """
    try:
        with _file_lock:
            # Garantir que o diretório existe
            backup_dir = os.path.dirname(BACKUP_FILE) if os.path.dirname(BACKUP_FILE) else '.'
            if backup_dir and not os.path.exists(backup_dir):
                os.makedirs(backup_dir, exist_ok=True)
            
            # Abrir arquivo em modo append ('a') para nunca sobrescrever histórico
            with open(BACKUP_FILE, 'a', encoding='utf-8') as f:
                # Escrever uma linha JSON por vez (formato JSON Lines)
                f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
                f.flush()  # Garantir que os dados são escritos imediatamente
    except Exception as e:
        # Suprimir exceções para não travar a aplicação principal
        # Em produção, você pode querer logar isso em um sistema de monitoramento
        print(f"ERRO ao escrever log de backup: {str(e)}")


def _determine_action(method: str) -> str:
    """
    Determina a ação baseada no método HTTP.
    
    Args:
        method: Método HTTP (POST, PUT, PATCH, DELETE)
    
    Returns:
        String com a ação: 'CREATE', 'UPDATE' ou 'DELETE'
    """
    method_upper = method.upper()
    if method_upper == 'POST':
        return 'CREATE'
    elif method_upper in ('PUT', 'PATCH'):
        return 'UPDATE'
    elif method_upper == 'DELETE':
        return 'DELETE'
    else:
        return 'UNKNOWN'


def _determine_entity(route: str, function_name: str) -> str:
    """
    Determina a entidade baseada na rota ou nome da função.
    
    Args:
        route: Rota Flask (ex: '/cliente/123/editar')
        function_name: Nome da função (ex: 'editar_cliente')
    
    Returns:
        String com o nome da entidade: 'Cliente', 'Cobrança', 'Usuário', etc.
    """
    route_lower = route.lower()
    func_lower = function_name.lower()
    
    if 'cliente' in route_lower or 'cliente' in func_lower:
        return 'Cliente'
    elif 'cobranca' in route_lower or 'cobranca' in func_lower:
        return 'Cobrança'
    elif 'usuario' in route_lower or 'usuario' in func_lower:
        return 'Usuário'
    elif 'parcela' in route_lower or 'parcela' in func_lower:
        return 'Parcela'
    elif 'pagamento' in route_lower or 'pagamento' in func_lower:
        return 'Pagamento'
    else:
        return 'Desconhecido'


def _extract_changes(request_obj, entity_id=None):
    """
    Extrai os dados de mudança do request.
    
    Args:
        request_obj: Objeto request do Flask
        entity_id: ID da entidade (se disponível)
    
    Returns:
        Dicionário com os dados alterados
    """
    changes = {}
    
    # Capturar dados do formulário (form)
    if request_obj.form:
        # Converter ImmutableMultiDict para dict normal
        form_dict = dict(request_obj.form)
        # Remover senhas por segurança
        if 'senha' in form_dict:
            form_dict['senha'] = '[REDACTED]'
        changes.update(form_dict)
    
    # Capturar dados JSON (se houver)
    if request_obj.is_json and request_obj.json:
        json_data = request_obj.json.copy()
        # Remover senhas por segurança
        if 'senha' in json_data:
            json_data['senha'] = '[REDACTED]'
        changes.update(json_data)
    
    # Adicionar ID da entidade se disponível
    if entity_id:
        changes['entity_id'] = entity_id
    
    return changes


def audit_log(entity_name=None):
    """
    Decorator para registrar automaticamente operações críticas no arquivo de backup.
    
    Uso:
        @app.route('/cliente/adicionar', methods=['POST'])
        @login_required
        @audit_log(entity_name='Cliente')
        def adicionar_cliente():
            ...
    
    Args:
        entity_name: Nome opcional da entidade. Se não fornecido, será inferido da rota/função.
    
    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Executar a função original primeiro
            result = func(*args, **kwargs)
            
            # Verificar se é uma operação de modificação (não GET)
            if request.method not in ('POST', 'PUT', 'PATCH', 'DELETE'):
                return result
            
            # Verificar se a operação foi bem-sucedida
            # Assumimos sucesso se não houve exceção e o resultado não é um erro
            # Para Flask, redirections e renderizações indicam sucesso
            try:
                # Obter user_id da sessão
                user_id = session.get('usuario_id')
                if not user_id:
                    # Se não houver usuário logado, não registrar
                    return result
                
                # Determinar ação
                action = _determine_action(request.method)
                
                # Determinar entidade
                if entity_name:
                    entity = entity_name
                else:
                    entity = _determine_entity(request.path, func.__name__)
                
                # Extrair ID da entidade dos argumentos ou kwargs
                entity_id = None
                # Procurar por padrões comuns: cliente_id, cobranca_id, usuario_id, id
                for key in ['cliente_id', 'cobranca_id', 'usuario_id', 'id']:
                    if key in kwargs:
                        entity_id = kwargs[key]
                        break
                    # Também verificar nos args (posição comum)
                    if args:
                        # Para rotas como /cliente/<int:cliente_id>, o ID geralmente é o primeiro arg
                        if len(args) > 0 and isinstance(args[0], int):
                            entity_id = args[0]
                            break
                
                # Extrair mudanças
                changes = _extract_changes(request, entity_id)
                
                # Criar entrada de log
                log_entry = {
                    'timestamp': datetime.now().isoformat(),
                    'user_id': user_id,
                    'action': action,
                    'entity': entity,
                    'changes': changes,
                    'route': request.path,
                    'method': request.method
                }
                
                # Registrar de forma assíncrona (thread-safe)
                _write_log_entry(log_entry)
                
            except Exception as e:
                # Suprimir qualquer erro no logging para não afetar a operação principal
                print(f"ERRO ao processar audit_log: {str(e)}")
            
            return result
        
        return wrapper
    return decorator

