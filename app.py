from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta, datetime
from functools import wraps
import json
import os

app = Flask(__name__)
app.secret_key = "minha_chave_super_secreta"
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)
app.config['TEMPLATES_AUTO_RELOAD'] = True

relatorios = []

users_db = {
    "teste@teste.com": {
        "name": "Usuario Teste",
        "password": generate_password_hash("123"),
        "progresso": {},
        "registro": "2025-01-01 12:00:00"
    }
}

questions_db = {
    'proposicoes': [
        {
            'pergunta': 'Qual das alternativas abaixo e uma proposicao?',
            'respostas': ['Feche a porta.', 'O ceu e azul.', 'Por que voce fez isso?', 'Leia o livro.'],
            'correta': 1,
            'explicacao': 'Proposicao e uma sentenca declarativa que pode ser verdadeira ou falsa. "O ceu e azul" e uma proposicao.'
        }
    ],
    'tabelas': [
        {
            'pergunta': 'Qual e o valor logico de "p ∧ q" se p = V e q = F?',
            'respostas': ['V', 'F', 'Indeterminado', 'Nao e possivel saber'],
            'correta': 1,
            'explicacao': 'A conjuncao (∧) so e verdadeira se ambas as proposicoes forem verdadeiras. Nesse caso, p = V e q = F, entao p ∧ q = F.'
        }
    ],
    'tautologias': [
        {
            'pergunta': 'Qual e o valor logico de "p ∧ q" se p = V e q = F?',
            'respostas': ['V', 'F', 'Indeterminado', 'Nao e possivel saber'],
            'correta': 1,
            'explicacao': 'A conjuncao (∧) so e verdadeira se ambas as proposicoes forem verdadeiras. Nesse caso, p = V e q = F, entao p ∧ q = F.'
        }
    ],
    'equivalencias': [
        {
            'pergunta': 'Qual e o valor logico de "p ∧ q" se p = V e q = F?',
            'respostas': ['V', 'F', 'Indeterminado', 'Nao e possivel saber'],
            'correta': 1,
            'explicacao': 'A conjuncao (∧) so e verdadeira se ambas as proposicoes forem verdadeiras. Nesse caso, p = V e q = F, entao p ∧ q = F.'
        }
    ]
}
questions_db['todos'] = sum(questions_db.values(), [])

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario' not in session:
            flash('Voce precisa estar logado para acessar esta pagina.', 'error')
            return redirect(url_for('entrar'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/entrar', methods=['GET', 'POST'])
def entrar():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '').strip()

        if not email or not senha:
            flash('Preencha todos os campos', 'error')
            return render_template('entrar.html')

        user = users_db.get(email)
        if user and check_password_hash(user['password'], senha):
            session['usuario'] = email
            return redirect(url_for('home'))

        flash('Credenciais invalidas', 'error')
        return render_template('entrar.html')

    return render_template('entrar.html')

@app.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']

        if email in users_db:
            flash('E-mail ja cadastrado', 'error')
            return redirect(url_for('cadastrar'))

        if len(senha) < 6:
            flash('A senha deve ter pelo menos 6 caracteres', 'error')
            return redirect(url_for('cadastrar'))

        users_db[email] = {
            'name': nome,
            'password': generate_password_hash(senha),
            'registro': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'progresso': {}
        }

        flash('Cadastro realizado com sucesso! Faca login.', 'success')
        return redirect(url_for('entrar'))

    return render_template('cadastrar.html')

@app.route('/home')
@login_required
def home():
    email = session['usuario']
    user = users_db.get(email)

    assuntos = [
        ('Proposições e Conectivos Logicos', 'Faça exercicios de reforço', 'proposicoes'),
        ('Construcao de tabelas-verdade simples', 'Faça exercicios de reforço', 'tabelas'),
        ('Identificacao de tautologias, contradicoes e contingencias', 'Faça exercicios de reforço', 'tautologias'),
        ('Equivalencias logicas', 'Faça exercicios de reforço', 'equivalencias'),
        ('Todos os Conteudos', 'Faça exercicios de reforço', 'todos')
    ]

    return render_template('home.html', user={"name": user['name']}, assuntos=assuntos)

@app.route('/relatorio')
@login_required
def relatorio():
    email = session['usuario']
    user = users_db.get(email)

    caminho = os.path.join('dados', 'relatorios.json')
    relatorios_usuario = []

    if os.path.exists(caminho):
        with open(caminho, 'r', encoding='utf-8') as f:
            try:
                todos_relatorios = json.load(f)
                # Filtra só relatórios do usuário atual, se tiver um campo usuario/email salvo (adicione no salvar_relatorio)
                relatorios_usuario = [r for r in todos_relatorios if r.get('usuario') == email]
            except json.JSONDecodeError:
                relatorios_usuario = []

    # Agora você pode montar dados agregados a partir de relatorios_usuario
    total_questoes = sum(r.get('acertos', 0) + r.get('erros', 0) for r in relatorios_usuario)
    acertos = sum(r.get('acertos', 0) for r in relatorios_usuario)
    erros = total_questoes - acertos
    tempo_total = sum(r.get('tempo', 0) for r in relatorios_usuario)
    tempo_medio = f"{round(tempo_total / total_questoes, 1)}s" if total_questoes else "0s"
    progresso_geral = (acertos / total_questoes * 100) if total_questoes else 0

    # Agrupa por assunto
    assuntos = {}
    for r in relatorios_usuario:
        a = r.get('assunto')
        if a not in assuntos:
            assuntos[a] = {'acertos': 0, 'erros': 0, 'tempo': 0, 'qtd': 0}
        assuntos[a]['acertos'] += r.get('acertos', 0)
        assuntos[a]['erros'] += r.get('erros', 0)
        assuntos[a]['tempo'] += r.get('tempo', 0)
        assuntos[a]['qtd'] += 1

    por_assunto = []
    for assunto, dados in assuntos.items():
        total = dados['acertos'] + dados['erros']
        percentual_acertos = round((dados['acertos'] / total) * 100, 1) if total else 0
        tempo_medio_assunto = round(dados['tempo'] / dados['qtd'], 1) if dados['qtd'] else 0
        por_assunto.append({
            "assunto": assunto.capitalize(),
            "acertos": dados['acertos'],
            "erros": dados['erros'],
            "percentual_acertos": percentual_acertos,
            "tempo": tempo_medio_assunto
        })

    return render_template(
        'relatorio.html',
        total_questoes=total_questoes,
        acertos=acertos,
        erros=erros,
        tempo_medio=tempo_medio,
        progresso_geral=round(progresso_geral, 1),
        feedback="Bom trabalho!" if progresso_geral >= 70 else "Continue praticando.",
        por_assunto=por_assunto
    )

@app.route('/salvar_relatorio', methods=['POST'])
@login_required
def salvar_relatorio():
    dados = request.get_json()
    email = session['usuario']

    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400

    novo_registro = {
        "usuario": email,  # <- adiciona o usuario para depois filtrar
        "assunto": dados.get("assunto"),
        "acertos": dados.get("acertos"),
        "erros": dados.get("erros"),
        "tempo": dados.get("tempo")
    }

    caminho = os.path.join('dados', 'relatorios.json')
    relatorios = []

    if os.path.exists(caminho):
        with open(caminho, 'r', encoding='utf-8') as f:
            try:
                relatorios = json.load(f)
            except json.JSONDecodeError:
                relatorios = []

    relatorios.append(novo_registro)

    with open(caminho, 'w', encoding='utf-8') as f:
        json.dump(relatorios, f, ensure_ascii=False, indent=4)

    return jsonify({"mensagem": "Relatório salvo com sucesso"}), 200

@app.route('/assunto/<assunto_id>')
@login_required
def assunto(assunto_id):
    with open('dados/perguntas.json', 'r', encoding='utf-8') as f:
        todas_perguntas = json.load(f)

    perguntas_do_assunto = [p for p in todas_perguntas if p['id'].startswith(assunto_id)]

    return render_template('assunto.html', perguntas=perguntas_do_assunto, assunto_id=assunto_id)

@app.route('/responder', methods=['POST'])
@login_required
def responder():
    assunto_id = request.form.get('assunto_id')
    indice = int(request.form.get('indice'))
    resposta_usuario = int(request.form.get('resposta'))

    pergunta = questions_db.get(assunto_id, [])[indice]
    resposta_correta = (resposta_usuario == pergunta['correta'])

    email = session['usuario']
    user = users_db[email]

    user['progresso'].setdefault(assunto_id, {'acertos': 0, 'erros': 0})

    if resposta_correta:
        user['progresso'][assunto_id]['acertos'] += 1
        flash('Resposta correta!', 'success')
    else:
        user['progresso'][assunto_id]['erros'] += 1
        flash(f'Resposta incorreta. {pergunta["explicacao"]}', 'error')

    return redirect(url_for('assunto', assunto_id=assunto_id))

@app.route('/minha_conta')
@login_required
def minha_conta():
    email = session['usuario']
    user = users_db.get(email)
    return render_template('minha_conta.html',
                           user=user,
                           registro=user.get('registro', 'Data nao disponivel'),
                           progresso=user.get('progresso', {}))

@app.route('/registrar_resultado/<assunto_id>', methods=['POST'])
@login_required
def registrar_resultado(assunto_id):
    dados = request.get_json()
    email = session['usuario']
    user = users_db[email]

    user['progresso'].setdefault(assunto_id, {'acertos': 0, 'erros': 0, 'tempo_total': 0, 'tentativas': 0})

    acertos = dados.get('acertos', 0)
    total = dados.get('total', 0)
    tempo = dados.get('tempo', 0)

    user['progresso'][assunto_id]['acertos'] += acertos
    user['progresso'][assunto_id]['erros'] += (total - acertos)
    user['progresso'][assunto_id]['tempo_total'] += tempo
    user['progresso'][assunto_id]['tentativas'] += 1

    return jsonify({"status": "ok"})

@app.route('/salvar_progresso', methods=['POST'])
@login_required
def salvar_progresso():
    data = request.get_json()
    assunto_id = data.get('assunto_id')
    acertos = data.get('acertos', 0)
    total = data.get('total', 1)
    tempo = data.get('tempo', 0)

    email = session['usuario']
    user = users_db.get(email)
    if user:
        progresso = user.setdefault('progresso', {})
        progresso[assunto_id] = {
            'acertos': acertos,
            'erros': total - acertos,
            'percentual_acertos': round((acertos / total) * 100, 1),
            'tempo': tempo
        }

    return '', 204

@app.route('/sair')
def sair():
    session.pop('usuario', None)
    flash('Voce saiu com sucesso.', 'success')
    return redirect(url_for('entrar'))

if __name__ == '__main__':
    app.run(debug=True)
