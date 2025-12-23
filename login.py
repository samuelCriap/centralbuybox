# login.py — Tela de login Flet com integração SQLite
"""
Tela de login com layout split: gradiente + formulário
Inclui seleção de servidor (Localhost/Rede)
"""
import flet as ft
import os
from typing import Callable, Optional
from configuracoes import carregar_preferencias, salvar_preferencias
from db_client import verificar_usuario, adicionar_usuario

try:
    from network_config import load_config, set_local_mode, set_network_mode, test_network_connection
    HAS_NETWORK = True
except ImportError:
    HAS_NETWORK = False


def verificar_login(usuario: str, senha: str):
    """Verifica credenciais e retorna (sucesso, mensagem, dados)"""
    return verificar_usuario(usuario, senha)


def adicionar_usuario_sheet(usuario: str, senha: str, email: str):
    """Adiciona usuário (wrapper para compatibilidade)"""
    return adicionar_usuario(usuario, senha, email)


def criar_login(page: ft.Page, on_success_callback: Callable[[str], None]):
    """Cria a tela de login com layout split"""
    
    # Carregar preferências
    prefs = carregar_preferencias() or {}
    usuario_salvo = prefs.get("usuario_padrao", "")
    lembrar_login = prefs.get("lembrar_login", False)
    
    # Configuração MySQL
    if HAS_NETWORK:
        config = load_config()
        mysql_config = config.get("mysql", {})
        mysql_host = [mysql_config.get("host", "localhost")]
    else:
        mysql_host = ["localhost"]
    
    # Campos do formulário
    campo_usuario = ft.TextField(
        label="Usuário",
        prefix_icon=ft.Icons.PERSON_OUTLINE,
        border_radius=8,
        bgcolor="#FFFFFF",
        width=300,
        value=usuario_salvo if lembrar_login else "",
    )
    
    campo_senha = ft.TextField(
        label="Senha",
        prefix_icon=ft.Icons.LOCK_OUTLINE,
        password=True,
        can_reveal_password=True,
        border_radius=8,
        bgcolor="#FFFFFF",
        width=300,
    )
    
    campo_email = ft.TextField(
        label="E-mail (para aprovação)",
        prefix_icon=ft.Icons.EMAIL,
        border_radius=8,
        bgcolor="#FFFFFF",
        width=300,
        visible=False,
    )
    
    # Campo de IP do servidor MySQL
    campo_mysql_ip = ft.TextField(
        label="IP do Servidor MySQL",
        hint_text="localhost ou IP da rede",
        prefix_icon=ft.Icons.DNS,
        border_radius=8,
        bgcolor="#FFFFFF",
        width=300,
        value=mysql_host[0],
    )
    
    status_conexao = ft.Text("", size=10, italic=True)
    
    checkbox_lembrar = ft.Checkbox(
        label="Lembrar login",
        value=lembrar_login,
    )
    
    label_erro = ft.Text("", color=ft.Colors.RED_400, size=12)
    
    modo_criacao = [False]
    titulo_texto = ft.Text("Login", size=32, weight=ft.FontWeight.BOLD, color="#000000")
    botao_acao = ft.Ref[ft.ElevatedButton]()
    botao_modo = ft.Ref[ft.TextButton]()
    
    def validar_login(e):
        # Salvar configuração MySQL primeiro
        if HAS_NETWORK:
            from network_config import save_config
            
            mysql_ip = campo_mysql_ip.value.strip()
            if not mysql_ip:
                mysql_ip = "localhost"
            
            # Testar conexão MySQL
            status_conexao.value = f"Conectando a {mysql_ip}..."
            status_conexao.color = "#3B82F6"
            page.update()
            
            # Atualizar config com o novo IP
            config = load_config()
            if "mysql" not in config:
                config["mysql"] = {}
            config["mysql"]["host"] = mysql_ip
            config["db_type"] = "mysql"
            save_config(config)
            
            # Testar conexão
            try:
                try:
                    import mysql.connector
                except ImportError:
                    label_erro.value = "Instale: pip install mysql-connector-python"
                    label_erro.color = ft.Colors.RED_400
                    status_conexao.value = ""
                    page.update()
                    return
                
                mysql_cfg = config.get("mysql", {})
                test_conn = mysql.connector.connect(
                    host=mysql_ip,
                    port=mysql_cfg.get("port", 3306),
                    user=mysql_cfg.get("user", "root"),
                    password=mysql_cfg.get("password", ""),
                    database=mysql_cfg.get("database", "netshoes_nivia"),
                )
                if test_conn.is_connected():
                    test_conn.close()
                    status_conexao.value = f"✅ Conectado: {mysql_ip}"
                    status_conexao.color = "#22C55E"
                    mysql_host[0] = mysql_ip
                else:
                    label_erro.value = "Falha na conexão MySQL"
                    label_erro.color = ft.Colors.RED_400
                    status_conexao.value = ""
                    page.update()
                    return
            except Exception as ex:
                error_msg = str(ex)
                if "Access denied" in error_msg:
                    label_erro.value = "Usuário/senha MySQL incorretos"
                elif "Can't connect" in error_msg or "10061" in error_msg:
                    label_erro.value = f"MySQL não encontrado em {mysql_ip}"
                elif "Unknown database" in error_msg:
                    label_erro.value = "Banco netshoes_nivia não existe"
                else:
                    label_erro.value = f"Erro MySQL: {error_msg[:50]}"
                label_erro.color = ft.Colors.RED_400
                status_conexao.value = ""
                page.update()
                return
            
            page.update()
        
        # Prosseguir com login
        usuario = campo_usuario.value.strip()
        senha = campo_senha.value.strip()
        
        if not usuario or not senha:
            label_erro.value = "Preencha todos os campos."
            label_erro.color = ft.Colors.ORANGE_400
            page.update()
            return
        
        label_erro.value = "Verificando..."
        label_erro.color = ft.Colors.BLUE_400
        page.update()
        
        sucesso, msg, dados = verificar_login(usuario, senha)
        
        if sucesso:
            label_erro.value = f"✅ {msg}"
            label_erro.color = ft.Colors.GREEN_400
            
            # Salvar preferências
            if checkbox_lembrar.value:
                salvar_preferencias({"lembrar_login": True, "usuario_padrao": usuario})
            else:
                salvar_preferencias({"lembrar_login": False, "usuario_padrao": ""})
            
            page.update()
            
            # Aguardar e abrir interface principal
            import time
            time.sleep(0.7)
            page.clean()
            # Callback agora recebe o dicionario completo
            on_success_callback(dados)
        else:
            label_erro.value = f"❌ {msg}"
            label_erro.color = ft.Colors.RED_400
            page.update()
    
    def criar_conta(e):
        usuario = campo_usuario.value.strip()
        senha = campo_senha.value.strip()
        email = campo_email.value.strip()
        
        if not usuario or not senha or not email:
            label_erro.value = "Preencha todos os campos."
            label_erro.color = ft.Colors.ORANGE_400
            page.update()
            return
        
        from db_client import listar_usuarios
        df = listar_usuarios()
        if df is not None and not df.empty and usuario in df["usuario"].values:
            label_erro.value = "Usuário já existe."
            label_erro.color = ft.Colors.RED_400
            page.update()
            return
        
        adicionar_usuario_sheet(usuario, senha, email)
        label_erro.value = "Cadastro enviado! Aguarde aprovação na planilha."
        label_erro.color = ft.Colors.GREEN_400
        page.update()
        
        # Voltar para login após 1.2s
        import time
        time.sleep(1.2)
        alternar_modo(None)
    
    def alternar_modo(e):
        modo_criacao[0] = not modo_criacao[0]
        
        if modo_criacao[0]:
            titulo_texto.value = "Criar Conta"
            botao_acao.current.text = "Cadastrar"
            botao_acao.current.on_click = criar_conta
            botao_modo.current.text = "Voltar ao Login"
            campo_email.visible = True
            label_erro.value = ""
        else:
            titulo_texto.value = "Login"
            botao_acao.current.text = "Entrar"
            botao_acao.current.on_click = validar_login
            botao_modo.current.text = "Criar nova conta"
            campo_email.visible = False
            label_erro.value = ""
        
        page.update()
    
    # Bind Enter para login
    campo_usuario.on_submit = lambda e: campo_senha.focus()
    campo_senha.on_submit = validar_login
    
    # Logo path
    logo_path = os.path.join(os.path.dirname(__file__), "data", "logo2.png")
    
    return ft.Container(
        content=ft.Row([
            # Lado esquerdo - Visual com gradiente
            ft.Container(
                content=ft.Column([
                    ft.Image(
                        src=logo_path if os.path.exists(logo_path) else None,
                        width=300,
                        height=300,
                        fit=ft.ImageFit.CONTAIN,
                    ) if os.path.exists(logo_path) else ft.Icon(
                        ft.Icons.SPORTS_SOCCER,
                        size=200,
                        color="#FFFFFF",
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                   alignment=ft.MainAxisAlignment.CENTER, spacing=15),
                expand=True,
                gradient=ft.LinearGradient(
                    begin=ft.alignment.top_left,
                    end=ft.alignment.bottom_right,
                    colors=["#FF6B35", "#F7931E", "#16A34A", "#0D9488", "#1F2937", "#111827"],
                ),
            ),
            # Lado direito - Formulário
            ft.Container(
                content=ft.Column([
                    titulo_texto,
                    ft.Container(height=15),
                    # Conexão MySQL
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.STORAGE, color="#3B82F6", size=16),
                                ft.Text("Servidor MySQL", size=12, weight=ft.FontWeight.BOLD, color="#666666"),
                            ], spacing=5),
                            campo_mysql_ip,
                            status_conexao,
                        ], spacing=5),
                        bgcolor="#F5F5F5",
                        padding=10,
                        border_radius=8,
                    ) if HAS_NETWORK else ft.Container(),
                    ft.Container(height=15),
                    campo_usuario,
                    ft.Container(height=10),
                    campo_senha,
                    ft.Container(height=10),
                    campo_email,
                    ft.Container(height=5),
                    checkbox_lembrar,
                    ft.Container(height=5),
                    label_erro,
                    ft.Container(height=15),
                    ft.ElevatedButton(
                        ref=botao_acao,
                        text="Entrar",
                        width=300,
                        height=50,
                        bgcolor="#000000",
                        color="#FFFFFF",
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                        on_click=validar_login,
                    ),
                    ft.Container(height=10),
                    ft.TextButton(
                        ref=botao_modo,
                        text="Criar nova conta",
                        on_click=alternar_modo,
                    ),
                    ft.Container(height=20),
                    ft.Text(
                        "Central do Comercial v2.0",
                        size=10,
                        color="#999999",
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                   alignment=ft.MainAxisAlignment.CENTER),
                expand=True,
                bgcolor="#FFFFFF",
                padding=40,
            ),
        ], spacing=0, expand=True),
        expand=True,
    )


if __name__ == "__main__":
    def main(page: ft.Page):
        page.title = "Login Test"
        page.window.width = 900
        page.window.height = 600
        page.add(criar_login(page, lambda u: print(f"Login: {u}")))
    
    ft.app(target=main)
