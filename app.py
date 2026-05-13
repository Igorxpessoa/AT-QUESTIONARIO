import os
import json
import uuid
import requests
from datetime import datetime
from flask import Flask, request, jsonify

# ── Configuração do Firestore REST API ────────────────────────────────────────
FIREBASE_API_KEY = os.environ.get("APIKEY")
FIREBASE_PROJECT_ID = os.environ.get("PROJECTID")

FIRESTORE_BASE_URL = (
    f"https://firestore.googleapis.com/v1/"
    f"projects/{FIREBASE_PROJECT_ID}/databases/(default)/documents"
)

def firestore_save(collection: str, data: dict) -> str:
    """
    Salva um documento no Firestore via REST API (API Key pública).
    Retorna o ID do documento criado.
    """
    doc_id = str(uuid.uuid4()).replace("-", "")[:20]
    url = f"{FIRESTORE_BASE_URL}/{collection}/{doc_id}?key={FIREBASE_API_KEY}"

    # Converte o dicionário Python para o formato de campos do Firestore
    fields = {}
    for k, v in data.items():
        if isinstance(v, bool):
            fields[k] = {"booleanValue": v}
        elif isinstance(v, int):
            fields[k] = {"integerValue": str(v)}
        elif isinstance(v, float):
            fields[k] = {"doubleValue": v}
        elif v is None:
            fields[k] = {"nullValue": None}
        else:
            fields[k] = {"stringValue": str(v)}

    payload = {"fields": fields}
    response = requests.patch(url, json=payload, timeout=10)

    if response.status_code not in (200, 201):
        raise Exception(f"Firestore erro {response.status_code}: {response.text}")

    return doc_id

if not FIREBASE_API_KEY or not FIREBASE_PROJECT_ID:
    print("❌ Variáveis de ambiente 'APIKEY' ou 'PROJECTID' não encontradas.")
else:
    print(f"✅ Firestore REST API configurado para o projeto: {FIREBASE_PROJECT_ID}")

# ── Configuração do Flask ──────────────────────────────────────────────────────
app = Flask(__name__)

# ── HTML ───────────────────────────────────────────────────────────────────────
HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Questionario de resolução de Check-in e Checkout Automático</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --auvo:       #6B4EFF;
    --auvo-dark:  #4930D4;
    --auvo-light: #EBE7FF;
    --bg:         #F7F6F2;
    --card:       #FFFFFF;
    --text:       #1A1A2E;
    --muted:      #6B6B80;
    --border:     #E2E0F0;
    --green:      #16A34A;
    --green-bg:   #F0FDF4;
    --radius:     14px;
    --radius-sm:  8px;
  }

  body {
    font-family: 'DM Sans', sans-serif;
    background: var(--bg);
    min-height: 100vh;
    display: flex; flex-direction: column; align-items: center;
    padding: 2rem 1rem 4rem; color: var(--text);
  }

  .header { width: 100%; max-width: 560px; display: flex; align-items: center; gap: 14px; margin-bottom: 2.5rem; }
  .logo-pill { background: var(--auvo); color: white; font-family: 'DM Serif Display', serif; font-size: 18px; padding: 7px 18px; border-radius: 40px; letter-spacing: -0.3px; }
  .header-title { font-size: 13px; font-weight: 500; color: var(--muted); letter-spacing: 0.05em; text-transform: uppercase; }

  .progress-wrap { width: 100%; max-width: 560px; margin-bottom: 1.75rem; }
  .progress-meta { display: flex; justify-content: space-between; font-size: 12px; color: var(--muted); margin-bottom: 8px; }
  .progress-track { height: 3px; background: var(--border); border-radius: 2px; overflow: hidden; }
  .progress-fill { height: 100%; background: var(--auvo); border-radius: 2px; transition: width 0.4s cubic-bezier(.4,0,.2,1); }

  .card { width: 100%; max-width: 560px; background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); padding: 2rem; animation: fadeUp 0.3s ease both; }
  @keyframes fadeUp { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }

  .badge { display: inline-flex; align-items: center; gap: 5px; font-size: 11px; font-weight: 500; color: var(--auvo); background: var(--auvo-light); padding: 4px 10px; border-radius: 20px; margin-bottom: 1rem; letter-spacing: 0.03em; text-transform: uppercase; }
  .question { font-family: 'DM Serif Display', serif; font-size: 22px; line-height: 1.4; color: var(--text); margin-bottom: 1.5rem; font-weight: 400; }

  .input-group { margin-bottom: 1.5rem; }
  .input-group label { display: block; font-size: 13px; font-weight: 500; color: var(--muted); margin-bottom: 8px; }
  .input-field { width: 100%; padding: 12px 16px; border: 1.5px solid var(--border); border-radius: var(--radius-sm); font-family: inherit; font-size: 15px; outline: none; transition: border-color 0.2s; }
  .input-field:focus { border-color: var(--auvo); }

  .options { display: flex; flex-direction: column; gap: 10px; }
  .opt { display: flex; align-items: flex-start; gap: 14px; padding: 14px 16px; border: 1.5px solid var(--border); border-radius: var(--radius-sm); cursor: pointer; background: transparent; transition: all 0.15s; text-align: left; font-family: inherit; width: 100%; }
  .opt:hover { border-color: var(--auvo); background: var(--auvo-light); }
  .opt.selected { border-color: var(--auvo); background: var(--auvo-light); }

  .radio-dot { width: 18px; height: 18px; min-width: 18px; border-radius: 50%; border: 2px solid #C4C0D8; margin-top: 1px; display: flex; align-items: center; justify-content: center; }
  .radio-dot::after { content: ''; width: 7px; height: 7px; border-radius: 50%; background: var(--auvo); opacity: 0; }
  .opt.selected .radio-dot::after { opacity: 1; }

  .nav { display: flex; align-items: center; justify-content: space-between; margin-top: 1.75rem; padding-top: 1.25rem; border-top: 1px solid var(--border); }
  .btn-back { font-size: 13px; font-weight: 500; color: var(--muted); background: none; border: none; cursor: pointer; padding: 8px 0; font-family: inherit; }
  .btn-next { background: var(--auvo); color: white; border: none; border-radius: var(--radius-sm); padding: 10px 26px; font-size: 14px; font-weight: 500; cursor: pointer; font-family: inherit; transition: all 0.15s; }
  .btn-next:disabled { opacity: 0.35; cursor: default; }

  .confirm-icon { width: 56px; height: 56px; border-radius: 50%; background: var(--green-bg); display: flex; align-items: center; justify-content: center; font-size: 26px; margin-bottom: 1.25rem; }
  .confirm-title { font-family: 'DM Serif Display', serif; font-size: 24px; color: var(--text); margin-bottom: 0.5rem; }
  .confirm-id { display: inline-block; font-size: 12px; background: var(--auvo-light); color: var(--auvo); padding: 4px 12px; border-radius: 20px; font-weight: 500; }
  
  .hidden { display: none !important; }
</style>
</head>
<body>

<div class="header">
  <div class="logo-pill">auvo</div>
  <div class="header-title">Diagnóstico de Check-in Automático</div>
</div>

<div class="progress-wrap">
  <div class="progress-meta">
    <span id="stepLabel">Identificação</span>
    <span id="pctLabel">0%</span>
  </div>
  <div class="progress-track">
    <div class="progress-fill" id="progressFill" style="width:0%"></div>
  </div>
</div>

<div class="card" id="step0">
  <span class="badge">👤 Identificação</span>
  <h2 class="question">Para começar, quem está realizando este diagnóstico?</h2>
  <div class="input-group">
    <label>Nome do Técnico</label>
    <input type="text" id="input_nome" class="input-field" placeholder="Ex: João Silva" oninput="validateStep0()">
  </div>
  <div class="input-group">
    <label>Empresa</label>
    <input type="text" id="input_empresa" class="input-field" placeholder="Nome da empresa" oninput="validateStep0()">
  </div>
  <div class="nav">
    <button class="btn-back" disabled>← Voltar</button>
    <button class="btn-next" id="n0" disabled onclick="saveTextAndGo(1)">Começar →</button>
  </div>
</div>

<div class="card hidden" id="step1">
  <span class="badge">📱 Dispositivo</span>
  <h2 class="question">Qual é o sistema operacional do dispositivo do técnico?</h2>
  <div class="options">
    <button class="opt" onclick="pick(this,'sistema','android')"><div class="radio-dot"></div><span class="opt-text">Android</span></button>
    <button class="opt" onclick="pick(this,'sistema','ios')"><div class="radio-dot"></div><span class="opt-text">iPhone (iOS)</span></button>
  </div>
  <div class="nav">
    <button class="btn-back" onclick="goTo(0)">← Voltar</button>
    <button class="btn-next" id="n1" disabled onclick="goTo(2)">Próximo →</button>
  </div>
</div>

<div class="card hidden" id="step2">
  <span class="badge">📍 Versão do aplicativo</span>
  <h2 class="question">Qual a versão do aplicativo Auvo instalada no dispositivo?</h2>
  <div class="options">
    <button class="opt" onclick="pick(this,'versao','Maior que 2.0')"><div class="radio-dot"></div><span class="opt-text">Maior que 2.0</span></button>
    <button class="opt" onclick="pick(this,'versao','Menor que 2.0')"><div class="radio-dot"></div><span class="opt-text">Menor que 2.0</span></button>
  </div>
  <div class="nav">
    <button class="btn-back" onclick="goTo(1)">← Voltar</button>
    <button class="btn-next" id="n2" disabled onclick="goTo(3)">Próximo →</button>
  </div>
</div>

<div class="card hidden" id="step3">
  <span class="badge">⚠️ Local da falha</span>
  <h2 class="question">Onde ocorreu a falha?</h2>
  <div class="options">
    <button class="opt" onclick="pick(this,'local_falha','No momento do Check-in')"><div class="radio-dot"></div><span class="opt-text">No momento do Check-in</span></button>
    <button class="opt" onclick="pick(this,'local_falha','No momento do Checkout')"><div class="radio-dot"></div><span class="opt-text">No momento do Checkout</span></button>
    <button class="opt" onclick="pick(this,'local_falha','Outro')"><div class="radio-dot"></div><span class="opt-text">Outro</span></button>
  </div>
  <div class="nav">
    <button class="btn-back" onclick="goTo(2)">← Voltar</button>
    <button class="btn-next" id="n3" disabled onclick="goTo(4)">Próximo →</button>
  </div>
</div>

<div class="card hidden" id="step4">
  <span class="badge">📍 Localização</span>
  <h2 class="question">O aplicativo tem permissão de acessar a localização?</h2>
  <div class="options">
    <button class="opt" onclick="pick(this,'permissao_localizacao','Sim')"><div class="radio-dot"></div><span class="opt-text">Sim</span></button>
    <button class="opt" onclick="pick(this,'permissao_localizacao','Não')"><div class="radio-dot"></div><span class="opt-text">Não</span></button>
  </div>
  <div class="nav">
    <button class="btn-back" onclick="goTo(3)">← Voltar</button>
    <button class="btn-next" id="n4" disabled onclick="goTo(5)">Próximo →</button>
  </div>
</div>

<div class="card hidden" id="step5">
  <span class="badge">📍 Localização</span>
  <h2 class="question">Em permissões, a permissão de localização está setada como?</h2>
  <div class="options">
    <button class="opt" onclick="pick(this,'status_permissao','Permitir o tempo todo')"><div class="radio-dot"></div><span class="opt-text">Permitir o tempo todo</span></button>
    <button class="opt" onclick="pick(this,'status_permissao','Permitir sempre')"><div class="radio-dot"></div><span class="opt-text">Permitir sempre</span></button>
    <button class="opt" onclick="pick(this,'status_permissao','Permitir durante o uso do app')"><div class="radio-dot"></div><span class="opt-text">Permitir durante o uso do app</span></button>
  </div>
  <div class="nav">
    <button class="btn-back" onclick="goTo(4)">← Voltar</button>
    <button class="btn-next" id="n5" disabled onclick="goTo(6)">Próximo →</button>
  </div>
</div>

<div class="card hidden" id="step6">
  <span class="badge">🎯 Localização exata</span>
  <h2 class="question">A opção "Usar localização exata" está ativa nas permissões do Auvo?</h2>
  <div class="options">
    <button class="opt" onclick="pick(this,'localização_exata','Sim')"><div class="radio-dot"></div><span class="opt-text">Sim, localização exata ativada</span></button>
    <button class="opt" onclick="pick(this,'localização_exata','Não')"><div class="radio-dot"></div><span class="opt-text">Não, está usando localização aproximada</span></button>
    <button class="opt" onclick="pick(this,'localização_exata','Não sei')"><div class="radio-dot"></div><span class="opt-text">Não sei / não verifiquei</span></button>
  </div>
  <div class="nav">
    <button class="btn-back" onclick="goTo(5)">← Voltar</button>
    <button class="btn-next" id="n6" disabled onclick="goTo(7)">Próximo →</button>
  </div>
</div>

<div class="card hidden" id="step7">
  <span class="badge">🔋 Bateria / Segundo plano</span>
  <h2 class="question">A otimização de bateria está desativada para o app Auvo?</h2>
  <div class="options">
    <button class="opt" onclick="pick(this,'nivel_bateria','Sim')"><div class="radio-dot"></div><span class="opt-text">Sim, a otimização de bateria está desativada</span></button>
    <button class="opt" onclick="pick(this,'nivel_bateria','Não')"><div class="radio-dot"></div><span class="opt-text">Não, o app está sendo otimizado</span></button>
  </div>
  <div class="nav">
    <button class="btn-back" onclick="goTo(6)">← Voltar</button>
    <button class="btn-next" id="n7" disabled onclick="goTo(8)">Próximo →</button>
  </div>
</div>

<div class="card hidden" id="step8">
  <span class="badge">🗺️ Pausa no app</span>
  <h2 class="question">A opção "Pausar app por falta de uso" está ativada?</h2>
  <div class="options">
    <button class="opt" onclick="pick(this,'pausa_inatividade','Sim')"><div class="radio-dot"></div><span class="opt-text">Sim, está ativada</span></button>
    <button class="opt" onclick="pick(this,'pausa_inatividade','Não')"><div class="radio-dot"></div><span class="opt-text">Não, está desativada</span></button>
  </div>
  <div class="nav">
    <button class="btn-back" onclick="goTo(7)">← Voltar</button>
    <button class="btn-next" id="n8" disabled onclick="goTo(9)">Próximo →</button>
  </div>
</div>

<div class="card hidden" id="step9">
  <span class="badge">🏭 Notificação</span>
  <h2 class="question">O app Auvo tem permissão para enviar notificações?</h2>
  <div class="options">
    <button class="opt" onclick="pick(this,'permissao_notificacao','Sim')"><div class="radio-dot"></div><span class="opt-text">Sim, tem permissão</span></button>
    <button class="opt" onclick="pick(this,'permissao_notificacao','Não')"><div class="radio-dot"></div><span class="opt-text">Não tem permissão</span></button>
  </div>
  <div class="nav">
    <button class="btn-back" onclick="goTo(8)">← Voltar</button>
    <button class="btn-next" id="n9" disabled onclick="enviar()">Enviar Respostas →</button>
  </div>
</div>

<div class="card hidden" id="stepResult">
  <div class="confirm-icon">✅</div>
  <h2 class="confirm-title">Respostas registradas!</h2>
  <span class="confirm-id" id="confirmId"></span>
  <br><br>
  <button class="btn-restart" onclick="restart()">↺ Novo questionário</button>
</div>

<script>
const answers = {};
const TOTAL = 9; // Perguntas de diagnóstico (1 a 9)

function validateStep0() {
  const nome = document.getElementById('input_nome').value.trim();
  const empresa = document.getElementById('input_empresa').value.trim();
  document.getElementById('n0').disabled = !(nome.length > 2 && empresa.length > 1);
}

function saveTextAndGo(num) {
  answers['nome'] = document.getElementById('input_nome').value.trim();
  answers['empresa'] = document.getElementById('input_empresa').value.trim();
  goTo(num);
}

function pick(el, key, val) {
  el.closest('.options').querySelectorAll('.opt').forEach(o => o.classList.remove('selected'));
  el.classList.add('selected');
  answers[key] = val;
  const num = parseInt(el.closest('[id^="step"]').id.replace('step', ''));
  const btn = document.getElementById('n' + num);
  if (btn) btn.disabled = false;
}

function goTo(num) {
  document.querySelectorAll('[id^="step"]').forEach(s => s.classList.add('hidden'));
  document.getElementById('step' + num).classList.remove('hidden');
  
  const pct = Math.round((num / TOTAL) * 100);
  document.getElementById('progressFill').style.width = pct + '%';
  document.getElementById('stepLabel').textContent = num === 0 ? 'Identificação' : 'Pergunta ' + num + ' de ' + TOTAL;
  document.getElementById('pctLabel').textContent = pct + '%';
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

async function enviar() {
  const btn = document.getElementById('n9');
  btn.disabled = true;
  btn.textContent = 'Salvando…';

  try {
    const res = await fetch('/salvar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(answers)
    });
    const data = await res.json();
    
    if(!res.ok) throw new Error(data.erro);

    document.querySelectorAll('[id^="step"]').forEach(s => s.classList.add('hidden'));
    document.getElementById('stepResult').classList.remove('hidden');
    document.getElementById('confirmId').textContent = 'ID: ' + data.id;
  } catch (err) {
    alert('Erro ao salvar no banco de dados. Tente novamente.');
    btn.disabled = false;
    btn.textContent = 'Enviar Respostas →';
  }
}

function restart() {
  location.reload();
}
</script>
</body>
</html>"""

# ── Rotas do Flask ─────────────────────────────────────────────────────────────

@app.route('/', methods=['GET'])
def index():
    # Retorna o HTML para o navegador
    return HTML

@app.route('/salvar', methods=['POST'])
def salvar():
    try:
        # Recebe os dados do front-end
        data = request.json

        # Adiciona o timestamp
        data['criado_em'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Salva no Firestore via REST API dentro da coleção 'respostas'
        doc_id = firestore_save('respostas', data)

        # Retorna o ID do documento criado no Firestore
        return jsonify({"ok": True, "id": doc_id}), 200

    except Exception as e:
        print(f"Erro ao salvar: {e}")
        return jsonify({"ok": False, "erro": str(e)}), 500

# ── Execução ───────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    # O Render injeta dinamicamente a porta através de variável de ambiente
    port = int(os.environ.get("PORT", 8080))
    # host='0.0.0.0' é obrigatório para rodar em servidores na nuvem
    app.run(host='0.0.0.0', port=port)