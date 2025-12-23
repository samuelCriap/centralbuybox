# migrate_auto.py - Script de migração automática (sem input)
import pandas as pd

def migrate_all():
    print("=" * 60)
    print("  MIGRAÇÃO SQLite → MySQL")
    print("=" * 60)
    
    import sqlite_client
    import mysql_client
    
    # Migrar PRODUTOS
    print("[1/4] Migrando PRODUTOS...")
    try:
        sqlite_conn = sqlite_client.get_connection()
        df = pd.read_sql_query("SELECT * FROM produtos", sqlite_conn)
        sqlite_conn.close()
        
        if not df.empty:
            if 'id' in df.columns:
                df = df.drop('id', axis=1)
            
            mysql_conn = mysql_client.get_connection()
            cursor = mysql_conn.cursor()
            cursor.execute("DELETE FROM produtos")
            
            columns = list(df.columns)
            placeholders = ", ".join(["%s"] * len(columns))
            col_str = ", ".join(columns)
            insert_query = f"INSERT INTO produtos ({col_str}) VALUES ({placeholders})"
            
            data = [tuple(None if pd.isna(v) else v for v in row) for row in df.values]
            cursor.executemany(insert_query, data)
            mysql_conn.commit()
            cursor.close()
            mysql_conn.close()
            print(f"      OK: {len(df)} produtos migrados")
        else:
            print("      Vazio")
    except Exception as e:
        print(f"      ERRO: {e}")
    
    # Migrar HISTORICO
    print("[2/4] Migrando HISTORICO...")
    try:
        sqlite_conn = sqlite_client.get_connection()
        df = pd.read_sql_query("SELECT * FROM historico", sqlite_conn)
        sqlite_conn.close()
        
        if not df.empty:
            if 'id' in df.columns:
                df = df.drop('id', axis=1)
            
            mysql_conn = mysql_client.get_connection()
            cursor = mysql_conn.cursor()
            cursor.execute("DELETE FROM historico")
            
            columns = list(df.columns)
            placeholders = ", ".join(["%s"] * len(columns))
            col_str = ", ".join(columns)
            insert_query = f"INSERT INTO historico ({col_str}) VALUES ({placeholders})"
            
            data = [tuple(None if pd.isna(v) else v for v in row) for row in df.values]
            cursor.executemany(insert_query, data)
            mysql_conn.commit()
            cursor.close()
            mysql_conn.close()
            print(f"      OK: {len(df)} registros migrados")
        else:
            print("      Vazio")
    except Exception as e:
        print(f"      ERRO: {e}")
    
    # Migrar USUARIOS
    print("[3/4] Migrando USUARIOS...")
    try:
        sqlite_conn = sqlite_client.get_connection()
        df = pd.read_sql_query("SELECT * FROM usuarios", sqlite_conn)
        sqlite_conn.close()
        
        if not df.empty:
            if 'id' in df.columns:
                df = df.drop('id', axis=1)
            
            mysql_conn = mysql_client.get_connection()
            cursor = mysql_conn.cursor()
            cursor.execute("DELETE FROM usuarios")
            
            columns = list(df.columns)
            placeholders = ", ".join(["%s"] * len(columns))
            col_str = ", ".join(columns)
            insert_query = f"INSERT INTO usuarios ({col_str}) VALUES ({placeholders})"
            
            data = [tuple(None if pd.isna(v) else v for v in row) for row in df.values]
            cursor.executemany(insert_query, data)
            mysql_conn.commit()
            cursor.close()
            mysql_conn.close()
            print(f"      OK: {len(df)} usuarios migrados")
        else:
            print("      Vazio")
    except Exception as e:
        print(f"      ERRO: {e}")
    
    # Migrar HISTORICO_BACKUP
    print("[4/4] Migrando HISTORICO_BACKUP...")
    try:
        sqlite_conn = sqlite_client.get_connection()
        cursor_check = sqlite_conn.cursor()
        cursor_check.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='historico_backup'")
        if cursor_check.fetchone():
            df = pd.read_sql_query("SELECT * FROM historico_backup", sqlite_conn)
            sqlite_conn.close()
            
            if not df.empty:
                if 'id' in df.columns:
                    df = df.drop('id', axis=1)
                
                mysql_conn = mysql_client.get_connection()
                cursor = mysql_conn.cursor()
                cursor.execute("DELETE FROM historico_backup")
                
                columns = list(df.columns)
                placeholders = ", ".join(["%s"] * len(columns))
                col_str = ", ".join(columns)
                insert_query = f"INSERT INTO historico_backup ({col_str}) VALUES ({placeholders})"
                
                data = [tuple(None if pd.isna(v) else v for v in row) for row in df.values]
                cursor.executemany(insert_query, data)
                mysql_conn.commit()
                cursor.close()
                mysql_conn.close()
                print(f"      OK: {len(df)} registros migrados")
            else:
                print("      Vazio")
        else:
            sqlite_conn.close()
            print("      Tabela nao existe no SQLite")
    except Exception as e:
        print(f"      ERRO: {e}")
    
    print()
    print("=" * 60)
    print("  MIGRAÇÃO CONCLUÍDA!")
    print("=" * 60)

if __name__ == "__main__":
    migrate_all()
