"""
Gera todas as abas do relatório XLSX.
Esta é a lógica que antes estava dentro de relatorios.py.
Agora está isolada para manter o projeto organizado.

Mantém 100% das funções atuais e adiciona a aba "Oportunidades IA" + geração de PDF.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

from oportunidades_ia import detectar_oportunidades

# ---------------- PDF ----------------
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm

# ---------------------------------------------------------------------
# Constantes (atualizadas para novo schema com 3 vendedores)
# ---------------------------------------------------------------------
COL_DATA = "Data Verificacao"
COL_PRECO = "Preco 1"  # Preco do vendedor principal
COL_VENDEDOR = "Vendedor 1"  # Vendedor principal
COL_SKU = "codigo_produto"


from oportunidades_ia import gerar_insights_texto

def gerar_pdf_ia(df_ia, out_file, df_hist=None, start_date=None, end_date=None):
    """
    Gera PDF EXECUTIVO com resumo da IA, bonito e compacto (max. 3 paginas).
    Nao lista SKUs - usa insights consolidados.
    """

    doc = SimpleDocTemplate(out_file, pagesize=A4, title="Oportunidades Color IA")

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Title'],
        fontSize=22,
        alignment=1,
        textColor="#1f6aa5",
        spaceAfter=20
    )

    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Heading2'],
        fontSize=15,
        textColor="#1f6aa5",
        spaceAfter=10
    )

    text_style = ParagraphStyle(
        'TextStyle',
        parent=styles['BodyText'],
        fontSize=11,
        leading=16,
    )

    flow = []

    # LOGO ---------------------------------------------------------
    try:
        logo = Image("data/logo2.png", width=5 * cm, height=5 * cm)
        logo.hAlign = "CENTER"
        flow.append(logo)
        flow.append(Spacer(1, 12))
    except:
        flow.append(Paragraph("<b>Color Sports</b>", title_style))

    # TITULO ---------------------------------------------------------
    flow.append(Paragraph("OPORTUNIDADES COLOR IA", title_style))
    flow.append(Spacer(1, 20))

    if df_ia is None or df_ia.empty:
        flow.append(Paragraph("Nenhuma oportunidade detectada.", text_style))
        doc.build(flow)
        return

    # ===============================================================
    # 1) GERAR TEXTO VIA IA (funcao adicionada no oportunidades_ia.py)
    # ===============================================================
    insights = gerar_insights_texto(df_hist, df_ia, start_date, end_date)

    # ===============================================================
    # 1) RESUMO EXECUTIVO
    # ===============================================================
    flow.append(Paragraph("<b>Resumo Executivo</b>", header_style))
    flow.append(Paragraph(insights["executive_summary"], text_style))
    flow.append(Spacer(1, 18))

    # ===============================================================
    # 2) DESTAQUES TOP 5
    # ===============================================================
    flow.append(Paragraph("<b>Destaques da Semana</b>", header_style))
    for titulo, texto in insights["highlights"]:
        flow.append(Paragraph(f"{titulo}:<br/>{texto}", text_style))
        flow.append(Spacer(1, 10))

    flow.append(Spacer(1, 18))

    # ===============================================================
    # 3) ACOES RECOMENDADAS
    # ===============================================================
    flow.append(Paragraph("<b>Acoes Recomendadas</b>", header_style))

    for rec in insights["recommendations"]:
        flow.append(Paragraph(f"- {rec}", text_style))
        flow.append(Spacer(1, 6))

    flow.append(Spacer(1, 18))

    # ===============================================================
    # 4) TABELA TOP 10 (curta)
    # ===============================================================
    flow.append(Paragraph("<b>Top Oportunidades</b>", header_style))

    top = insights["table_top"]

    if not top.empty and COL_SKU in top.columns and "tipo" in top.columns:
        # Monta tabela em texto (clean)
        for _, row in top.iterrows():
            ganho = row.get('Ganho Estimado', 0)
            txt = (
                f"<b>SKU:</b> {row[COL_SKU]} - "
                f"<b>{row['tipo']}</b> - "
                f"<b>Ganho:</b> R$ {ganho:.2f}" if isinstance(ganho, (int, float)) else f"<b>Ganho:</b> {ganho}"
            )
            flow.append(Paragraph(txt, text_style))
            flow.append(Spacer(1, 6))

    flow.append(Spacer(1, 20))

    # ===============================================================
    # 5) AVISOS IMPORTANTES
    # ===============================================================
    if insights["warnings"]:
        flow.append(Paragraph("<b>Avisos Importantes</b>", header_style))
        for w in insights["warnings"]:
            flow.append(Paragraph(f"- {w}", text_style))
            flow.append(Spacer(1, 6))

    # ===============================================================
    # Finaliza PDF
    # ===============================================================
    doc.build(flow)

# ---------------------------------------------------------------------
# Funcao auxiliar XLSX
# ---------------------------------------------------------------------
def _df_to_excel(writer, df, name):
    if df is None or df.empty:
        pd.DataFrame({"Info": ["Sem dados"]}).to_excel(writer, sheet_name=name, index=False)
    else:
        df.to_excel(writer, sheet_name=name, index=False)


# ---------------------------------------------------------------------
# Calculos
# ---------------------------------------------------------------------
def _competitor_substitutions(df_hist, vendor="Color Sports"):
    if COL_SKU not in df_hist.columns or COL_VENDEDOR not in df_hist.columns:
        return pd.DataFrame()
    
    df2 = df_hist[[COL_SKU, COL_VENDEDOR, COL_DATA]].dropna().copy()
    df2 = df2.sort_values([COL_SKU, COL_DATA])

    eventos = {}
    for sku, group in df2.groupby(COL_SKU):
        last = None
        for _, row in group.iterrows():
            v = str(row[COL_VENDEDOR]).strip()
            if last and last.lower() == vendor.lower() and v.lower() != vendor.lower():
                eventos[v] = eventos.get(v, 0) + 1
            last = v

    return pd.DataFrame(list(eventos.items()), columns=[COL_VENDEDOR, "count"]).sort_values("count", ascending=False)


def _aggressiveness_delta(df_hist):
    if COL_SKU not in df_hist.columns or COL_PRECO not in df_hist.columns:
        return pd.DataFrame()
    
    df = df_hist.dropna(subset=[COL_SKU, COL_PRECO]).copy()
    
    if "dia" not in df.columns:
        return pd.DataFrame()

    media = df.groupby(["dia", COL_SKU])[COL_PRECO].mean().reset_index()
    media = media.rename(columns={COL_PRECO: "media_sku"})

    df = df.merge(media, on=["dia", COL_SKU], how="left")
    df["delta"] = df[COL_PRECO] - df["media_sku"]

    agg = df.groupby(COL_VENDEDOR)["delta"].mean().reset_index(name="delta_mean")
    return agg.sort_values("delta_mean")


def _buybox_stats(df_hist, vendor_name="Color Sports"):
    if COL_PRECO not in df_hist.columns or COL_SKU not in df_hist.columns:
        return pd.DataFrame(), {"losses": 0, "recovers": 0, "loss_events": []}
    
    df = df_hist.dropna(subset=[COL_PRECO, COL_SKU]).copy()
    
    if "dia" not in df.columns:
        return pd.DataFrame(), {"losses": 0, "recovers": 0, "loss_events": []}

    idx = df.groupby(["dia", COL_SKU])[COL_PRECO].idxmin()
    bb = df.loc[idx, ["dia", COL_SKU, COL_VENDEDOR, COL_PRECO]]
    bb = bb.rename(columns={COL_VENDEDOR: "Vencedor", COL_PRECO: "PrecoBuyBox"})

    wins = bb.groupby("Vencedor").size().reset_index(name="wins").sort_values("wins", ascending=False)

    losses = 0
    recovers = 0
    events = []
    prev = {}

    for _, row in bb.sort_values([COL_SKU, "dia"]).iterrows():
        sku = row[COL_SKU]
        v = row["Vencedor"]

        if sku in prev:
            old = prev[sku]

            if old.lower() == vendor_name.lower() and v.lower() != vendor_name.lower():
                losses += 1
                events.append((sku, old, v, row["dia"]))

            if old.lower() != vendor_name.lower() and v.lower() == vendor_name.lower():
                recovers += 1

        prev[sku] = v

    return wins, {"losses": losses, "recovers": recovers, "loss_events": events}


def _top_volatile_skus(df_hist, top_n=200):
    if COL_SKU not in df_hist.columns or COL_PRECO not in df_hist.columns:
        return pd.DataFrame()
    
    agg = df_hist.groupby(COL_SKU)[COL_PRECO].agg(["min", "max"]).reset_index()
    agg["amp"] = agg["max"] - agg["min"]
    return agg.sort_values("amp", ascending=False).head(top_n)


# ---------------------------------------------------------------------
# GERAR XLSX + PDF
# ---------------------------------------------------------------------
def gerar_relatorio(df_hist, start_date, end_date, include, out_dir):

    df = df_hist.copy()
    
    # Converter coluna de data para datetime se for string
    if COL_DATA in df.columns:
        df[COL_DATA] = pd.to_datetime(df[COL_DATA], format="%d/%m/%Y %H:%M:%S", errors="coerce")
        if df[COL_DATA].isna().all():
            df[COL_DATA] = pd.to_datetime(df[COL_DATA], dayfirst=True, errors="coerce")
    
    # Adicionar coluna dia
    if COL_DATA in df.columns:
        df["dia"] = df[COL_DATA].dt.date

    # filtros
    if start_date and COL_DATA in df.columns:
        df = df[df[COL_DATA] >= start_date]
    if end_date and COL_DATA in df.columns:
        df = df[df[COL_DATA] <= end_date + timedelta(days=1)]

    # nome final
    sd_txt = start_date.strftime("%Y-%m-%d") if start_date else "inicio"
    ed_txt = end_date.strftime("%Y-%m-%d") if end_date else datetime.now().strftime("%Y-%m-%d")

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    filename = out_dir / f"relatorio_color_sports_{sd_txt}_ate_{ed_txt}.xlsx"

    # ---------------------- CRIA XLSX ----------------------
    with pd.ExcelWriter(filename, engine="openpyxl") as writer:

        # PREÇOS
        if "precos" in include:
            dfc = df[df[COL_VENDEDOR].str.contains("Color Sports", case=False, na=False)]
            dfc2 = df[~df[COL_VENDEDOR].str.contains("Color Sports", case=False, na=False)]

            serie_cs = dfc.groupby("dia")[COL_PRECO].mean().reset_index().rename(columns={COL_PRECO: "Color"})
            serie_conc = dfc2.groupby("dia")[COL_PRECO].mean().reset_index().rename(columns={COL_PRECO: "Conc"})

            comp = pd.merge(serie_cs, serie_conc, on="dia", how="outer").sort_values("dia")
            _df_to_excel(writer, comp, "Precos")

        # BUYBOX
        if "buybox" in include:
            wins, bb = _buybox_stats(df)
            _df_to_excel(writer, wins, "BuyBox_Wins")

            if bb["loss_events"]:
                pd.DataFrame(bb["loss_events"], columns=["SKU", "Prev", "New", "Dia"])\
                    .to_excel(writer, sheet_name="BuyBox_Loss", index=False)

        # CONCORRÊNCIA
        if "concorrencia" in include:
            agg = _aggressiveness_delta(df)
            _df_to_excel(writer, agg, "Agressividade")

        # SUBSTITUIÇÕES
        if "substituicoes" in include:
            subs = _competitor_substitutions(df)
            _df_to_excel(writer, subs, "Substituicoes")

        # VOLATILIDADE
        if "produtos" in include:
            vol = _top_volatile_skus(df)
            _df_to_excel(writer, vol, "Volatilidade")

        # BRUTOS
        if "brutos" in include:
            _df_to_excel(writer, df, "DadosBrutos")

        # IA
        df_ia = None
        if "ia" in include:
            df_ia = detectar_oportunidades(df)
            _df_to_excel(writer, df_ia, "Oportunidades IA")

    # ---------------------- PDF IA ----------------------
    if "ia" in include and df_ia is not None:
        pdf_path = str(filename).replace(".xlsx", "_IA.pdf")
        gerar_pdf_ia(df_ia, pdf_path, df_hist=df, start_date=start_date, end_date=end_date)

    return str(filename)
