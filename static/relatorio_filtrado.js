document.addEventListener("DOMContentLoaded", function () {
    const selectSala = document.getElementById("sala");
    const selectAluno = document.getElementById("aluno");
    const btnCarregar = document.getElementById("btn-carregar-ocorrencias");
    const areaOcorrencias = document.getElementById("area-ocorrencias");
    const areaPdf = document.getElementById("area-pdf");

    if (!selectSala || !selectAluno || !btnCarregar || !areaOcorrencias) {
        console.error("⚠️ Elementos esperados não encontrados no HTML.");
        return;
    }

    carregarSalas();

    selectSala.addEventListener("change", carregarAlunos);
    btnCarregar.addEventListener("click", carregarOcorrencias);

    async function carregarSalas() {
        selectSala.innerHTML = '<option value="">Carregando...</option>';
        try {
            const resp = await fetch("/api/salas_com_ocorrencias");
            const salas = await resp.json();
            selectSala.innerHTML = '<option value="">Selecione...</option>';
            salas.forEach(s => {
                selectSala.innerHTML += `<option value="${s.id}">${s.nome}</option>`;
            });
            selectAluno.innerHTML = '<option value="">Selecione a sala primeiro</option>';
        } catch (err) {
            console.error("Erro ao carregar salas:", err);
            selectSala.innerHTML = '<option value="">Erro ao carregar</option>';
        }
    }

    async function carregarAlunos() {
        const salaId = selectSala.value;
        if (!salaId) {
            selectAluno.innerHTML = '<option value="">Selecione a sala primeiro</option>';
            return;
        }
        selectAluno.innerHTML = '<option value="">Carregando...</option>';
        try {
            const resp = await fetch(`/api/alunos_com_ocorrencias_por_sala/${salaId}`);
            const alunos = await resp.json();
            selectAluno.innerHTML = '<option value="">Selecione...</option>';
            alunos.forEach(a => {
                selectAluno.innerHTML += `<option value="${a.id}">${a.nome}</option>`;
            });
        } catch (err) {
            console.error("Erro ao carregar alunos:", err);
            selectAluno.innerHTML = '<option value="">Erro ao carregar</option>';
        }
    }

    async function carregarOcorrencias() {
        const alunoId = selectAluno.value;
        if (!alunoId) {
            areaOcorrencias.innerHTML = '<p class="text-red-400">Selecione o aluno.</p>';
            return;
        }

        areaOcorrencias.innerHTML = "Carregando ocorrências...";
        try {
            const resp = await fetch(`/api/ocorrencias_por_aluno/${alunoId}`);
            const ocorrencias = await resp.json();

            if (!ocorrencias || ocorrencias.length === 0) {
                areaOcorrencias.innerHTML = '<p class="text-yellow-400">Nenhuma ocorrência encontrada para o aluno.</p>';
                return;
            }

            const alunoNome = ocorrencias[0]?.aluno_nome || "";
            let html = `<h3 class="text-lg mb-2">Ocorrências de <b>${alunoNome}</b></h3>
                <form id="form-ocorrencias"><ul class="mb-4">`;

            ocorrencias.forEach(o => {
                html += `<li class="mb-2">
                    <label>
                        <input type="checkbox" name="ocorrencia" value="${o.numero}" class="checkbox-ocorrencia mr-2">
                        <b>Nº ${o.numero}</b> - ${o.data_hora} (${o.status})<br>
                        <span class="text-sm">${o.descricao}</span>
                    </label>
                </li>`;
            });

            html += `</ul>
                <button type="submit" class="px-4 py-2 rounded bg-green-600 text-white hover:bg-green-700">Gerar PDF</button>
            </form>`;
            areaOcorrencias.innerHTML = html;

            document.getElementById("form-ocorrencias").onsubmit = async function (ev) {
                ev.preventDefault();
                const selecionadas = Array.from(document.querySelectorAll(".checkbox-ocorrencia:checked")).map(x => x.value);
                if (selecionadas.length === 0) {
                    alert("Selecione ao menos uma ocorrência!");
                    return;
                }
                const res = await fetch("/api/gerar_pdf_ocorrencias", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ numeros: selecionadas })
                });
                if (res.ok) {
                    const blob = await res.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement("a");
                    a.href = url;
                    a.download = `${alunoNome.replace(/\s/g, "_")}_ocorrencias.pdf`;
                    document.body.appendChild(a);
                    a.click();
                    a.remove();
                    window.URL.revokeObjectURL(url);
                    document.querySelectorAll(".checkbox-ocorrencia").forEach(cb => cb.disabled = true);
                    if (areaPdf) areaPdf.innerHTML = '<p class="text-green-400">✅ PDF gerado com sucesso!</p>';
                } else {
                    if (areaPdf) areaPdf.innerHTML = '<p class="text-red-400">Erro ao gerar PDF.</p>';
                }
            };
        } catch (err) {
            console.error("Erro ao carregar ocorrências:", err);
            areaOcorrencias.innerHTML = '<p class="text-red-400">Erro ao carregar ocorrências.</p>';
        }
    }
});
