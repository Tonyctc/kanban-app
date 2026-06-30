/**
 * Kanban App - Core Kanban JavaScript
 * Gerencia o Drag & Drop e interações dos cartões
 * Dependências: Sortable.js
 */

// ─── Inicialização ─────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', function() {
    initKanbanBoard();
});

function initKanbanBoard() {
    // Inicializar Sortable em cada coluna
    document.querySelectorAll('.kanban-cards').forEach(function(el) {
        if (el.dataset.sortableInitialized) return;
        el.dataset.sortableInitialized = 'true';

        new Sortable(el, {
            group: {
                name: 'kanban',
                pull: true,
                put: true
            },
            animation: 200,
            easing: 'cubic-bezier(0.25, 0.46, 0.45, 0.94)',
            ghostClass: 'kanban-card-ghost',
            dragClass: 'kanban-card-dragging',
            handle: '.kanban-card',
            delay: 150,
            delayOnTouchOnly: true,
            touchStartThreshold: 5,
            onEnd: function(evt) {
                const cardId = evt.item.dataset.cardId;
                if (!cardId) return;

                const targetColumn = evt.to.closest('.kanban-column');
                if (!targetColumn) return;

                const columnId = targetColumn.dataset.columnId;
                const newIndex = Array.from(evt.to.children).indexOf(evt.item);

                updateCardCounts();

                // Enviar movimento para o backend
                moveCardToServer(cardId, columnId, newIndex);
            }
        });
    });
}

// ─── Atualizar Contadores ─────────────────────────────────────────

function updateCardCounts() {
    document.querySelectorAll('.kanban-column').forEach(function(col) {
        const cards = col.querySelector('.kanban-cards');
        const countEl = col.querySelector('.card-count');
        if (cards && countEl) {
            countEl.textContent = cards.children.length;
        }
    });
}

// ─── API Calls ─────────────────────────────────────────────────────

function moveCardToServer(cardId, columnId, newIndex) {
    if (!window.BOARD_NAME) return;

    fetch(`/api/quadro/${window.BOARD_NAME}/card/${cardId}/mover`, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            column_id: columnId,
            new_index: newIndex
        })
    })
    .then(r => r.json())
    .then(data => {
        if (!data.success) {
            console.error('Erro ao mover cartão:', data.error);
            location.reload();
        }
    })
    .catch(err => {
        console.error('Erro de rede ao mover cartão:', err);
        location.reload();
    });
}

function criarCard(boardName, data) {
    return fetch(`/api/quadro/${boardName}/card`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    }).then(r => r.json());
}

function atualizarCard(boardName, cardId, data) {
    return fetch(`/api/quadro/${boardName}/card/${cardId}`, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    }).then(r => r.json());
}

function excluirCard(boardName, cardId) {
    return fetch(`/api/quadro/${boardName}/card/${cardId}`, {
        method: 'DELETE',
    }).then(r => r.json());
}

function criarColuna(boardName, titulo) {
    return fetch(`/api/quadro/${boardName}/coluna`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({title: titulo})
    }).then(r => r.json());
}

function excluirColuna(boardName, columnId) {
    return fetch(`/api/quadro/${boardName}/coluna/${columnId}`, {
        method: 'DELETE',
    }).then(r => r.json());
}
