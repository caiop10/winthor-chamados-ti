# -*- coding: utf-8 -*-
"""
Script para criar estrutura de notificações no Oracle
Execute uma vez para configurar tabela, sequência e triggers
"""
from config.database import get_connection
from utils.logger import logger

def criar_estrutura_notificacoes():
    """Cria tabela, sequência e triggers de notificações"""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()

        print("=" * 60)
        print("CONFIGURAÇÃO DE NOTIFICAÇÕES")
        print("=" * 60)

        # 1. Criar sequência
        print("\n[1] Criando sequência SEQ_PCS_CHAMADOS_TI_NOTIF...")
        try:
            cur.execute("CREATE SEQUENCE SEQ_PCS_CHAMADOS_TI_NOTIF START WITH 1 INCREMENT BY 1")
            print("    OK - Sequência criada")
        except Exception as e:
            if "ORA-00955" in str(e):
                print("    OK - Sequência já existe")
            else:
                print(f"    ERRO: {e}")

        # 2. Criar tabela de notificações
        print("\n[2] Criando tabela PCS_CHAMADOS_TI_NOTIF...")
        try:
            cur.execute("""
                CREATE TABLE PCS_CHAMADOS_TI_NOTIF (
                    ID NUMBER PRIMARY KEY,
                    MATRICULA_DESTINO NUMBER NOT NULL,
                    ID_CHAMADO NUMBER NOT NULL,
                    TIPO VARCHAR2(50) NOT NULL,
                    TITULO VARCHAR2(200) NOT NULL,
                    MENSAGEM VARCHAR2(500),
                    DATAHORA DATE DEFAULT SYSDATE NOT NULL,
                    LIDA CHAR(1) DEFAULT 'N' NOT NULL,
                    DATA_LEITURA DATE,
                    CONSTRAINT CHK_NOTIF_LIDA CHECK (LIDA IN ('S', 'N'))
                )
            """)
            print("    OK - Tabela criada")
        except Exception as e:
            if "ORA-00955" in str(e):
                print("    OK - Tabela já existe")
            else:
                print(f"    ERRO: {e}")

        # 3. Criar índices
        print("\n[3] Criando índices...")
        indices = [
            ("IDX_NOTIF_MATRICULA", "PCS_CHAMADOS_TI_NOTIF(MATRICULA_DESTINO, LIDA)"),
            ("IDX_NOTIF_CHAMADO", "PCS_CHAMADOS_TI_NOTIF(ID_CHAMADO)"),
            ("IDX_NOTIF_DATAHORA", "PCS_CHAMADOS_TI_NOTIF(DATAHORA DESC)")
        ]
        for nome, definicao in indices:
            try:
                cur.execute(f"CREATE INDEX {nome} ON {definicao}")
                print(f"    OK - {nome}")
            except Exception as e:
                if "ORA-00955" in str(e) or "ORA-01408" in str(e):
                    print(f"    OK - {nome} já existe")
                else:
                    print(f"    ERRO {nome}: {e}")

        # 4. Criar trigger para NOVO CHAMADO -> notifica analistas TI (codsetor = 10)
        print("\n[4] Criando trigger TRG_NOTIF_NOVO_CHAMADO...")
        try:
            cur.execute("DROP TRIGGER TRG_NOTIF_NOVO_CHAMADO")
        except:
            pass
        try:
            cur.execute("""
                CREATE OR REPLACE TRIGGER TRG_NOTIF_NOVO_CHAMADO
                AFTER INSERT ON PCS_CHAMADOS_TI
                FOR EACH ROW
                DECLARE
                    CURSOR c_analistas IS
                        SELECT MATRICULA FROM PCEMPR WHERE CODSETOR = 10 AND DT_EXCLUSAO IS NULL;
                BEGIN
                    FOR r IN c_analistas LOOP
                        INSERT INTO PCS_CHAMADOS_TI_NOTIF (ID, MATRICULA_DESTINO, ID_CHAMADO, TIPO, TITULO, MENSAGEM, DATAHORA, LIDA)
                        VALUES (
                            SEQ_PCS_CHAMADOS_TI_NOTIF.NEXTVAL,
                            r.MATRICULA,
                            :NEW.ID,
                            'NOVO_CHAMADO',
                            'Novo Chamado #' || :NEW.ID,
                            :NEW.CATEGORIA || ' - ' || :NEW.PRIORIDADE || ' - ' || SUBSTR(:NEW.NOME_USUARIO, 1, 30),
                            SYSDATE,
                            'N'
                        );
                    END LOOP;
                END;
            """)
            print("    OK - Trigger criado")
        except Exception as e:
            print(f"    ERRO: {e}")

        # 5. Criar trigger para RESPOSTA ANALISTA -> notifica usuário
        print("\n[5] Criando trigger TRG_NOTIF_RESPOSTA_ANALISTA...")
        try:
            cur.execute("DROP TRIGGER TRG_NOTIF_RESPOSTA_ANALISTA")
        except:
            pass
        try:
            cur.execute("""
                CREATE OR REPLACE TRIGGER TRG_NOTIF_RESPOSTA_ANALISTA
                AFTER INSERT ON PCS_CHAMADOS_TI_HIST
                FOR EACH ROW
                WHEN (NEW.TIPO = 'RESPOSTA_ANALISTA')
                DECLARE
                    v_matricula_usuario NUMBER;
                BEGIN
                    SELECT MATRICULA INTO v_matricula_usuario
                    FROM PCS_CHAMADOS_TI WHERE ID = :NEW.IDCHAMADO;

                    INSERT INTO PCS_CHAMADOS_TI_NOTIF (ID, MATRICULA_DESTINO, ID_CHAMADO, TIPO, TITULO, MENSAGEM, DATAHORA, LIDA)
                    VALUES (
                        SEQ_PCS_CHAMADOS_TI_NOTIF.NEXTVAL,
                        v_matricula_usuario,
                        :NEW.IDCHAMADO,
                        'RESPOSTA_ANALISTA',
                        'Resposta no Chamado #' || :NEW.IDCHAMADO,
                        SUBSTR(:NEW.MENSAGEM, 1, 200),
                        SYSDATE,
                        'N'
                    );
                EXCEPTION
                    WHEN NO_DATA_FOUND THEN NULL;
                END;
            """)
            print("    OK - Trigger criado")
        except Exception as e:
            print(f"    ERRO: {e}")

        # 6. Criar trigger para RESPOSTA USUÁRIO -> notifica analista responsável
        print("\n[6] Criando trigger TRG_NOTIF_RESPOSTA_USUARIO...")
        try:
            cur.execute("DROP TRIGGER TRG_NOTIF_RESPOSTA_USUARIO")
        except:
            pass
        try:
            cur.execute("""
                CREATE OR REPLACE TRIGGER TRG_NOTIF_RESPOSTA_USUARIO
                AFTER INSERT ON PCS_CHAMADOS_TI_HIST
                FOR EACH ROW
                WHEN (NEW.TIPO = 'RESPOSTA_USUARIO')
                DECLARE
                    v_analista_resp NUMBER;
                BEGIN
                    SELECT ANALISTA_RESP INTO v_analista_resp
                    FROM PCS_CHAMADOS_TI WHERE ID = :NEW.IDCHAMADO;

                    IF v_analista_resp IS NOT NULL THEN
                        INSERT INTO PCS_CHAMADOS_TI_NOTIF (ID, MATRICULA_DESTINO, ID_CHAMADO, TIPO, TITULO, MENSAGEM, DATAHORA, LIDA)
                        VALUES (
                            SEQ_PCS_CHAMADOS_TI_NOTIF.NEXTVAL,
                            v_analista_resp,
                            :NEW.IDCHAMADO,
                            'RESPOSTA_USUARIO',
                            'Usuário respondeu Chamado #' || :NEW.IDCHAMADO,
                            SUBSTR(:NEW.MENSAGEM, 1, 200),
                            SYSDATE,
                            'N'
                        );
                    END IF;
                EXCEPTION
                    WHEN NO_DATA_FOUND THEN NULL;
                END;
            """)
            print("    OK - Trigger criado")
        except Exception as e:
            print(f"    ERRO: {e}")

        # 7. Criar trigger para CHAMADO ASSUMIDO -> notifica usuário
        print("\n[7] Criando trigger TRG_NOTIF_CHAMADO_ASSUMIDO...")
        try:
            cur.execute("DROP TRIGGER TRG_NOTIF_CHAMADO_ASSUMIDO")
        except:
            pass
        try:
            cur.execute("""
                CREATE OR REPLACE TRIGGER TRG_NOTIF_CHAMADO_ASSUMIDO
                AFTER INSERT ON PCS_CHAMADOS_TI_HIST
                FOR EACH ROW
                WHEN (NEW.TIPO = 'ASSUMIDO')
                DECLARE
                    v_matricula_usuario NUMBER;
                    v_nome_analista VARCHAR2(100);
                BEGIN
                    SELECT MATRICULA INTO v_matricula_usuario
                    FROM PCS_CHAMADOS_TI WHERE ID = :NEW.IDCHAMADO;

                    SELECT NOME_GUERRA INTO v_nome_analista
                    FROM PCEMPR WHERE MATRICULA = :NEW.MATRICULA;

                    INSERT INTO PCS_CHAMADOS_TI_NOTIF (ID, MATRICULA_DESTINO, ID_CHAMADO, TIPO, TITULO, MENSAGEM, DATAHORA, LIDA)
                    VALUES (
                        SEQ_PCS_CHAMADOS_TI_NOTIF.NEXTVAL,
                        v_matricula_usuario,
                        :NEW.IDCHAMADO,
                        'CHAMADO_ASSUMIDO',
                        'Chamado #' || :NEW.IDCHAMADO || ' foi assumido',
                        'Analista ' || v_nome_analista || ' assumiu seu chamado',
                        SYSDATE,
                        'N'
                    );
                EXCEPTION
                    WHEN NO_DATA_FOUND THEN NULL;
                END;
            """)
            print("    OK - Trigger criado")
        except Exception as e:
            print(f"    ERRO: {e}")

        # 8. Criar trigger para FINALIZAÇÃO -> notifica usuário
        print("\n[8] Criando trigger TRG_NOTIF_FINALIZADO...")
        try:
            cur.execute("DROP TRIGGER TRG_NOTIF_FINALIZADO")
        except:
            pass
        try:
            cur.execute("""
                CREATE OR REPLACE TRIGGER TRG_NOTIF_FINALIZADO
                AFTER INSERT ON PCS_CHAMADOS_TI_HIST
                FOR EACH ROW
                WHEN (NEW.TIPO = 'FINALIZACAO')
                DECLARE
                    v_matricula_usuario NUMBER;
                BEGIN
                    SELECT MATRICULA INTO v_matricula_usuario
                    FROM PCS_CHAMADOS_TI WHERE ID = :NEW.IDCHAMADO;

                    INSERT INTO PCS_CHAMADOS_TI_NOTIF (ID, MATRICULA_DESTINO, ID_CHAMADO, TIPO, TITULO, MENSAGEM, DATAHORA, LIDA)
                    VALUES (
                        SEQ_PCS_CHAMADOS_TI_NOTIF.NEXTVAL,
                        v_matricula_usuario,
                        :NEW.IDCHAMADO,
                        'FINALIZADO',
                        'Chamado #' || :NEW.IDCHAMADO || ' finalizado',
                        'Seu chamado foi finalizado',
                        SYSDATE,
                        'N'
                    );
                EXCEPTION
                    WHEN NO_DATA_FOUND THEN NULL;
                END;
            """)
            print("    OK - Trigger criado")
        except Exception as e:
            print(f"    ERRO: {e}")

        conn.commit()
        print("\n" + "=" * 60)
        print("CONFIGURAÇÃO CONCLUÍDA COM SUCESSO!")
        print("=" * 60)

    except Exception as e:
        logger.error(f"Erro na configuração: {e}")
        print(f"\nERRO GERAL: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    criar_estrutura_notificacoes()
