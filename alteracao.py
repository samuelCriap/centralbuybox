# alteracao.py — UI para adicionar/alterar planilha (com segurança na mesclagem por SKU Color)
import os
from typing import Tuple
import pandas as pd
import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk
from google_sheet_client import ler_aba, gravar_aba

NOME_ABA = "Página1"
TEMP_PATH = os.path.join("data", "temp")
os.makedirs(TEMP_PATH, exist_ok=True)


def abrir_janela_alteracao(parent=None):
    win = ctk.CTkToplevel()
    win.title("Adicionar / Alterar Planilha")
    win.geometry("600x240")
    win.lift()
    win.focus_force()
    win.grab_set()
    ctk.CTkLabel(win, text="Selecione uma planilha (*.xlsx ou *.csv)", font=("Arial", 17, "bold")).pack(pady=18)

    frame_btn = ctk.CTkFrame(win)
    frame_btn.pack(pady=14)

    def selecionar_arquivo():
        caminho = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx"), ("CSV", "*.csv")])
        if caminho:
            abrir_preview(caminho, win)

    ctk.CTkButton(frame_btn, text="Selecionar arquivo", width=210, command=selecionar_arquivo).pack()
    return win


def abrir_preview(caminho: str, janela_pai):
    try:
        if caminho.lower().endswith(".xlsx"):
            df_novo = pd.read_excel(caminho)
        else:
            df_novo = pd.read_csv(caminho)
    except Exception as e:
        messagebox.showerror("Erro ao abrir arquivo", str(e))
        return

    df_novo = df_novo.fillna("")
    if "SKU Color" not in df_novo.columns:
        messagebox.showerror("Erro", "A planilha enviada precisa conter a coluna 'SKU Color'.")
        return

    preview = ctk.CTkToplevel()
    preview.title("Preview da planilha enviada")
    preview.geometry("1200x600")
    preview.lift()
    preview.focus_force()
    preview.grab_set()

    frame = ctk.CTkFrame(preview)
    frame.pack(fill="both", expand=True, padx=10, pady=10)

    cols = list(df_novo.columns)
    tree = ttk.Treeview(frame, columns=cols, show="headings", height=20)
    style = ttk.Style()
    style.configure("Treeview.Heading", font=("Arial", 11, "bold"))
    style.configure("Treeview", font=("Arial", 10), rowheight=25)

    for col in cols:
        tree.heading(col, text=col)
        tree.column(col, width=140, anchor="center")

    for _, row in df_novo.iterrows():
        tree.insert("", "end", values=list(row))

    scroll_y = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scroll_y.set)
    tree.pack(side="left", fill="both", expand=True)
    scroll_y.pack(side="right", fill="y")

    def confirmar():
        janela_confirmacao(df_novo, janela_pai, preview)

    ctk.CTkButton(preview, text="Confirmar Alterações", fg_color="#0A84FF", hover_color="#0062CC",
                  width=240, height=38, command=confirmar).pack(pady=12)
    return preview


def janela_confirmacao(df_novo: pd.DataFrame, janela_pai, preview_win):
    confirm = ctk.CTkToplevel()
    confirm.title("Confirmação")
    confirm.geometry("420x200")
    confirm.lift()
    confirm.focus_force()
    confirm.grab_set()
    ctk.CTkLabel(confirm, text="Tem certeza que deseja aplicar as alterações\nna planilha do Google Sheets?",
                 font=("Arial", 15), justify="center").pack(pady=25)
    btn_frame = ctk.CTkFrame(confirm)
    btn_frame.pack(pady=10)

    def executar():
        aplicar_alteracoes(df_novo, janela_pai)
        confirm.destroy()
        preview_win.destroy()

    ctk.CTkButton(btn_frame, text="Confirmar", fg_color="#16A34A", width=120, command=executar).pack(side="left",
                                                                                                      padx=10)
    ctk.CTkButton(btn_frame, text="Cancelar", fg_color="#DC2626", width=120, command=confirm.destroy).pack(side="left",
                                                                                                             padx=10)


def aplicar_alteracoes(df_novo: pd.DataFrame, janela_pai):
    try:
        df_original = ler_aba(NOME_ABA).copy()
    except Exception as e:
        messagebox.showerror("Erro", f"Erro lendo '{NOME_ABA}':\n{e}")
        return

    df_original = df_original.fillna("")
    if df_original.empty:
        messagebox.showerror("Erro", "A planilha original está vazia.")
        return

    df_final, resumo = atualizar_base_seguro(df_original, df_novo)
    df_final = df_final.fillna("").replace("nan", "")
    ok = gravar_aba(NOME_ABA, df_final)
    if not ok:
        messagebox.showerror("Erro", "Falha ao gravar alterações.")
        return

    messagebox.showinfo("Concluído",
                        f"Alterações aplicadas com sucesso!\n\n🔄 Linhas atualizadas: {resumo['atualizados']}\n➕ Novas linhas inseridas: {resumo['inseridos']}")
    janela_pai.lift()
    janela_pai.focus_force()


def atualizar_base_seguro(df_original: pd.DataFrame, df_novo: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
    """
    Regras:
    - Se SKU Color existir -> substituir linha inteira
    - Se NÃO existir -> adicionar nova linha
    """
    def normalize(value):
        if pd.isna(value):
            return ""
        return str(value).replace("\u200b", "").replace("\ufeff", "").strip()

    orig = df_original.copy()
    novo = df_novo.copy()

    orig = orig.applymap(normalize)
    novo = novo.applymap(normalize)

    if "SKU Color" not in orig.columns:
        raise ValueError("A coluna 'SKU Color' não existe na planilha original.")
    if "SKU Color" not in novo.columns:
        raise ValueError("A planilha enviada não possui a coluna 'SKU Color'.")

    # garante colunas
    for col in orig.columns:
        if col not in novo.columns:
            novo[col] = ""
    novo = novo[orig.columns.tolist()]

    orig_idx = orig.set_index("SKU Color", drop=False)
    novo_idx = novo.set_index("SKU Color", drop=False)

    atualizados = 0
    inseridos = 0

    for sku, row in novo_idx.iterrows():
        sku_norm = str(sku).strip()
        if sku_norm == "":
            continue
        if sku_norm in orig_idx.index:
            orig_idx.loc[sku_norm] = row
            atualizados += 1
        else:
            orig_idx.loc[sku_norm] = row
            inseridos += 1

    df_final = orig_idx.reset_index(drop=True).applymap(normalize)
    return df_final, {"atualizados": atualizados, "inseridos": inseridos}
