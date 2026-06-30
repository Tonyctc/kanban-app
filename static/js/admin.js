/**
 * Kanban App - Admin Panel JavaScript
 * Gerencia interações do painel administrativo
 */

// ─── Admin Global ──────────────────────────────────────────────────

function editarUsuario(id, nome, email, perfil, corp) {
    const form = document.getElementById('form-editar-usuario');
    if (!form) return;

    form.action = `/admin/global/usuarios/${id}/editar`;
    document.getElementById('edit-user-nome').value = nome;
    document.getElementById('edit-user-email').value = email;
    document.getElementById('edit-user-perfil').value = perfil;
    document.getElementById('edit-user-corp').value = corp;
    document.getElementById('modal-editar-usuario').classList.remove('hidden');
}

function fecharModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.classList.add('hidden');
}

// ─── Admin Corporativo ─────────────────────────────────────────────

function visualizarQuadrosUsuario(userId, userName) {
    window.location.href = `/admin/corporativo/quadros/${userId}`;
}

// ─── Dashboard ─────────────────────────────────────────────────────

function confirmarExclusao(nome) {
    return confirm(`Excluir o quadro "${nome}"? Todos os cartões serão perdidos permanentemente.`);
}

// ─── Utilitários ───────────────────────────────────────────────────

// Fechar modais com tecla Escape
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        document.querySelectorAll('.fixed.z-50').forEach(function(el) {
            el.classList.add('hidden');
        });
    }
});

// Fechar modais clicando fora
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('fixed') && e.target.classList.contains('z-50')) {
        e.target.classList.add('hidden');
    }
});
