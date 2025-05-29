from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
import json
import os
import re

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'chave_para_desenvolvimento')

# Diretórios e arquivos
os.makedirs('dados', exist_ok=True)
USERS_FILE = os.path.join('dados', 'usuarios.json')
ASSUNTOS_FILE = os.path.join('dados', 'assuntos.json')
PERGUNTAS_FILE = os.path.join('dados', 'perguntas.json')
COMENTARIOS_FILE = os.path.join('dados', 'comentarios.json')
RELATORIOS_FILE = os.path.join('dados', 'relatorios.json')

DATABASE = {
    'comentarios': COMENTARIOS_FILE,
    'perguntas': PERGUNTAS_FILE,
    'relatorios': RELATORIOS_FILE
}

# Inicializar dados
def init_data():
    # Inicializa assuntos se não existir
    if not os.path.exists(ASSUNTOS_FILE):
        assuntos = [
            {"id": 1, "nome": "Lógica Proposicional", "descricao": "Fundamentos da lógica proposicional"},
            {"id": 2, "nome": "Tabelas Verdade", "descricao": "Construção e análise de tabelas verdade"},
            {"id": 3, "nome": "Argumentos Válidos", "descricao": "Identificação de argumentos lógicos válidos"},
            {"id": 4, "nome": "Formas Normais", "descricao": "Formas normais conjuntiva e disjuntiva"}
        ]
        with open(ASSUNTOS_FILE, 'w', encoding='utf-8') as f:
            json.dump(assuntos, f, ensure_ascii=False, indent=4)
    # Inicializa usuarios se não existir
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f)
    # Inicializa os demais arquivos para evitar erros
    for path in [PERGUNTAS_FILE, COMENTARIOS_FILE, RELATORIOS_FILE]:
        if not os.path.exists(path):
            with open(path, 'w', encoding='utf-8') as f:
                json.dump([], f)

init_data()

# Funções auxiliares
def validar_email(email):
    regex = r'^[^@]+@[^@]+\.[^@]+$'
    return re.match(regex, email) is not None

def carregar_dados(caminho):
    if os.path.exists(caminho):
        with open(caminho, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                if caminho == USERS_FILE:
                    return {}
                return []
    else:
        if caminho == USERS_FILE:
            return {}
        return []

def salvar_dados(caminho, dados):
    with open(caminho, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

def carregar_usuarios():
    return carregar_dados(USERS_FILE)

def salvar_usuarios(usuarios):
    salvar_dados(USERS_FILE, usuarios)

def carregar_assuntos():
    return carregar_dados(ASSUNTOS_FILE)

def carregar_perguntas():
    return carregar_dados(PERGUNTAS_FILE)

def carregar_comentarios():
    return carregar_dados(COMENTARIOS_FILE)

def salvar_comentarios(comentarios):
    salvar_dados(COMENTARIOS_FILE, comentarios)

# Rotas principais
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    if request.method == 'POST':
        usuarios = carregar_usuarios()
        email = request.form.get('email', '').strip().lower()
        nome = request.form.get('nome', '').strip()
        senha = request.form.get('senha', '').strip()

        erros = []
        if not nome:
            erros.append('Nome é obrigatório.')
        if not email or not validar_email(email):
            erros.append('E-mail inválido ou ausente.')
        if len(senha) < 6:
            erros.append('Senha deve ter pelo menos 6 caracteres.')
        if email in usuarios:
            erros.append('E-mail já cadastrado.')

        if erros:
            for erro in erros:
                flash(erro, 'error')
            return render_template('cadastrar.html', nome=nome, email=email)

        usuarios[email] = {
            'nome': nome,
            'senha': generate_password_hash(senha),
            'data_cadastro': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        salvar_usuarios(usuarios)
        flash('Cadastro realizado com sucesso! Faça login.', 'success')
        return redirect(url_for('entrar'))

    return render_template('cadastrar.html')

@app.route('/entrar', methods=['GET', 'POST'])
def entrar():
    if 'usuario_logado' in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        senha = request.form.get('senha', '').strip()

        usuarios = carregar_usuarios()

        if not usuarios:
            flash('Nenhum usuário cadastrado. Por favor, cadastre-se primeiro.', 'error')
            return redirect(url_for('cadastrar'))

        usuario = usuarios.get(email)

        if not usuario or not check_password_hash(usuario['senha'], senha):
            flash('E-mail ou senha incorretos', 'error')
            return render_template('entrar.html', email=email)

        session['usuario_logado'] = email
        session['nome_usuario'] = usuario['nome']
        flash(f'Bem-vindo(a), {usuario["nome"]}!', 'success')
        return redirect(url_for('home'))

    return render_template('entrar.html')


@app.route('/home')
def home():
    if 'usuario_logado' not in session:
        flash('Faça login para acessar esta página.', 'error')
        return redirect(url_for('entrar'))

    usuarios = carregar_usuarios()
    email = session['usuario_logado']
    nome = usuarios.get(email, {}).get('nome', 'Usuário')

    return render_template('home.html',
                           user={'name': nome},
                           assuntos=carregar_assuntos())

@app.route('/assunto/<int:assunto_id>')
def assunto(assunto_id):
    assuntos = carregar_assuntos()
    assunto_info = next((a for a in assuntos if a['id'] == assunto_id), None)

    if not assunto_info:
        return "Assunto não encontrado", 404

    perguntas = carregar_perguntas()
    perguntas_assunto = [p for p in perguntas if p.get('assunto_id') == assunto_id]

    if not perguntas_assunto:
        return "Nenhuma pergunta encontrada", 404

    return render_template('assunto.html',
                           perguntas=perguntas_assunto,
                           assunto_id=assunto_id,
                           assunto_nome=assunto_info.get('nome', ''))

@app.route('/api/comentarios', methods=['GET', 'POST'])
def api_comentarios():
    if 'usuario_logado' not in session:
        return jsonify({'error': 'Não autorizado'}), 401

    user_name = session.get('nome_usuario', 'Anônimo')

    if request.method == 'GET':
        assunto_id = request.args.get('assunto')
        questao_id = request.args.get('questao_id')
        comentarios = carregar_comentarios()
        # Filtra considerando que assunto e questao_id são strings
        filtrados = [c for c in comentarios if str(c.get('assunto')) == str(assunto_id) and str(c.get('questao_id')) == str(questao_id)]
        return jsonify(filtrados)

    if request.method == 'POST':
        data = request.get_json()
        if not data or 'texto' not in data or 'assunto' not in data or 'questao_id' not in data:
            return jsonify({'error': 'Dados incompletos'}), 400

        novo = {
            'usuario': user_name,
            'texto': data['texto'],
            'assunto': data['assunto'],
            'questao_id': data['questao_id'],
            'timestamp': datetime.now().isoformat()
        }
        comentarios = carregar_comentarios()
        comentarios.append(novo)
        salvar_comentarios(comentarios)
        return jsonify({'status': 'success'})

@app.route('/api/questao/<questao_id>')
def api_questao(questao_id):
    if 'usuario_logado' not in session:
        return jsonify({'error': 'Não autorizado'}), 401

    questoes = carregar_perguntas()
    questao = next((q for q in questoes if str(q.get('id')) == str(questao_id)), None)
    if not questao:
        return jsonify({'error': 'Questão não encontrada'}), 404
    return jsonify(questao)

@app.route('/api/salvar_relatorio', methods=['POST'])
def salvar_relatorio():
    if 'usuario_logado' not in session:
        return jsonify({'error': 'Não autorizado'}), 401

    dados = request.get_json()
    if not dados:
        return jsonify({'error': 'Dados inválidos'}), 400

    relatorios = carregar_dados(DATABASE['relatorios'])

    try:
        novo_relatorio = {
            'usuario': session['usuario_logado'],
            'assunto': dados.get('assunto', 'Desconhecido'),
            'acertos': int(dados.get('acertos', 0)),
            'erros': int(dados.get('erros', 0)),
            'tempo': float(dados.get('tempo', 0)),
            'data': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    except (ValueError, TypeError):
        return jsonify({'error': 'Dados numéricos inválidos'}), 400

    relatorios.append(novo_relatorio)
    salvar_dados(DATABASE['relatorios'], relatorios)
    return jsonify({'status': 'sucesso'})

@app.route('/minha_conta')
def minha_conta():
    if 'usuario_logado' not in session:
        flash('Faça login para acessar sua conta.', 'error')
        return redirect(url_for('entrar'))

    email = session['usuario_logado']
    usuarios = carregar_usuarios()
    usuario = usuarios.get(email)

    if not usuario:
        flash('Usuário não encontrado.', 'error')
        return redirect(url_for('entrar'))

    return render_template('minha_conta.html',
                           nome=usuario.get('nome'),
                           email=email,
                           data_cadastro=usuario.get('data_cadastro'))

@app.route('/relatorio')
def relatorio():
    if 'usuario_logado' not in session:
        flash('Faça login para acessar o relatório.', 'error')
        return redirect(url_for('entrar'))

    relatorios = carregar_dados(DATABASE['relatorios'])
    usuario = session['usuario_logado']
    relatorios_usuario = [r for r in relatorios if r['usuario'] == usuario]
    return render_template('relatorio.html', relatorios=relatorios_usuario)

@app.route('/sair')
def sair():
    session.clear()
    flash('Você saiu da conta.', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
