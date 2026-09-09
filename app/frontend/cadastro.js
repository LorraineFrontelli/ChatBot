// ============================================================
// Configuração
// ============================================================
const API_BASE = "http://localhost:8000";
const REGISTER_ENDPOINT = `${API_BASE}/register`;
const TOKEN_STORAGE_KEY = "assistente_access_token";

if (localStorage.getItem(TOKEN_STORAGE_KEY)) {
  window.location.href = "index.html";
}

// ============================================================
// Elementos
// ============================================================
const form = document.getElementById("cadastro-form");
const inputNome = document.getElementById("nome");
const inputEmail = document.getElementById("email");
const inputSenha = document.getElementById("senha");
const botaoCadastrar = document.getElementById("cadastrar");
const hint = document.getElementById("hint");

function setHint(texto, comoErro = false, comoSucesso = false) {
  hint.textContent = texto || "";
  hint.classList.toggle("is-error", comoErro);
  hint.classList.toggle("is-success", comoSucesso);
}

// ============================================================
// Envio
// ============================================================
form.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  setHint("");

  if (inputSenha.value.length < 8) {
    setHint("A senha precisa ter no mínimo 8 caracteres.", true);
    return;
  }

  botaoCadastrar.disabled = true;

  try {
    const resposta = await fetch(REGISTER_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        nome: inputNome.value.trim(),
        email: inputEmail.value.trim(),
        senha: inputSenha.value,
      }),
    });

    if (!resposta.ok) {
      const detalhe = await resposta.json().catch(() => null);
      const mensagem = Array.isArray(detalhe?.detail)
        ? detalhe.detail.map((d) => d.msg).join(" ")
        : detalhe?.detail || "Não foi possível concluir o cadastro.";
      throw new Error(mensagem);
    }

    setHint("Conta criada! Redirecionando para o login…", false, true);
    setTimeout(() => {
      window.location.href = "login.html";
    }, 1200);
  } catch (erro) {
    setHint(
      erro.message.includes("Failed to fetch")
        ? `Não foi possível falar com a API em ${API_BASE}.`
        : erro.message,
      true
    );
    botaoCadastrar.disabled = false;
  }
});
