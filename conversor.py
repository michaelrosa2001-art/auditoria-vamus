import pdfplumber
import json
import re

pdf_path = "vamus_horarios.pdf"
base_dados_horarios = {}

def limpar_nome_paragem(nome):
    if not nome:
        return ""
    return nome.replace("\n", " ").strip()

with pdfplumber.open(pdf_path) as pdf:
    for page_num, page in enumerate(pdf.pages):
        text = page.extract_text()
        if not text:
            continue
            
        lines = text.split("\n")
        if not lines:
            continue
            
        # Detecta o número e nome da linha (ex: "1 Alagoa – Castro Marim")
        primeira_linha = lines[0].strip()
        match_linha = re.match(r"^(\d+)\s+(.+)$", primeira_linha)
        if not match_linha:
            continue
            
        num_linha = match_linha.group(1)
        nome_linha = match_linha.group(2).strip()
        
        if num_linha not in base_dados_horarios:
            base_dados_horarios[num_linha] = {
                "Ascendente": { "Dias Úteis": {}, "Sábado": {}, "Domingo e Feriado": {} },
                "Descendente": { "Dias Úteis": {}, "Sábado": {}, "Domingo e Feriado": {} }
            }
            
       # === AJUSTE DE PRECISÃO: Reduzimos a tolerância para não "arrastar" colunas ===
        table = page.extract_table(table_settings={
            "vertical_strategy": "text",
            "horizontal_strategy": "text",
            "snap_y_tolerance": 2,
            "snap_x_tolerance": 2
        })
        
        if not table or len(table) < 3:
            continue
            
        sentido_atual = "Ascendente"
        row_calendario = table[1]
        
        for row in table[2:]:
            if not row or not row[0]:
                continue
                
            paragem_nome = limpar_nome_paragem(row[0])
            
            # Deteta se mudou o sentido na tabela
            if "VOLTA" in paragem_nome or "INBOUND" in paragem_nome:
                sentido_atual = "Descendente"
                if len(table) > table.index(row) + 1:
                    row_calendario = table[table.index(row) + 1]
                continue
                
            # Ignora palavras de controle
            if paragem_nome in ["IDA", "VOLTA", "OUTBOUND", "INBOUND", "A-U", "E-U", "FE-U", "A-S", "A-DF", "FEV-U"]:
                continue
                
            for col_idx in range(1, len(row)):
                hora = row[col_idx]
                if not hora:
                    continue
                
                hora = hora.strip()
                # Suporta formatos de hora de 1 ou 2 dígitos (ex: "8:00" ou "08:00")
                if hora == "-" or not re.match(r"^\d{1,2}:\d{2}$", hora):
                    continue
                    
                # Determina o tipo de dia (U = Dias Úteis, S = Sábado, DF = Domingo/Feriado)
                cal_code = row_calendario[col_idx] if col_idx < len(row_calendario) else "U"
                if not cal_code:
                    cal_code = "U"
                
                tipo_dia = "Dias Úteis"
                if "S" in cal_code:
                    tipo_dia = "Sábado"
                elif "DF" in cal_code:
                    tipo_dia = "Domingo e Feriado"
                    
                # Descobre qual é a hora de partida desta viagem específica da coluna
                hora_partida = None
                for r in table[2:]:
                    if r[0] and ("VOLTA" in r[0] or "INBOUND" in r[0]) and sentido_atual == "Ascendente":
                        break
                    if r[0] and ("VOLTA" in r[0] or "INBOUND" in r[0]) and sentido_atual == "Descendente":
                        continue
                    if r[col_idx] and re.match(r"^\d{1,2}:\d{2}$", r[col_idx].strip()):
                        hora_partida = r[col_idx].strip()
                        break
                
                if not hora_partida:
                    hora_partida = hora
                    
                viagem_key = f"Partida às {hora_partida}"
                
                viagens_da_linha = base_dados_horarios[num_linha][sentido_atual][tipo_dia]
                if viagem_key not in viagens_da_linha:
                    viagens_da_linha[viagem_key] = []
                    
                viagens_da_linha[viagem_key].append({
                    "nome": paragem_nome,
                    "horaPrevista": hora
                })

# Grava o resultado estruturado em formato JSON
with open("baseDadosHorarios.json", "w", encoding="utf-8") as f:
    json.dump(base_dados_horarios, f, ensure_ascii=False, indent=2)

print("Sincronização concluída! baseDadosHorarios.json gerado com sucesso!")