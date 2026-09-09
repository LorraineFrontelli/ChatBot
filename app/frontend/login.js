// ============================================================
// Configuração
// ============================================================
const API_BASE = "http://localhost:8000";
const LOGIN_ENDPOINT = `${API_BASE}/login`;
const TOKEN_STORAGE_KEY = "assistente_access_token";

// Já logado? Não faz sentido ficar na tela de login.
if (localStorage.getItem(TOKEN_STORAGE_KEY)) {
  window.location.href = "index.html";
}

// ============================================================
// Elementos
// ============================================================
const form = document.getElementById("login-form");
const inputEmail = document.getElementById("email");
const inputSenha = document.getElementById("senha");
const botaoEntrar = document.getElementById("entrar");
const hint = document.getElementById("hint");

function setHint(texto, comoErro = false) {
  hint.textContent = texto || "";
  hint.classList.toggle("is-error", comoErro);
}

// ============================================================
// Envio
// ============================================================
form.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  setHint("");
  botaoEntrar.disabled = true;

  try {
    const resposta = await fetch(LOGIN_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: inputEmail.value.trim(),
        senha: inputSenha.value,
      }),
    });

    if (!resposta.ok) {
      const detalhe = await resposta.json().catch(() => null);
      throw new Error(detalhe?.detail || "E-mail ou senha inválidos.");
    }

    const dados = await resposta.json();
    localStorage.setItem(TOKEN_STORAGE_KEY, dados.access_token);
    window.location.href = "index.html";
  } catch (erro) {
    setHint(
      erro.message.includes("Failed to fetch")
        ? `Não foi possível falar com a API em ${API_BASE}.`
        : erro.message,
      true
    );
    botaoEntrar.disabled = false;
  }
});
