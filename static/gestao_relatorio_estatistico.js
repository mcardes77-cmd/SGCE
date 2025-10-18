// JS para relatório estatístico de ocorrências

async function carregarEstatisticas() {
    try {
        const response = await fetch('/api/relatorio_estatistico');
        const data = await response.json();

        // Cards
        document.getElementById('total-ocorrencias').textContent = data.total ?? 0;
        document.getElementById('abertas-ocorrencias').textContent = data.abertas ?? 0;
        document.getElementById('finalizadas-ocorrencias').textContent = data.finalizadas ?? 0;

        // Resumo Geral (por tipo)
        let total = data.total ?? 1;
        let tipos = data.tipos ?? {};
        let resumoHTML = "";
        Object.entries(tipos).forEach(([tipo, count]) => {
            let pct = ((count / total) * 100).toFixed(1);
            resumoHTML += `<tr>
                <td>${tipo}</td>
                <td>${count}</td>
                <td>${pct}%</td>
            </tr>`;
        });
        document.getElementById('tabela-resumo-geral').innerHTML = resumoHTML;

        // Ocorrências por Sala
        if(data.por_sala){
            let porSalaHTML = "";
            data.por_sala.forEach(item => {
                let pct = ((item.total / total) * 100).toFixed(1);
                porSalaHTML += `<tr>
                    <td>${item.sala || 'Indefinida'}</td>
                    <td>${item.total}</td>
                    <td>${pct}%</td>
                    <td>${item.menos_7d ?? '-'}</td>
                    <td>${item.mais_7d ?? '-'}</td>
                    <td>${item.nao_respondidas ?? '-'}</td>
                </tr>`;
            });
            document.getElementById('tabela-por-sala').innerHTML = porSalaHTML;
        }

        // Ocorrências por Tutor
        if(data.por_tutor){
            let porTutorHTML = "";
            data.por_tutor.forEach(item => {
                porTutorHTML += `<tr>
                    <td>${item.tutor || 'Indefinido'}</td>
                    <td>${item.total}</td>
                    <td>${item.finalizadas}</td>
                    <td>${item.abertas}</td>
                    <td>${item.media_dias_resposta ?? '-'}</td>
                </tr>`;
            });
            document.getElementById('tabela-por-tutor').innerHTML = porTutorHTML;
        }

        // Gráfico Tempo de Resposta
        if(data.tempo_resposta){
            criarGraficoRespostas(data.tempo_resposta);
        }

        // Gráfico Ocorrências por Tutor
        if(data.por_tutor){
            criarGraficoTutor(data.por_tutor);
        }

        // Gráfico por tipo
        if(data.tipos){
            criarGraficoTipo(data.tipos);
        }

        // Gráfico por mês
        if(data.ocorrencias_por_mes){
            criarGraficoPorMes(data.ocorrencias_por_mes);
        }

    } catch (err) {
        document.getElementById('mensagem-status').classList.remove('hidden');
        document.getElementById('mensagem-status').textContent = 'Erro ao carregar estatísticas: ' + err;
    }
}

function criarGraficoRespostas(tempo_resposta) {
    const el = document.getElementById('chart-respostas');
    if (!el) return;
    const ctx = el.getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: tempo_resposta.labels,
            datasets: [{
                label: 'Qtd Ocorrências',
                data: tempo_resposta.valores,
                backgroundColor: 'rgba(99, 102, 241, 0.6)'
            }]
        },
        options: {
            plugins: { legend: { display: false } },
            scales: { x: { title: { display: true, text: 'Faixa de Dias' } }, y: { beginAtZero: true } }
        }
    });
}

function criarGraficoTutor(por_tutor) {
    const el = document.getElementById('chart-tutor');
    if (!el) return;
    const ctx = el.getContext('2d');
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: por_tutor.map(x => x.tutor),
            datasets: [{
                data: por_tutor.map(x => x.total),
                backgroundColor: [
                    'rgba(34,197,94,0.7)','rgba(251,191,36,0.7)',
                    'rgba(99,102,241,0.7)','rgba(239,68,68,0.7)',
                    'rgba(59,130,246,0.7)','rgba(156,163,175,0.7)'
                ]
            }]
        },
        options: {
            plugins: { legend: { position: 'bottom' } }
        }
    });
}

function criarGraficoTipo(tipos) {
    const el = document.createElement('canvas');
    el.height = 180;
    document.querySelector('section.grid').appendChild(el);
    const ctx = el.getContext('2d');
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: Object.keys(tipos),
            datasets: [{
                data: Object.values(tipos),
                backgroundColor: [
                    'rgba(99,102,241,0.7)','rgba(34,197,94,0.7)',
                    'rgba(251,191,36,0.7)','rgba(239,68,68,0.7)'
                ]
            }]
        },
        options: {
            plugins: { legend: { position: 'bottom' } }
        }
    });
}

function criarGraficoPorMes(ocorrencias_por_mes) {
    const el = document.createElement('canvas');
    el.height = 180;
    document.querySelector('section.grid').appendChild(el);
    const ctx = el.getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ocorrencias_por_mes.labels,
            datasets: [{
                label: 'Ocorrências por Mês',
                data: ocorrencias_por_mes.valores,
                backgroundColor: 'rgba(251,191,36,0.7)'
            }]
        },
        options: {
            plugins: { legend: { display: false } },
            scales: { x: { title: { display: true, text: 'Mês' } }, y: { beginAtZero: true } }
        }
    });
}

// Inicialização
window.addEventListener('DOMContentLoaded', carregarEstatisticas);
