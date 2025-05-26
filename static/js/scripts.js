// ================================================================================================
// MÓDULO DE AUTENTICAÇÃO
// ================================================================================================

const AuthModule = (function() {
    // Configuração
    const config = {
        minPasswordLength: 6,
        usersKey: 'logprop_users',
        currentUserKey: 'logprop_current_user'
    };

    // Elementos DOM
    const elements = {
        loginForm: document.getElementById('loginForm'),
        registerForm: document.getElementById('registerForm'),
        logoutBtn: document.getElementById('logoutBtn')
    };

    // Inicialização
    function init() {
        // Verificar se forms existem na página
        if (elements.loginForm) setupLogin();
        if (elements.registerForm) setupRegister();
        if (elements.logoutBtn) setupLogout();
        
        // Verificar autenticação ao carregar
        checkAuthState();
    }

    // Configurar formulário de login
    function setupLogin() {
        elements.loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const email = this.querySelector('#email').value.trim();
            const password = this.querySelector('#password').value.trim();
            
            const user = authenticateUser(email, password);
            
            if (user) {
                setCurrentUser(user);
                window.location.href = 'home.html';
            } else {
                alert('E-mail ou senha incorretos!');
            }
        });
    }

    // Configurar formulário de cadastro
    function setupRegister() {
        elements.registerForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const name = this.querySelector('#name').value.trim();
            const email = this.querySelector('#email').value.trim();
            const password = this.querySelector('#password').value.trim();
            const confirmPassword = this.querySelector('#confirmPassword').value.trim();
            
            // Validações
            if (password !== confirmPassword) {
                alert('As senhas não coincidem!');
                return;
            }
            
            if (password.length < config.minPasswordLength) {
                alert(`A senha deve ter pelo menos ${config.minPasswordLength} caracteres!`);
                return;
            }
            
            // Registrar usuário
            const user = registerUser(name, email, password);
            
            if (user) {
                setCurrentUser(user);
                window.location.href = 'home.html';
            } else {
                alert('Este e-mail já está cadastrado!');
            }
        });
    }

    // Configurar logout
    function setupLogout() {
        elements.logoutBtn.addEventListener('click', function() {
            logoutUser();
            window.location.href = 'index.html';
        });
    }

    // Autenticar usuário
    function authenticateUser(email, password) {
        const users = getUsers();
        return users.find(user => user.email === email && user.password === password);
    }

    // Registrar novo usuário
    function registerUser(name, email, password) {
        const users = getUsers();
        
        // Verificar se usuário já existe
        if (users.some(user => user.email === email)) {
            return null;
        }
        
        const newUser = {
            id: Date.now(),
            name,
            email,
            password,
            createdAt: new Date().toISOString(),
            photo: 'assets/icones/icone-usuario.png',
            progress: {}
        };
        
        users.push(newUser);
        localStorage.setItem(config.usersKey, JSON.stringify(users));
        
        return newUser;
    }

    // Definir usuário atual
    function setCurrentUser(user) {
        localStorage.setItem(config.currentUserKey, JSON.stringify(user));
    }

    // Obter usuário atual
    function getCurrentUser() {
        return JSON.parse(localStorage.getItem(config.currentUserKey));
    }

    // Obter todos os usuários
    function getUsers() {
        return JSON.parse(localStorage.getItem(config.usersKey)) || [];
    }

    // Fazer logout
    function logoutUser() {
        localStorage.removeItem(config.currentUserKey);
    }

    // Verificar estado de autenticação
    function checkAuthState() {
        const currentUser = getCurrentUser();
        const authPages = ['entrar.html', 'cadastrar.html'];
        const protectedPages = ['home.html', 'exercicios.html', 'minha-conta.html'];
        
        const currentPage = window.location.pathname.split('/').pop();
        
        // Redirecionar se não autenticado em página protegida
        if (!currentUser && protectedPages.includes(currentPage)) {
            window.location.href = 'entrar.html';
        }
        
        // Redirecionar se autenticado em página de auth
        if (currentUser && authPages.includes(currentPage)) {
            window.location.href = 'home.html';
        }
    }

    // API Pública
    return {
        init,
        getCurrentUser,
        logoutUser
    };
})();

// ================================================================================================
// MÓDULO DE EXERCÍCIOS
// ================================================================================================
const ExercisesModule = (function () {
    const config = {
        apiBaseUrl: 'http://localhost:5000'
    };

    const state = {
        currentQuestion: 0,
        answers: [],
        score: 0,
        answered: false,
        selectedOption: null,
        startTime: null,
        questionStartTime: null,
        totalTime: 0,
        currentAssunto: null,
        currentSet: []  // ADICIONADO: conjunto de questões carregadas
    };

    const elements = {
        exerciseContainer: document.getElementById('exercise-container'),
        actionButton: document.getElementById('action-button'),
        resultsContainer: document.getElementById('results-container'),
        progressCompleted: document.getElementById('progress-completed'),
        progressText: document.getElementById('progress-text'),
        homeButton: document.getElementById('home-button'),
        timeDisplay: document.getElementById('time-display')
    };

    function init() {
        if (!elements.exerciseContainer) return;

        state.currentAssunto = document.body.dataset.assunto;
        if (!state.currentAssunto) {
            console.error('Assunto não definido no data-attribute do body');
            return;
        }

        state.startTime = new Date();
        state.currentQuestion = 0;
        state.score = 0;
        state.answers = [];
        state.totalTime = 0;

        loadQuestions();  // Agora carregamos todas as questões do assunto
        setupEventListeners();
        updateProgress();
        startTimer();
    }

    async function loadQuestions() {
        try {
            const response = await fetch(`${config.apiBaseUrl}/api/questoes/${state.currentAssunto}`);
            if (!response.ok) throw new Error('Erro ao carregar questões');

            const questions = await response.json();
            state.currentSet = questions;
            loadQuestion();  // Carrega a primeira questão
        } catch (error) {
            console.error('Erro:', error);
            elements.exerciseContainer.innerHTML = `
                <div class="error-message">
                    <p>Erro ao carregar as questões. Por favor, tente novamente.</p>
                    <button onclick="window.location.reload()">Recarregar</button>
                </div>
            `;
        }
    }

    function loadQuestion() {
        state.questionStartTime = new Date();
        state.answered = false;
        state.selectedOption = null;

        const question = state.currentSet[state.currentQuestion];
        if (!question) {
            showResults();
            return;
        }
        renderQuestion(question);
    }

    function renderQuestion(question) {
        let html = `
            <div class="question-header">
                <h2 class="question-title">${question.title || 'Questão'}</h2>
                ${question.level ? `<div class="question-level">Nível: ${question.level}</div>` : ''}
            </div>
            <div class="question-text">${question.text}</div>
            <div class="options-container" id="options-container">
        `;

        question.opcoes.forEach((opt, i) => {
            const letter = String.fromCharCode(65 + i);
            html += `
                <div class="option" data-index="${i}">
                    <span class="option-letter">${letter}</span> ${opt}
                </div>
            `;
        });

        html += `</div><div class="feedback" id="feedback"></div>`;
        elements.exerciseContainer.innerHTML = html;
        elements.actionButton.disabled = true;
        elements.actionButton.textContent = 'Responder';

        document.querySelectorAll('.option').forEach(opt =>
            opt.addEventListener('click', () => selectOption(opt))
        );
    }

    function selectOption(optionElement) {
        if (state.answered) return;
        document.querySelectorAll('.option').forEach(opt => opt.classList.remove('selected'));
        optionElement.classList.add('selected');
        state.selectedOption = Number(optionElement.dataset.index);
        elements.actionButton.disabled = false;
    }

    function checkAnswer() {
        if (state.selectedOption === null) {
            alert('Selecione uma opção antes de responder.');
            return;
        }

        submitAnswer();
    }

    async function submitAnswer() {
        const questionTime = Math.floor((new Date() - state.questionStartTime) / 1000);
        state.totalTime += questionTime;

        const question = state.currentSet[state.currentQuestion];

        try {
            const response = await fetch(`${config.apiBaseUrl}/api/resposta/${state.currentAssunto}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    questao_id: question.id,    // USAR ID DA QUESTÃO CORRETA
                    resposta: state.selectedOption,
                    tempo: questionTime
                })
            });

            if (!response.ok) throw new Error('Erro ao enviar resposta');

            const result = await response.json();

            const feedback = document.getElementById('feedback');
            feedback.className = `feedback ${result.correta ? 'correct' : 'incorrect'}`;
            feedback.innerHTML = `
                <div class="feedback-title">${result.correta ? '✓ Correto!' : '✗ Incorreto'}</div>
                <div>${result.explicacao}</div>
            `;

            // Registrar resposta no estado para relatório
            state.answers.push({
                questionId: question.id,
                selectedOption: state.selectedOption,
                correta: result.correta,
                tempo: questionTime
            });

            if (result.correta) state.score++;
            state.answered = true;
            elements.actionButton.textContent = 'Próxima Questão';
            updateProgress();
        } catch (error) {
            console.error('Erro:', error);
            alert('Erro ao enviar resposta. Por favor, tente novamente.');
        }
    }

    function nextStep() {
        state.currentQuestion++;
        if (state.currentQuestion >= state.currentSet.length) {
            showResults();
        } else {
            loadQuestion();
            updateProgress();
        }
    }

    function showResults() {
        const totalTime = Math.floor((new Date() - state.startTime) / 1000);
        const minutes = Math.floor(totalTime / 60);
        const seconds = totalTime % 60;
        const incorrectAnswers = state.currentSet.length - state.score;

        document.getElementById('correct-answers').textContent = state.score;
        document.getElementById('incorrect-answers').textContent = incorrectAnswers;
        document.getElementById('time-spent').textContent = `${minutes}m ${seconds}s`;

        elements.exerciseContainer.style.display = 'none';
        elements.actionButton.style.display = 'none';
        elements.resultsContainer.style.display = 'block';

        const resultData = {
            topic: window.location.pathname,
            date: new Date().toISOString(),
            correct: state.score,
            incorrect: incorrectAnswers,
            timeSpent: totalTime,
            questions: state.currentSet.length,
            details: state.answers
        };

        const allResults = JSON.parse(localStorage.getItem(storageKey)) || [];
        allResults.push(resultData);
        localStorage.setItem(storageKey, JSON.stringify(allResults));
    }

    function updateProgress() {
        const total = state.currentSet.length;
        const current = state.currentQuestion + (state.answered ? 1 : 0);
        if(elements.progressCompleted) elements.progressCompleted.style.width = `${(current / total) * 100}%`;
        if(elements.progressText) elements.progressText.textContent = `${current}/${total}`;
    }

    function setupEventListeners() {
        if (elements.actionButton) {
            elements.actionButton.addEventListener('click', () => {
                if (!state.answered) {
                    checkAnswer();
                } else {
                    nextStep();
                }
            });
        }

        if (elements.homeButton) {
            elements.homeButton.addEventListener('click', () => {
                window.location.href = 'home.html';
            });
        }
    }

    function startTimer() {
        if (!elements.timeDisplay) return;
        setInterval(() => {
            if (!state.startTime) return;
            const elapsed = Math.floor((new Date() - state.startTime) / 1000);
            const mins = Math.floor(elapsed / 60);
            const secs = elapsed % 60;
            elements.timeDisplay.textContent = `${mins}m ${secs}s`;
        }, 1000);
    }

    document.addEventListener('DOMContentLoaded', function () {
        if (document.body.classList.contains('pagina-exercicio')) {
            ExercisesModule.init();
        }
    });

        // Atualiza barra de progresso
    const progresso = ((questaoAtual + 1) / questoes.length) * 100;
    document.getElementById('barra-progresso').style.width = progresso + '%';


    return { init };
})();



// ================================================================================================
// MÓDULO DE RELATÓRIOS/DASHBOARD
// ================================================================================================

async function buscarDados() {
  const dataInicio = document.getElementById('dataInicio').value;
  const dataFim = document.getElementById('dataFim').value;

  const res = await fetch(`http://localhost:5000/api/desempenho?inicio=${dataInicio}&fim=${dataFim}`);
  const dados = await res.json();

  document.getElementById('acertos').innerText = `✅ Acertos: ${dados.acertos}`;
  document.getElementById('erros').innerText = `❌ Erros: ${dados.erros}`;
  document.getElementById('tempo').innerText = `⏱️ Tempo Médio: ${formatarTempo(dados.tempo_medio_segundos)}`;

  desenharGraficoDesempenho(dados.desempenho_tempo);
  desenharGraficoErrosCategoria(dados.erros_por_categoria);
}

function formatarTempo(segundos) {
  const m = Math.floor(segundos / 60);
  const s = segundos % 60;
  return `${m}m ${s}s`;
}

let chartLinha, chartPizza;

function desenharGraficoDesempenho(data) {
  const labels = data.map(d => d.data);
  const acertos = data.map(d => d.acertos);
  const erros = data.map(d => d.erros);

  if (chartLinha) chartLinha.destroy();

  const ctx = document.getElementById('graficoDesempenho').getContext('2d');
  chartLinha = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        { label: 'Acertos', data: acertos, borderColor: 'green', fill: false },
        { label: 'Erros', data: erros, borderColor: 'red', fill: false }
      ]
    }
  });
}

function desenharGraficoErrosCategoria(data) {
  const labels = data.map(d => d.categoria);
  const valores = data.map(d => d.quantidade);

  if (chartPizza) chartPizza.destroy();

  const ctx = document.getElementById('graficoErrosCategoria').getContext('2d');
  chartPizza = new Chart(ctx, {
    type: 'pie',
    data: {
      labels: labels,
      datasets: [{
        data: valores,
        backgroundColor: ['#ff6384', '#36a2eb', '#ffcd56', '#4bc0c0', '#9966ff']
      }]
    }
  });
}


// ================================================================================================
// MÓDULO DE CONTA DO USUÁRIO
// ================================================================================================

const AccountModule = (function() {
    // Inicialização
    function init() {
        if (!document.getElementById('conta-container')) return;
        
        loadUserProfile();
        setupEventListeners();
    }

    // Carregar perfil
    function loadUserProfile() {
        const user = AuthModule.getCurrentUser();
        // Preencher formulários com dados do usuário
    }

    // Configurar listeners
    function setupEventListeners() {
        // Foto, alterar dados, senha, etc.
    }

    // Atualizar perfil
    function updateProfile(profileData) {
        // Validar e salvar alterações
    }

    // API Pública
    return {
        init
    };
})();

// ================================================================================================
// INICIALIZAÇÃO GERAL
// ================================================================================================

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar módulos conforme a página
    AuthModule.init();
    
    const path = window.location.pathname;
    
    if (path.includes('exercicios.html')) {
        ExercisesModule.init();
    } else if (path.includes('relatorio.html')) {
        DashboardModule.init();
    } else if (path.includes('minha-conta.html')) {
        AccountModule.init();
    }
});

// ================================================================================================
// UTILITÁRIOS
// ================================================================================================

const Utils = {
    formatDate(dateString) {
        const options = { year: 'numeric', month: 'short', day: 'numeric' };
        return new Date(dateString).toLocaleDateString('pt-BR', options);
    },
    
    formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}m ${secs}s`;
    },
    
    calculatePercentage(value, total) {
        return total > 0 ? Math.round((value / total) * 100) : 0;
    }
};