from flask import Flask, request, jsonify, send_from_directory
from leitor_placa_veiculo import ConsultaLupaVeicular
import os
import base64
import cv2
import numpy as np
import pytesseract

# Configura o caminho do executável do Tesseract para Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

app = Flask(__name__)

def extrair_placa_ocr(imagem_b64):
    # Remove prefixo data:image/jpeg;base64,
    if ',' in imagem_b64:
        imagem_b64 = imagem_b64.split(',')[1]
    img_bytes = base64.b64decode(imagem_b64)
    nparr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    # Pré-processamento: tons de cinza e binarização
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 120, 255, cv2.THRESH_BINARY)

    # Tenta OCR em tons de cinza e binarizado
    textos = []
    textos.append(('gray', pytesseract.image_to_string(gray, lang='eng')))
    textos.append(('thresh', pytesseract.image_to_string(thresh, lang='eng')))

    import re
    padrao_mercosul = r'[A-Z]{3}[0-9][A-Z][0-9]{2}'  # Ex: ABC1D23
    padrao_comum = r'[A-Z]{3}[0-9]{4}'              # Ex: ABC1234
    # Mapeamento de substituições ambíguas por posição (letra ou número)
    posicoes = [
        # 0,1,2: letras
        {'P': ['P','F','R'], 'A': ['A','V'], 'U': ['U','V'], 'N': ['N','M','W'], 'V': ['V','A','U'], 'F': ['F','P'], 'R': ['R','P'], 'M': ['M','N'], 'W': ['W','N'], 'I': ['I','L','1'], 'L': ['L','I','1']},
        {'A': ['A','V'], 'V': ['V','A'], 'U': ['U','V'], 'N': ['N','M','W'], 'M': ['M','N'], 'W': ['W','N'], 'I': ['I','L','1'], 'L': ['L','I','1']},
        {'U': ['U','V'], 'V': ['V','U'], 'A': ['A','V'], 'N': ['N','M','W'], 'M': ['M','N'], 'W': ['W','N'], 'I': ['I','L','1'], 'L': ['L','I','1']},
        # 3: número
        {'9': ['9','0','8','6'], '0': ['0','9','8','6','D','O'], '8': ['8','0','9','6','B'], '6': ['6','8','9','0','G'], '1': ['1','I','L'], '2': ['2','Z'], '5': ['5','S'], '4': ['4','A'], '7': ['7'], '3': ['3'], 'D': ['0','D'], 'O': ['0','O']},
        # 4: letra ou número
        {'I': ['I','L','1'], 'L': ['L','I','1'], '1': ['1','I','L'], '0': ['0','O','D'], 'O': ['O','0','D'], 'D': ['D','0','O'], 'A': ['A','4'], '4': ['4','A'], 'S': ['S','5'], '5': ['5','S'], 'Z': ['Z','2'], '2': ['2','Z'], 'B': ['B','8'], '8': ['8','B']},
        # 5: número
        {'7': ['7','1'], '1': ['1','I','L','7'], 'I': ['I','1','L','7'], 'L': ['L','I','1','7'], '0': ['0','O','D'], 'O': ['O','0','D'], 'D': ['D','0','O'], '8': ['8','B'], 'B': ['B','8'], '9': ['9','0','8','6'], '6': ['6','8','9','0','G'], '5': ['5','S'], 'S': ['S','5'], '2': ['2','Z'], 'Z': ['Z','2']},
        # 6: número
        {'2': ['2','Z'], 'Z': ['Z','2'], '7': ['7','1'], '1': ['1','I','L','7'], 'I': ['I','1','L','7'], 'L': ['L','I','1','7'], '0': ['0','O','D'], 'O': ['O','0','D'], 'D': ['D','0','O'], '8': ['8','B'], 'B': ['B','8'], '9': ['9','0','8','6'], '6': ['6','8','9','0','G'], '5': ['5','S'], 'S': ['S','5']}
    ]

    def gerar_variantes(placa):
        """Gera todas as variantes possíveis de uma placa trocando caracteres ambíguos por posição."""
        from itertools import product
        chars = []
        for i, c in enumerate(placa[:7]):
            if i < len(posicoes):
                chars.append(posicoes[i].get(c, [c]))
            else:
                chars.append([c])
        for variante in product(*chars):
            yield ''.join(variante)

    # Tenta todas as linhas do texto OCR de cada abordagem
    for nome, texto in textos:
        texto_corrigido = texto.upper().replace(' ', '').replace('\n', '')
        linhas = re.split(r'\n|\r', texto_corrigido)
        for linha in linhas:
            l = linha.strip()
            if len(l) >= 7:
                for variante in gerar_variantes(l):
                    if re.fullmatch(padrao_mercosul, variante):
                        return {'placa': variante, 'tipo': 'mercosul'}, texto
                    if re.fullmatch(padrao_comum, variante):
                        return {'placa': variante, 'tipo': 'comum'}, texto
        # Se não achou, tenta no texto inteiro
        if len(texto_corrigido) >= 7:
            for variante in gerar_variantes(texto_corrigido):
                if re.fullmatch(padrao_mercosul, variante):
                    return {'placa': variante, 'tipo': 'mercosul'}, texto
                if re.fullmatch(padrao_comum, variante):
                    return {'placa': variante, 'tipo': 'comum'}, texto
    return None, textos[0][1] if textos else ''
    import re
    padrao_mercosul = r'[A-Z]{3}[0-9][A-Z][0-9]{2}'  # Ex: ABC1D23
    padrao_comum = r'[A-Z]{3}[0-9]{4}'              # Ex: ABC1234
    # Mapeamento de substituições ambíguas por posição (letra ou número)
    posicoes = [
        # 0,1,2: letras
        {'P': ['P','F','R'], 'A': ['A','V'], 'U': ['U','V'], 'N': ['N','M','W'], 'V': ['V','A','U'], 'F': ['F','P'], 'R': ['R','P'], 'M': ['M','N'], 'W': ['W','N'], 'I': ['I','L','1'], 'L': ['L','I','1']},
        {'A': ['A','V'], 'V': ['V','A'], 'U': ['U','V'], 'N': ['N','M','W'], 'M': ['M','N'], 'W': ['W','N'], 'I': ['I','L','1'], 'L': ['L','I','1']},
        {'U': ['U','V'], 'V': ['V','U'], 'A': ['A','V'], 'N': ['N','M','W'], 'M': ['M','N'], 'W': ['W','N'], 'I': ['I','L','1'], 'L': ['L','I','1']},
        # 3: número
        {'9': ['9','0','8','6'], '0': ['0','9','8','6','D','O'], '8': ['8','0','9','6','B'], '6': ['6','8','9','0','G'], '1': ['1','I','L'], '2': ['2','Z'], '5': ['5','S'], '4': ['4','A'], '7': ['7'], '3': ['3'], 'D': ['0','D'], 'O': ['0','O']},
        # 4: letra ou número
        {'I': ['I','L','1'], 'L': ['L','I','1'], '1': ['1','I','L'], '0': ['0','O','D'], 'O': ['O','0','D'], 'D': ['D','0','O'], 'A': ['A','4'], '4': ['4','A'], 'S': ['S','5'], '5': ['5','S'], 'Z': ['Z','2'], '2': ['2','Z'], 'B': ['B','8'], '8': ['8','B']},
        # 5: número
        {'7': ['7','1'], '1': ['1','I','L','7'], 'I': ['I','1','L','7'], 'L': ['L','I','1','7'], '0': ['0','O','D'], 'O': ['O','0','D'], 'D': ['D','0','O'], '8': ['8','B'], 'B': ['B','8'], '9': ['9','0','8','6'], '6': ['6','8','9','0','G'], '5': ['5','S'], 'S': ['S','5'], '2': ['2','Z'], 'Z': ['Z','2']},
        # 6: número
        {'2': ['2','Z'], 'Z': ['Z','2'], '7': ['7','1'], '1': ['1','I','L','7'], 'I': ['I','1','L','7'], 'L': ['L','I','1','7'], '0': ['0','O','D'], 'O': ['O','0','D'], 'D': ['D','0','O'], '8': ['8','B'], 'B': ['B','8'], '9': ['9','0','8','6'], '6': ['6','8','9','0','G'], '5': ['5','S'], 'S': ['S','5']}
    ]

    def gerar_variantes(placa):
        """Gera todas as variantes possíveis de uma placa trocando caracteres ambíguos por posição."""
        from itertools import product
        chars = []
        for i, c in enumerate(placa[:7]):
            if i < len(posicoes):
                chars.append(posicoes[i].get(c, [c]))
            else:
                chars.append([c])
        for variante in product(*chars):
            yield ''.join(variante)

    # Tenta todas as linhas do texto OCR
    linhas = re.split(r'\n|\r', texto_corrigido)
    for linha in linhas:
        l = linha.strip()
        if len(l) >= 7:
            for variante in gerar_variantes(l):
                if re.fullmatch(padrao_mercosul, variante):
                    return {'placa': variante, 'tipo': 'mercosul'}, texto
                if re.fullmatch(padrao_comum, variante):
                    return {'placa': variante, 'tipo': 'comum'}, texto
    # Se não achou, tenta no texto inteiro
    if len(texto_corrigido) >= 7:
        for variante in gerar_variantes(texto_corrigido):
            if re.fullmatch(padrao_mercosul, variante):
                return {'placa': variante, 'tipo': 'mercosul'}, texto
            if re.fullmatch(padrao_comum, variante):
                return {'placa': variante, 'tipo': 'comum'}, texto
    return None, texto

@app.route('/ocr_placa', methods=['POST'])
def ocr_placa():
    data = request.get_json()
    imagem_b64 = data.get('imagem', '')
    resultado, texto_ocr = extrair_placa_ocr(imagem_b64)
    if resultado is None:
        return jsonify({'placa': None, 'tipo': None, 'ocr_text': texto_ocr})
    return jsonify({'placa': resultado['placa'], 'tipo': resultado['tipo'], 'ocr_text': texto_ocr})

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/consultar', methods=['POST'])
def consultar():
    data = request.get_json()
    placa = data.get('placa', '')
    consulta = ConsultaLupaVeicular(headless=True)
    resultado = consulta.consultar(placa)
    return jsonify(resultado)

if __name__ == '__main__':
    app.run(debug=True)
