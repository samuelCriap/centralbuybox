# main.py - coleta assincrona com protecao anti-deteccao maxima
import aiohttp
import asyncio
import pandas as pd
import random
import re
import hashlib
import time
from datetime import datetime
from tqdm.asyncio import tqdm
from db_client import ler_planilha, salvar_planilha, atualizar_historico

BACKUP_CSV = "backup_netshoes_temp.csv"
REQ_POR_LOTE = 500          # Lotes de 500
PAUSA_ENTRE_LOTES = 3       # Pausa entre lotes
REQ_CONCORRENTES = 50       # 50 concorrentes
MAX_TENTATIVAS = 3
TIMEOUT_API = 15

# ==================== ANTI-DETECTION: ADAPTIVE RATE LIMITING ====================
class AdaptiveRateLimiter:
    """Ajusta velocidade automaticamente baseado em sinais de throttling"""
    def __init__(self):
        self.slow_responses = 0
        self.total_requests = 0
        self.current_delay_multiplier = 1.0
    
    def record_response(self, response_time: float):
        self.total_requests += 1
        # Se resposta demorou mais de 5 segundos, considera lenta
        if response_time > 5.0:
            self.slow_responses += 1
        
        # Se mais de 20% das respostas estao lentas, aumenta delays
        if self.total_requests > 10:
            slow_ratio = self.slow_responses / self.total_requests
            if slow_ratio > 0.2:
                self.current_delay_multiplier = min(3.0, self.current_delay_multiplier * 1.2)
            elif slow_ratio < 0.05:
                self.current_delay_multiplier = max(0.5, self.current_delay_multiplier * 0.9)
    
    def get_multiplier(self) -> float:
        return self.current_delay_multiplier

# Instancia global do rate limiter
rate_limiter = AdaptiveRateLimiter()

# ==================== ANTI-DETECTION: USER AGENTS ====================
# Lista extensa de user agents reais de diferentes navegadores/OS
USER_AGENTS = [
    # Chrome Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # Chrome Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    # Chrome Linux
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    # Firefox Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0",
    # Firefox Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.1; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0",
    # Safari Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    # Edge Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
    # Opera
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 OPR/105.0.0.0",
]

# ==================== ANTI-DETECTION: ACCEPT LANGUAGES ====================
ACCEPT_LANGUAGES = [
    "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "pt-BR,pt;q=0.9,en;q=0.8",
    "pt-BR,pt;q=0.8,en-US;q=0.6,en;q=0.4",
    "pt,pt-BR;q=0.9,en-US;q=0.8,en;q=0.7",
    "pt-BR,pt;q=0.9",
]

# ==================== ANTI-DETECTION: SEC-CH-UA ====================
SEC_CH_UA_LIST = [
    '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    '"Not_A Brand";v="8", "Chromium";v="119", "Google Chrome";v="119"',
    '"Firefox";v="121"',
    '"Microsoft Edge";v="120", "Chromium";v="120"',
]

SKU_REGEX = re.compile(r"/([A-Z0-9-]{5,})")


def extrair_sku(link: str | None) -> str | None:
    if not link:
        return None
    m = SKU_REGEX.search(str(link))
    return m.group(1) if m else None


def _generate_session_id():
    """Gera ID de sessao aleatorio para parecer usuario real"""
    return hashlib.md5(str(random.random()).encode()).hexdigest()[:16]


def _get_random_headers(sku: str = None, session_id: str = None):
    """
    Gera headers completamente aleatorios para cada requisicao
    Simula comportamento de navegador real
    """
    ua = random.choice(USER_AGENTS)
    is_chrome = "Chrome" in ua and "Edg" not in ua
    is_firefox = "Firefox" in ua
    is_safari = "Safari" in ua and "Chrome" not in ua
    
    headers = {
        "User-Agent": ua,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": random.choice(ACCEPT_LANGUAGES),
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Cache-Control": random.choice(["no-cache", "max-age=0"]),
    }
    
    # Headers especificos de Chrome
    if is_chrome:
        headers["sec-ch-ua"] = random.choice(SEC_CH_UA_LIST[:2])
        headers["sec-ch-ua-mobile"] = "?0"
        headers["sec-ch-ua-platform"] = random.choice(['"Windows"', '"macOS"', '"Linux"'])
        headers["Sec-Fetch-Dest"] = "empty"
        headers["Sec-Fetch-Mode"] = "cors"
        headers["Sec-Fetch-Site"] = "same-origin"
    
    # Referer aleatorio mas realista
    referers = [
        "https://www.netshoes.com.br/",
        "https://www.netshoes.com.br/busca?q=tenis",
        "https://www.netshoes.com.br/calcados/tenis",
        f"https://www.netshoes.com.br/produto/{sku}" if sku else "https://www.netshoes.com.br/",
    ]
    headers["Referer"] = random.choice(referers)
    
    # Adiciona DNT aleatoriamente
    if random.random() > 0.5:
        headers["DNT"] = "1"
    
    # Adiciona Pragma aleatoriamente  
    if random.random() > 0.7:
        headers["Pragma"] = "no-cache"
    
    return headers


def _format_price(centavos):
    """Converte preco de centavos para reais"""
    if centavos is None:
        return "-"
    try:
        return round(float(centavos) / 100, 2)
    except:
        return "-"


async def _random_delay():
    """
    Delay aleatorio com distribuicao GAUSSIANA (mais natural)
    Ajustado dinamicamente pelo rate limiter adaptativo
    """
    # Distribuicao gaussiana centrada em 0.3s com desvio padrao de 0.15s
    base_delay = max(0.05, random.gauss(0.3, 0.15))
    
    # Aplica multiplicador adaptativo
    multiplier = rate_limiter.get_multiplier()
    final_delay = base_delay * multiplier
    
    # Garante limites razoaveis
    final_delay = max(0.05, min(5.0, final_delay))
    
    await asyncio.sleep(final_delay)


def _get_random_timeout():
    """
    Timeout variavel para simular diferentes velocidades de rede
    """
    # Timeout base + variacao gaussiana
    return max(5, min(30, random.gauss(TIMEOUT_API, 3)))


async def coletar_dados_pdp(session: aiohttp.ClientSession, sku: str, session_id: str):
    """
    Usa a PDP API para coletar multiplos vendedores
    Com protecoes anti-deteccao
    """
    resultado = {
        "Site Disponivel": "Nao",
        "Status Final": "SEM ESTOQUE",
        "Vendedor 1": "-", "Preco 1": "-", "Frete 1": "-",
        "Vendedor 2": "-", "Preco 2": "-", "Frete 2": "-",
        "Vendedor 3": "-", "Preco 3": "-", "Frete 3": "-",
    }
    
    api_url = f"https://www.netshoes.com.br/pdp-api/api/product/{sku}"
    
    # Delay aleatorio ANTES da requisicao
    await _random_delay()
    
    # Headers aleatorios para cada requisicao
    headers = _get_random_headers(sku, session_id)
    
    # Retry com backoff exponencial
    for attempt in range(3):
        start_time = time.time()
        try:
            # Timeout variavel para cada requisicao
            timeout = aiohttp.ClientTimeout(total=_get_random_timeout())
            async with session.get(api_url, headers=headers, timeout=timeout) as r:
                if r.status == 200:
                    data = await r.json()
                    
                    if not data or not isinstance(data, dict):
                        resultado["Status Final"] = "SEM ESTOQUE"
                        return resultado
                    
                    resultado["Site Disponivel"] = "Sim"
                    
                    current = data.get("currentProduct", {})
                    prices = current.get("prices", [])
                    
                    if not prices or not isinstance(prices, list):
                        resultado["Status Final"] = "SEM ESTOQUE"
                        return resultado
                    
                    # Contador separado para ofertas disponiveis
                    available_count = 0
                    
                    for idx, offer in enumerate(prices):
                        if available_count >= 3:  # Maximo 3 vendedores
                            break
                            
                        if not isinstance(offer, dict):
                            continue
                        
                        # VERIFICAR DISPONIBILIDADE
                        is_available = offer.get("available", True)
                        if not is_available:
                            continue  # Pular ofertas sem estoque
                        
                        # Incrementar contador apenas para ofertas disponiveis
                        available_count += 1
                        num = available_count
                        
                        # Vendedor - pode ser objeto ou string
                        seller_data = offer.get("seller", {})
                        if isinstance(seller_data, dict):
                            seller_name = seller_data.get("name", "")
                            seller_id = seller_data.get("id", "")
                        else:
                            seller_name = offer.get("sellerName", "") or str(seller_data)
                            seller_id = ""
                        
                        if seller_name:
                            resultado[f"Vendedor {num}"] = str(seller_name)[:50]
                        
                        # BUSCAR PRECO REAL NA API POR VENDEDOR
                        # A API /frdmprcsts retorna o preco final correto com todos os descontos
                        price = None
                        if seller_id and sku:
                            try:
                                seller_api_url = f"https://www.netshoes.com.br/frdmprcsts/{sku}/{seller_id}/lazy"
                                await _random_delay()  # Delay antes de cada requisicao
                                seller_timeout = aiohttp.ClientTimeout(total=_get_random_timeout())
                                async with session.get(seller_api_url, headers=_get_random_headers(sku, session_id), timeout=seller_timeout) as seller_r:
                                    if seller_r.status == 200:
                                        seller_data_json = await seller_r.json()
                                        # Priorizar salePrice que contem o preco final com descontos
                                        price = seller_data_json.get("salePrice") or seller_data_json.get("finalPriceWithoutPaymentBenefitDiscount")
                            except:
                                pass  # Se falhar, usa o preco da API principal
                        
                        # Fallback: usar preco da API principal se nao conseguiu da API por vendedor
                        if not price:
                            price = offer.get("finalPriceWithoutPaymentBenefitDiscount") or offer.get("saleInCents") or offer.get("listInCents")
                        
                        if price:
                            resultado[f"Preco {num}"] = _format_price(price)
                        
                        # Frete
                        free_shipping = offer.get("freeShipping", False)
                        if free_shipping:
                            resultado[f"Frete {num}"] = "Gratis"
                        else:
                            shipping = offer.get("shipping") or offer.get("shippingCost")
                            if shipping:
                                resultado[f"Frete {num}"] = _format_price(shipping)
                            else:
                                resultado[f"Frete {num}"] = "Pago"
                    
                    if resultado["Vendedor 1"] != "-" and resultado["Preco 1"] != "-":
                        resultado["Status Final"] = "OK"
                    else:
                        resultado["Status Final"] = "SEM ESTOQUE"
                    
                    # Registrar tempo de resposta para rate limiting adaptativo
                    response_time = time.time() - start_time
                    rate_limiter.record_response(response_time)
                    
                    return resultado
                
                elif r.status == 403:
                    # Bloqueado - espera mais e tenta com headers diferentes
                    wait_time = (attempt + 1) * 3 + random.uniform(1, 3)
                    await asyncio.sleep(wait_time)
                    headers = _get_random_headers(sku, session_id)  # Novos headers
                    continue
                    
                elif r.status == 429:
                    # Rate limit - espera bem mais
                    await asyncio.sleep(10 + random.uniform(1, 5))
                    continue
                else:
                    resultado["Status Final"] = "SEM ESTOQUE"
                    return resultado
                    
        except asyncio.TimeoutError:
            await asyncio.sleep(2)
            continue
        except Exception as e:
            await asyncio.sleep(1)
            continue
    
    resultado["Status Final"] = "FALHA"
    return resultado


async def verificar_produto(session: aiohttp.ClientSession, i: int, row: pd.Series, session_id: str):
    link = str(row.get("link", "")).strip()
    sku = extrair_sku(link)
    if not sku:
        return i, {
            "Site Disponivel": "Nao",
            "Status Final": "Erro - SKU nao encontrado",
            "Vendedor 1": "-", "Preco 1": "-", "Frete 1": "-",
            "Vendedor 2": "-", "Preco 2": "-", "Frete 2": "-",
            "Vendedor 3": "-", "Preco 3": "-", "Frete 3": "-",
        }
    resultado = await coletar_dados_pdp(session, sku, session_id)
    resultado["Data Verificacao"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    return i, resultado


async def processar_lote(df: pd.DataFrame, session: aiohttp.ClientSession, indices: list[int], tentativa: int, sem_conc: asyncio.Semaphore, session_id: str):
    tasks = [verificar_produto(session, i, df.loc[i], session_id) for i in indices]
    async def sem_task(coro):
        async with sem_conc:
            return await coro
    coros = [sem_task(t) for t in tasks]
    resultados = []
    for coro in tqdm(asyncio.as_completed(coros), total=len(coros), desc=f"Tentativa {tentativa} - Lote {indices[0]}>{indices[-1]}"):
        try:
            i, result = await coro
            resultados.append((i, result))
        except Exception as e:
            pass
    for i, result in resultados:
        for k, v in result.items():
            df.at[i, k] = v


async def main():
    df = ler_planilha()
    
    if df.empty:
        print("[AVISO] Nenhum produto encontrado no banco. Importe produtos primeiro.")
        return
    
    for col in ["Site Disponivel", "Status Final", "Data Verificacao",
                "Vendedor 1", "Preco 1", "Frete 1",
                "Vendedor 2", "Preco 2", "Frete 2",
                "Vendedor 3", "Preco 3", "Frete 3"]:
        if col not in df.columns:
            df[col] = ""
    
    total = len(df)
    print(f"[INFO] Total de produtos a verificar: {total}")
    print(f"[INFO] Modo: PDP API com protecao anti-deteccao")
    print(f"[INFO] Concorrencia: {REQ_CONCORRENTES} | Lote: {REQ_POR_LOTE}")
    indices_all = list(range(total))
    
    # Gera session ID para esta execucao
    session_id = _generate_session_id()
    print(f"[INFO] Session ID: {session_id}")
    
    # Connector com limites conservadores
    connector = aiohttp.TCPConnector(
        limit=REQ_CONCORRENTES,
        limit_per_host=REQ_CONCORRENTES,
        ssl=False,
        ttl_dns_cache=300,
        use_dns_cache=True,
    )
    sem_conc = asyncio.Semaphore(REQ_CONCORRENTES)
    
    # Timeout global mais generoso
    timeout = aiohttp.ClientTimeout(total=30, connect=10)
    
    # Cookie jar para persistencia de sessao (simula navegador real)
    cookie_jar = aiohttp.CookieJar(unsafe=True)
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout, cookie_jar=cookie_jar) as session:
        tentativa = 1
        indices_para_tentar = indices_all.copy()
        
        while tentativa <= MAX_TENTATIVAS and indices_para_tentar:
            print(f"\n[RETRY] Iniciando tentativa {tentativa}/{MAX_TENTATIVAS} - {len(indices_para_tentar)} itens")
            
            # Embaralha indices para nao seguir ordem previsivel
            random.shuffle(indices_para_tentar)
            
            for start in range(0, len(indices_para_tentar), REQ_POR_LOTE):
                subset = indices_para_tentar[start:start + REQ_POR_LOTE]
                lote_num = start // REQ_POR_LOTE + 1
                print(f"[LOTE] Processando lote {lote_num} ({len(subset)} itens)...")
                
                await processar_lote(df, session, subset, tentativa, sem_conc, session_id)
                df.to_csv(BACKUP_CSV, index=False)
                
                # Pausa entre lotes com variacao
                if start + REQ_POR_LOTE < len(indices_para_tentar):
                    pausa = PAUSA_ENTRE_LOTES + random.uniform(0, 3)
                    print(f"[PAUSA] Aguardando {pausa:.1f}s antes do proximo lote...")
                    await asyncio.sleep(pausa)
            
            indices_para_tentar = [i for i, row in df.iterrows() 
                                   if str(row.get("Status Final", "")).strip() in ["", "TIMEOUT", "ERRO", "FALHA"]]
            print(f"[RETRY] Itens para proxima tentativa: {len(indices_para_tentar)}")
            
            if indices_para_tentar:
                # Pausa maior entre tentativas
                print(f"[PAUSA] Aguardando 15s antes da proxima tentativa...")
                await asyncio.sleep(15)
            
            tentativa += 1
    
    salvar_planilha(df)
    df.to_csv(BACKUP_CSV, index=False)
    
    ok = int((df["Status Final"] == "OK").sum())
    sem_estoque = int((df["Status Final"] == "SEM ESTOQUE").sum())
    falhas = int((df["Status Final"].isin(["FALHA", "ERRO", "TIMEOUT"])).sum())
    
    print("\n=== Resumo final ===")
    print(f"   OK.............. {ok}")
    print(f"   Sem estoque..... {sem_estoque}")
    print(f"   Falhas.......... {falhas}")
    
    v2 = len(df[df["Vendedor 2"] != "-"])
    v3 = len(df[df["Vendedor 3"] != "-"])
    frete_gratis = len(df[df["Frete 1"] == "Gratis"])
    print(f"   Com Vendedor 2.. {v2}")
    print(f"   Com Vendedor 3.. {v3}")
    print(f"   Frete Gratis.... {frete_gratis}")
    
    print("\n[HIST] Salvando historico no SQLite...")
    await asyncio.to_thread(atualizar_historico, df, 60)
    print("[HIST] Historico atualizado com sucesso!")


if __name__ == "__main__":
    asyncio.run(main())
