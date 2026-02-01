# -*- coding: utf-8 -*-
"""
Serviço de Chamados - Lógica de negócio
"""
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from config.database import get_connection
from models.chamado import Chamado, Usuario, HistoricoChamado
from utils.logger import logger, audit_logger


def _new_cursor(conn, arraysize: int = 200):
    """Cria cursor com prefetch/arraysize ajustados para reduzir round-trips."""
    cur = conn.cursor()
    try:
        cur.arraysize = arraysize
        cur.prefetchrows = arraysize
    except Exception:
        pass
    return cur


class ChamadoService:
    """Serviço para operações com chamados"""

    @staticmethod
    def carregar_usuario(usuario_wt: str, usuario_bd: str = None) -> Optional[Usuario]:
        """
        Carrega dados do usuário pelo USUARIOWT ou USUARIOBD.

        Args:
            usuario_wt: Nome/matrícula do usuário WinThor
            usuario_bd: Usuário do banco de dados

        Returns:
            Objeto Usuario ou None se não encontrado
        """
        conn = None
        try:
            conn = get_connection()
            cur = conn.cursor()
            row = None

            # Tenta por matrícula
            try:
                mat = int(usuario_wt)
                cur.execute(
                    "SELECT matricula, nome_guerra, codsetor FROM pcempr WHERE matricula = :m",
                    {"m": mat}
                )
                row = cur.fetchone()
            except ValueError:
                pass

            # Tenta por usuário BD
            if not row and usuario_bd:
                cur.execute(
                    "SELECT matricula, nome_guerra, codsetor FROM pcempr WHERE UPPER(usuariobd) = UPPER(:u)",
                    {"u": usuario_bd}
                )
                row = cur.fetchone()

            # Tenta por nome
            if not row:
                cur.execute(
                    "SELECT matricula, nome_guerra, codsetor FROM pcempr WHERE UPPER(nome_guerra) = UPPER(:n)",
                    {"n": usuario_wt}
                )
                row = cur.fetchone()

            cur.close()

            if row:
                usuario = Usuario(
                    matricula=row[0],
                    nome=row[1],
                    codsetor=row[2],
                    usuario_bd=usuario_bd or ""
                )
                audit_logger.log_login(usuario.matricula, usuario.nome, True)
                return usuario

            logger.warning(f"Usuário não encontrado: {usuario_wt}")
            return None

        except Exception as e:
            logger.error(f"Erro ao carregar usuário: {e}")
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def listar_chamados_usuario(
        matricula: int,
        data_inicio: datetime = None,
        data_fim: datetime = None,
        status: str = None
    ) -> List[Chamado]:
        """
        Lista chamados de um usuário específico.

        Args:
            matricula: Matrícula do usuário
            data_inicio: Filtro data inicial
            data_fim: Filtro data final
            status: Filtro de status

        Returns:
            Lista de Chamados
        """
        conn = None
        try:
            conn = get_connection()
            cur = _new_cursor(conn, 500)

            sql = """
                SELECT ID, DATA_ABERTURA, CATEGORIA, PRIORIDADE, STATUS, STATUS_SLA,
                       CAMINHO_IMAGEM, DATA_LIMITE_SLA, SLA_MINUTOS
                FROM PCS_CHAMADOS_TI WHERE MATRICULA = :m
            """
            params = {"m": matricula}

            if data_inicio:
                sql += " AND DATA_ABERTURA >= :dt_ini"
                params["dt_ini"] = data_inicio

            if data_fim:
                sql += " AND DATA_ABERTURA < :dt_fim"
                params["dt_fim"] = data_fim + timedelta(days=1)

            if status and status != "Todos":
                sql += " AND STATUS = :status"
                params["status"] = status

            sql += " ORDER BY DATA_ABERTURA DESC"

            cur.execute(sql, params)
            dados = cur.fetchall()
            cur.close()

            return [Chamado.from_row(row, include_user_info=False) for row in dados]

        except Exception as e:
            logger.error(f"Erro ao listar chamados do usuário {matricula}: {e}")
            return []
        finally:
            if conn:
                conn.close()

    @staticmethod
    def listar_chamados_ti(
        apenas_nao_finalizados: bool = True,
        data_inicio: datetime = None,
        data_fim: datetime = None
    ) -> List[Chamado]:
        """
        Lista chamados para o painel TI.

        Args:
            apenas_nao_finalizados: Se True, filtra apenas não finalizados
            data_inicio: Filtro data inicial
            data_fim: Filtro data final

        Returns:
            Lista de Chamados
        """
        conn = None
        try:
            conn = get_connection()
            cur = _new_cursor(conn, 500)

            sql = """
                SELECT ID, DATA_ABERTURA, NOME_USUARIO, SETOR, CATEGORIA, PRIORIDADE,
                       STATUS, STATUS_SLA, CAMINHO_IMAGEM, DATA_LIMITE_SLA, SLA_MINUTOS, DESCRICAO
                FROM PCS_CHAMADOS_TI WHERE 1=1
            """
            params = {}

            if apenas_nao_finalizados:
                sql += " AND STATUS != 'FINALIZADO'"

            if data_inicio:
                sql += " AND DATA_ABERTURA >= :dt_ini"
                params["dt_ini"] = data_inicio

            if data_fim:
                sql += " AND DATA_ABERTURA < :dt_fim"
                params["dt_fim"] = data_fim + timedelta(days=1)

            sql += " ORDER BY DATA_ABERTURA DESC"

            cur.execute(sql, params)
            dados = cur.fetchall()
            cur.close()

            return [Chamado.from_row(row, include_user_info=True) for row in dados]

        except Exception as e:
            logger.error(f"Erro ao listar chamados TI: {e}")
            return []
        finally:
            if conn:
                conn.close()

    @staticmethod
    def abrir_chamado(
        matricula: int,
        prioridade: str,
        categoria: str,
        descricao: str,
        caminho_imagem: str = None
    ) -> Optional[int]:
        """
        Abre um novo chamado.

        Returns:
            ID do chamado criado ou None em caso de erro
        """
        conn = None
        try:
            conn = get_connection()
            cur = _new_cursor(conn, 200)

            cur.callproc("PRC_ABRIR_CHAMADO", [
                int(matricula), prioridade, categoria, descricao, caminho_imagem
            ])

            cur.execute("""
                SELECT ID FROM PCS_CHAMADOS_TI
                WHERE MATRICULA = :m AND CATEGORIA = :cat AND PRIORIDADE = :prio
                ORDER BY DATA_ABERTURA DESC, ID DESC
                FETCH FIRST 1 ROW ONLY
            """, {"m": matricula, "cat": categoria, "prio": prioridade})

            row = cur.fetchone()
            conn.commit()

            if row:
                audit_logger.log_chamado_aberto(row[0], matricula, categoria)
                return row[0]
            return None

        except Exception as e:
            logger.error(f"Erro ao abrir chamado: {e}")
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def assumir_chamado(id_chamado: int, matricula_analista: int) -> bool:
        """Assume um chamado (analista TI)"""
        conn = None
        try:
            conn = get_connection()
            cur = _new_cursor(conn, 200)
            cur.callproc("PRC_ASSUMIR_CHAMADO", [int(id_chamado), int(matricula_analista)])
            conn.commit()
            audit_logger.log_chamado_assumido(id_chamado, matricula_analista)
            return True
        except Exception as e:
            logger.error(f"Erro ao assumir chamado {id_chamado}: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def resposta_analista(id_chamado: int, matricula: int, resposta: str) -> bool:
        """Adiciona resposta do analista"""
        conn = None
        try:
            conn = get_connection()
            cur = _new_cursor(conn, 200)
            cur.callproc("PRC_RESPOSTA_ANALISTA", [int(id_chamado), int(matricula), resposta])
            conn.commit()
            audit_logger.log_resposta(id_chamado, matricula, "ANALISTA")
            return True
        except Exception as e:
            logger.error(f"Erro ao adicionar resposta analista: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def resposta_usuario(id_chamado: int, matricula: int, resposta: str, finalizar: bool) -> bool:
        """Adiciona resposta do usuário"""
        conn = None
        try:
            conn = get_connection()
            cur = _new_cursor(conn, 200)
            cur.callproc("PRC_RESPOSTA_USUARIO", [int(id_chamado), int(matricula), resposta, finalizar])
            conn.commit()
            tipo = "FINALIZAÇÃO" if finalizar else "USUARIO"
            audit_logger.log_resposta(id_chamado, matricula, tipo)
            if finalizar:
                audit_logger.log_chamado_finalizado(id_chamado, matricula)
            return True
        except Exception as e:
            logger.error(f"Erro ao adicionar resposta usuário: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mover_categoria(id_chamado: int, matricula: int, nova_categoria: str) -> bool:
        """Move chamado para outra categoria"""
        conn = None
        try:
            conn = get_connection()
            cur = _new_cursor(conn, 200)
            cur.callproc("PRC_MOVER_CATEGORIA", [int(id_chamado), int(matricula), nova_categoria])
            conn.commit()
            logger.info(f"Chamado {id_chamado} movido para {nova_categoria}")
            return True
        except Exception as e:
            logger.error(f"Erro ao mover categoria: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mover_prioridade(id_chamado: int, matricula: int, nova_prioridade: str) -> bool:
        """Altera prioridade do chamado"""
        conn = None
        try:
            conn = get_connection()
            cur = _new_cursor(conn, 200)

            cur.execute("""
                UPDATE PCS_CHAMADOS_TI
                SET PRIORIDADE = :prio
                WHERE ID = :id
            """, {"prio": nova_prioridade, "id": id_chamado})

            cur.execute("""
                INSERT INTO PCS_CHAMADOS_TI_HIST (IDHIST, IDCHAMADO, MATRICULA, TIPO, MENSAGEM, DATAHORA)
                VALUES (SEQ_PCS_CHAMADOS_TI_HIST.NEXTVAL, :id, :mat, 'MUDANCA_PRIORIDADE', :msg, SYSDATE)
            """, {"id": id_chamado, "mat": matricula, "msg": f"Prioridade alterada para: {nova_prioridade}"})

            conn.commit()
            logger.info(f"Prioridade do chamado {id_chamado} alterada para {nova_prioridade}")
            return True
        except Exception as e:
            logger.error(f"Erro ao alterar prioridade: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def buscar_historico(id_chamado: int) -> List[HistoricoChamado]:
        """Busca histórico do chamado"""
        conn = None
        try:
            conn = get_connection()
            cur = _new_cursor(conn, 200)
            cur.execute("""
                SELECT DATAHORA, TIPO, MATRICULA, MENSAGEM
                FROM PCS_CHAMADOS_TI_HIST WHERE IDCHAMADO = :id ORDER BY DATAHORA
            """, {"id": id_chamado})
            dados = cur.fetchall()
            cur.close()

            return [
                HistoricoChamado(
                    datahora=row[0],
                    tipo=row[1],
                    matricula=row[2],
                    mensagem=row[3]
                )
                for row in dados
            ]

        except Exception as e:
            logger.error(f"Erro ao buscar histórico: {e}")
            return []
        finally:
            if conn:
                conn.close()

    @staticmethod
    def buscar_anexos(id_chamado: int) -> List[str]:
        """Busca anexos do chamado"""
        anexos = []
        conn = None
        try:
            conn = get_connection()
            cur = _new_cursor(conn, 200)

            # Anexo principal
            cur.execute(
                "SELECT CAMINHO_IMAGEM FROM PCS_CHAMADOS_TI WHERE ID = :id AND CAMINHO_IMAGEM IS NOT NULL",
                {"id": id_chamado}
            )
            row = cur.fetchone()
            if row and row[0]:
                anexos.append(row[0])

            # Anexos adicionais
            try:
                cur.execute(
                    "SELECT CAMINHO FROM PCS_CHAMADOS_TI_ANEXOS WHERE IDCHAMADO = :id ORDER BY DATAHORA",
                    {"id": id_chamado}
                )
                for row in cur.fetchall():
                    if row[0]:
                        anexos.append(row[0])
            except Exception:
                pass

            cur.close()

        except Exception as e:
            logger.error(f"Erro ao buscar anexos: {e}")
        finally:
            if conn:
                conn.close()

        return anexos

    @staticmethod
    def atualizar_anexo(id_chamado: int, matricula: int, caminho: str) -> bool:
        """Atualiza/adiciona anexo ao chamado"""
        conn = None
        try:
            import os
            conn = get_connection()
            cur = _new_cursor(conn, 200)

            cur.execute(
                "UPDATE PCS_CHAMADOS_TI SET CAMINHO_IMAGEM = :caminho WHERE ID = :id",
                {"caminho": caminho, "id": id_chamado}
            )

            cur.execute("""
                INSERT INTO PCS_CHAMADOS_TI_HIST (IDHIST, IDCHAMADO, MATRICULA, TIPO, MENSAGEM, DATAHORA)
                VALUES (SEQ_PCS_CHAMADOS_TI_HIST.NEXTVAL, :id, :mat, 'ANEXO', :msg, SYSDATE)
            """, {"id": id_chamado, "mat": matricula, "msg": f"Anexo: {os.path.basename(caminho)}"})

            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Erro ao atualizar anexo: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def registrar_anexo_adicional(id_chamado: int, matricula: int, caminho: str) -> bool:
        """Registra anexo adicional na tabela de anexos"""
        conn = None
        try:
            import os
            conn = get_connection()
            cur = _new_cursor(conn, 200)

            nome_arquivo = os.path.basename(caminho)

            cur.execute("""
                INSERT INTO PCS_CHAMADOS_TI_ANEXOS (ID, IDCHAMADO, MATRICULA, CAMINHO, NOME_ARQUIVO, DATAHORA)
                VALUES (SEQ_PCS_CHAMADOS_TI_ANEXOS.NEXTVAL, :id, :mat, :caminho, :nome, SYSDATE)
            """, {"id": id_chamado, "mat": matricula, "caminho": caminho, "nome": nome_arquivo})

            cur.execute("""
                INSERT INTO PCS_CHAMADOS_TI_HIST (IDHIST, IDCHAMADO, MATRICULA, TIPO, MENSAGEM, DATAHORA)
                VALUES (SEQ_PCS_CHAMADOS_TI_HIST.NEXTVAL, :id, :mat, 'ANEXO', :msg, SYSDATE)
            """, {"id": id_chamado, "mat": matricula, "msg": f"Anexo adicional: {nome_arquivo}"})

            conn.commit()
            logger.info(f"Anexo adicional registrado: chamado {id_chamado}, arquivo {nome_arquivo}")
            return True
        except Exception as e:
            logger.error(f"Erro ao registrar anexo adicional: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def top_usuarios_chamados(limit: int = 10) -> List[Tuple[str, int]]:
        """
        Retorna top usuários com mais chamados (para painel gerência).

        Returns:
            Lista de tuplas (nome_usuario, quantidade)
        """
        conn = None
        try:
            conn = get_connection()
            cur = _new_cursor(conn, 100)

            cur.execute(f"""
                SELECT NOME_USUARIO, COUNT(*) as QTD
                FROM PCS_CHAMADOS_TI
                WHERE DATA_ABERTURA >= ADD_MONTHS(SYSDATE, -3)
                GROUP BY NOME_USUARIO
                ORDER BY QTD DESC
                FETCH FIRST {limit} ROWS ONLY
            """)

            dados = cur.fetchall()
            cur.close()
            return [(row[0], row[1]) for row in dados]

        except Exception as e:
            logger.error(f"Erro ao buscar top usuários: {e}")
            return []
        finally:
            if conn:
                conn.close()
