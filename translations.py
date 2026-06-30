"""
Módulo de tradução multilíngue do Kanban App.
Suporta: pt-BR, en, fr, it, zh (Mandarim Simplificado)
"""

from typing import Dict, Optional
import re

# ─── Todos os idiomas suportados ────────────────────────────────────
LANGUAGES = {
    'pt-BR': 'Português (BR)',
    'en': 'English',
    'fr': 'Français',
    'it': 'Italiano',
    'zh': '中文',
}

LANGUAGE_NAMES = {
    'pt-BR': 'Português',
    'en': 'English',
    'fr': 'Français',
    'it': 'Italiano',
    'zh': '普通话',
}

# Mapa de locale do browser -> codigo do sistema
BROWSER_LOCALE_MAP = {
    'pt': 'pt-BR', 'pt-br': 'pt-BR', 'pt-pt': 'pt-BR',
    'en': 'en', 'en-us': 'en', 'en-gb': 'en',
    'fr': 'fr', 'fr-fr': 'fr', 'fr-ca': 'fr',
    'it': 'it', 'it-it': 'it',
    'zh': 'zh', 'zh-cn': 'zh', 'zh-tw': 'zh', 'zh-hans': 'zh',
}

# ─── Dicionario de traducoes ────────────────────────────────────────
T = {}

def add(key, pt_br='', en='', fr='', it='', zh=''):
    """Adiciona uma traducao."""
    T[key] = {'pt-BR': pt_br, 'en': en, 'fr': fr, 'it': it, 'zh': zh}

# ═════════════════════════════════════════════════════════════════════
#  GERAL / NAVEGACAO
# ═════════════════════════════════════════════════════════════════════

add('app_name', pt_br='Kanban', en='Kanban', fr='Kanban', it='Kanban', zh='看板')
add('kanban_app', pt_br='Kanban App', en='Kanban App', fr='Kanban App', it='Kanban App', zh='看板应用')
add('nav_admin_global', pt_br='Admin Global', en='Global Admin', fr='Admin Global', it='Admin Globale', zh='全局管理')
add('nav_corporativo', pt_br='Corporativo', en='Corporate', fr='Corporate', it='Aziendale', zh='企业')
add('nav_meus_quadros', pt_br='Meus Quadros', en='My Boards', fr='Mes Tableaux', it='Le Mie Lavagne', zh='我的看板')
add('nav_quadros', pt_br='Quadros', en='Boards', fr='Tableaux', it='Lavagne', zh='看板')
add('nav_conta', pt_br='Minha Conta', en='My Account', fr='Mon Compte', it='Il Mio Account', zh='我的账户')
add('nav_planos', pt_br='Planos', en='Plans', fr='Forfaits', it='Piani', zh='套餐')
add('nav_sair', pt_br='Sair', en='Logout', fr='Déconnexion', it='Esci', zh='退出')
add('nav_toggle_theme', pt_br='Alternar tema', en='Toggle theme', fr='Changer le theme', it='Cambia tema', zh='切换主题')
add('nav_idioma', pt_br='Idioma', en='Language', fr='Langue', it='Lingua', zh='语言')
add('footer_text', pt_br='Kanban App - Persistência em arquivos OKF - Python + Flask',
    en='Kanban App - OKF file persistence - Python + Flask',
    fr='Kanban App - Persistance en fichiers OKF - Python + Flask',
    it='Kanban App - Persistenza su file OKF - Python + Flask',
    zh='看板应用 - OKF 文件持久化 - Python + Flask')

# ═════════════════════════════════════════════════════════════════════
#  LOGIN
# ═════════════════════════════════════════════════════════════════════

add('login_title', pt_br='Entrar', en='Login', fr='Connexion', it='Accedi', zh='登录')
add('login_email', pt_br='Email', en='Email', fr='Email', it='Email', zh='邮箱')
add('login_senha', pt_br='Senha', en='Password', fr='Mot de passe', it='Password', zh='密码')
add('login_entrar', pt_br='Entrar', en='Sign In', fr='Se connecter', it='Accedi', zh='登录')
add('login_placeholder_email', pt_br='seu@email.com', en='your@email.com', fr='votre@email.com', it='tua@email.com', zh='your@email.com')
add('login_placeholder_senha', pt_br='Sua senha', en='Your password', fr='Votre mot de passe', it='La tua password', zh='您的密码')
add('login_required', pt_br='Preencha email e senha.', en='Please fill email and password.', fr='Remplissez email et mot de passe.', it='Inserisci email e password.', zh='请填写邮箱和密码。')
add('login_user_not_found', pt_br='Usuário não encontrado.', en='User not found.', fr='Utilisateur non trouve.', it='Utente non trovato.', zh='找不到用户。')
add('login_user_suspended', pt_br='Usuário suspenso. Contate o administrador.', en='User suspended. Contact the administrator.', fr='Utilisateur suspendu. Contactez l\'administrateur.', it='Utente sospeso. Contatta l\'amministratore.', zh='用户已被暂停。请联系管理员。')
add('login_wrong_password', pt_br='Senha incorreta.', en='Wrong password.', fr='Mot de passe incorrect.', it='Password errata.', zh='密码错误。')
add('login_welcome', pt_br='Bem-vindo(a)', en='Welcome', fr='Bienvenue', it='Benvenuto', zh='欢迎')
add('login_session_expired', pt_br='Sessão expirada. Faça login novamente.', en='Session expired. Please login again.', fr='Session expiree. Veuillez vous reconnecter.', it='Sessione scaduta. Accedi di nuovo.', zh='会话已过期。请重新登录。')
add('login_senha_curta', pt_br='Senha muito curta.', en='Password too short.', fr='Mot de passe trop court.', it='Password troppo corta.', zh='密码太短。')
add('login_email_invalido', pt_br='Email inválido.', en='Invalid email.', fr='Email invalide.', it='Email non valida.', zh='邮箱无效。')

# ═════════════════════════════════════════════════════════════════════
#  DASHBOARD
# ═════════════════════════════════════════════════════════════════════

add('dashboard_title', pt_br='Meus Quadros', en='My Boards', fr='Mes Tableaux', it='Le Mie Lavagne', zh='我的看板')
add('dashboard_quadro_count', pt_br='quadro(s)', en='board(s)', fr='tableau(x)', it='lavagna(e)', zh='个看板')
add('dashboard_novo_quadro', pt_br='Novo Quadro', en='New Board', fr='Nouveau Tableau', it='Nuova Lavagna', zh='新建看板')
add('dashboard_nenhum_quadro', pt_br='Nenhum quadro ainda', en='No boards yet', fr='Aucun tableau', it='Nessuna lavagna ancora', zh='暂无看板')
add('dashboard_crie_primeiro', pt_br='Crie seu primeiro quadro Kanban para começar', en='Create your first Kanban board to get started', fr='Creez votre premier tableau Kanban pour commencer', it='Crea la tua prima lavagna Kanban per iniziare', zh='创建您的第一个看板以开始使用')
add('dashboard_criar_quadro', pt_br='Criar Quadro', en='Create Board', fr='Creer un Tableau', it='Crea Lavagna', zh='创建看板')
add('dashboard_espaco_disco', pt_br='Espaço em disco utilizado', en='Disk space used', fr='Espace disque utilise', it='Spazio disco utilizzato', zh='已用磁盘空间')
add('dashboard_arquivos', pt_br='Arquivos', en='Files', fr='Fichiers', it='File', zh='文件')
add('dashboard_abrir', pt_br='Abrir', en='Open', fr='Ouvrir', it='Apri', zh='打开')
add('dashboard_excluir', pt_br='Excluir', en='Delete', fr='Supprimer', it='Elimina', zh='删除')

# Upgrade banner
add('upgrade_banner_uso', pt_br='Você está usando', en='You are using', fr='Vous utilisez', it='Stai usando', zh='您正在使用')
add('upgrade_banner_de', pt_br='de', en='of', fr='de', it='di', zh='共')
add('upgrade_banner_gratuito', pt_br='quadros do plano Gratuito', en='boards of the Free plan', fr='tableaux du plan Gratuit', it='lavagne del piano Gratuito', zh='免费套餐的看板')
add('upgrade_banner_texto', pt_br='Faça upgrade para o Plano Comum (R$ 6,99/mês) e tenha até 20 quadros!',
    en='Upgrade to the Common Plan ($ 6.99/month) and get up to 20 boards!',
    fr='Passez au Plan Commun (6.99 EUR/mois) et obtenez jusqu\'a 20 tableaux !',
    it='Passa al Piano Comune (EUR 6,99/mese) e ottieni fino a 20 lavagne!',
    zh='升级到普通套餐，获得最多 20 个看板！')
add('upgrade_banner_ver', pt_br='Ver Planos', en='View Plans', fr='Voir les Forfaits', it='Vedi Piani', zh='查看套餐')

# ═════════════════════════════════════════════════════════════════════
#  BOARD (KANBAN)
# ═════════════════════════════════════════════════════════════════════

add('board_voltar', pt_br='Voltar', en='Back', fr='Retour', it='Indietro', zh='返回')
add('board_card_btn', pt_br='Card', en='Card', fr='Carte', it='Carta', zh='卡片')
add('board_coluna_btn', pt_br='Coluna', en='Column', fr='Colonne', it='Colonna', zh='列')
add('board_adicionar_card', pt_br='Adicionar cartão', en='Add card', fr='Ajouter une carte', it='Aggiungi carta', zh='添加卡片')
add('board_novo_card', pt_br='Novo Cartão', en='New Card', fr='Nouvelle Carte', it='Nuova Carta', zh='新卡片')
add('board_nova_coluna', pt_br='Nova Coluna', en='New Column', fr='Nouvelle Colonne', it='Nuova Colonna', zh='新列')
add('board_editar_card', pt_br='Editar Cartão', en='Edit Card', fr='Modifier la Carte', it='Modifica Carta', zh='编辑卡片')
add('board_titulo_card', pt_br='Título *', en='Title *', fr='Titre *', it='Titolo *', zh='标题 *')
add('board_descricao', pt_br='Descricao', en='Description', fr='Description', it='Descrizione', zh='描述')
add('board_prioridade', pt_br='Prioridade', en='Priority', fr='Priorite', it='Priorita', zh='优先级')
add('board_prioridade_baixa', pt_br='Baixa', en='Low', fr='Basse', it='Bassa', zh='低')
add('board_prioridade_media', pt_br='Média', en='Medium', fr='Moyenne', it='Media', zh='中')
add('board_prioridade_alta', pt_br='Alta', en='High', fr='Haute', it='Alta', zh='高')
add('board_data_entrega', pt_br='Data de Entrega', en='Due Date', fr='Date d\'echeance', it='Data Scadenza', zh='截止日期')
add('board_coluna_a_fazer', pt_br='A Fazer', en='To Do', fr='A Faire', it='Da Fare', zh='待办')
add('board_coluna_em_progresso', pt_br='Em Progresso', en='In Progress', fr='En Cours', it='In Corso', zh='进行中')
add('board_coluna_concluido', pt_br='Concluído', en='Done', fr='Termine', it='Completato', zh='已完成')
add('board_criar', pt_br='Criar', en='Create', fr='Creer', it='Crea', zh='创建')
add('board_salvar', pt_br='Salvar', en='Save', fr='Sauvegarder', it='Salva', zh='保存')
add('board_excluir', pt_br='Excluir', en='Delete', fr='Supprimer', it='Elimina', zh='删除')
add('board_titulo_coluna', pt_br='Título da Coluna *', en='Column Title *', fr='Titre de la Colonne *', it='Titolo Colonna *', zh='列标题 *')
add('board_placeholder_coluna', pt_br='ex: Revisão, Aguardando', en='e.g.: Review, Waiting', fr='ex: Revision, En attente', it='es: Revisione, In attesa', zh='例如：审核、待处理')
add('board_adicionar', pt_br='Adicionar', en='Add', fr='Ajouter', it='Aggiungi', zh='添加')

# ═════════════════════════════════════════════════════════════════════
#  ADMIN GLOBAL
# ═════════════════════════════════════════════════════════════════════

add('admin_global_titulo', pt_br='Painel do Administrador Global', en='Global Administrator Panel', fr='Panneau d\'Administration Global', it='Pannello Amministratore Globale', zh='全局管理员面板')
add('admin_global_total_usuarios', pt_br='Total de Usuários', en='Total Users', fr='Total Utilisateurs', it='Totale Utenti', zh='用户总数')
add('admin_global_quadros_okf', pt_br='Quadros OKF', en='OKF Boards', fr='Tableaux OKF', it='Lavagne OKF', zh='OKF 看板')
add('admin_global_arquivos_okf', pt_br='Arquivos OKF', en='OKF Files', fr='Fichiers OKF', it='File OKF', zh='OKF 文件')
add('admin_global_perfis', pt_br='Perfis', en='Profiles', fr='Profils', it='Profili', zh='角色')
add('admin_global_distribuicao', pt_br='Distribuição por Perfil', en='Profile Distribution', fr='Repartition par Profil', it='Distribuzione per Profilo', zh='角色分布')
add('admin_global_acoes_rapidas', pt_br='Ações Rápidas', en='Quick Actions', fr='Actions Rapides', it='Azioni Rapide', zh='快捷操作')
add('admin_global_criar_usuario', pt_br='Criar novo usuário', en='Create new user', fr='Creer un nouvel utilisateur', it='Crea nuovo utente', zh='创建新用户')
add('admin_global_ver_logs', pt_br='Ver logs de armazenamento', en='View storage logs', fr='Voir les logs de stockage', it='Vedi log di archiviazione', zh='查看存储日志')
add('admin_global_meus_quadros', pt_br='Meus quadros', en='My boards', fr='Mes tableaux', it='Le mie lavagne', zh='我的看板')
add('admin_global_novo_usuario_btn', pt_br='Novo Usuário', en='New User', fr='Nouvel Utilisateur', it='Nuovo Utente', zh='新用户')
add('admin_global_tabela', pt_br='Usuários do Sistema', en='System Users', fr='Utilisateurs du Systeme', it='Utenti del Sistema', zh='系统用户')
add('admin_global_novo', pt_br='Novo', en='New', fr='Nouveau', it='Nuovo', zh='新建')

# Table headers
add('th_id', pt_br='ID', en='ID', fr='ID', it='ID', zh='ID')
add('th_nome', pt_br='Nome', en='Name', fr='Nom', it='Nome', zh='名称')
add('th_email', pt_br='Email', en='Email', fr='Email', it='Email', zh='邮箱')
add('th_perfil', pt_br='Perfil', en='Profile', fr='Profil', it='Profilo', zh='角色')
add('th_plano', pt_br='Plano', en='Plan', fr='Forfait', it='Piano', zh='套餐')
add('th_corp', pt_br='Corp', en='Corp', fr='Societe', it='Azienda', zh='企业')
add('th_status', pt_br='Status', en='Status', fr='Statut', it='Stato', zh='状态')
add('th_acoes', pt_br='Ações', en='Actions', fr='Actions', it='Azioni', zh='操作')
add('th_arquivo', pt_br='Arquivo', en='File', fr='Fichier', it='File', zh='文件')
add('th_usuario', pt_br='Usuário', en='User', fr='Utilisateur', it='Utente', zh='用户')
add('th_tamanho', pt_br='Tamanho', en='Size', fr='Taille', it='Dimensione', zh='大小')
add('th_modificado', pt_br='Modificado', en='Modified', fr='Modifie', it='Modificato', zh='修改时间')

# Status
add('status_ativo', pt_br='Ativo', en='Active', fr='Actif', it='Attivo', zh='活跃')
add('status_suspenso', pt_br='Suspenso', en='Suspended', fr='Suspendu', it='Sospeso', zh='已暂停')
add('perfil_label_admin', pt_br='Admin', en='Admin', fr='Admin', it='Admin', zh='管理员')
add('perfil_label_corp', pt_br='Corp', en='Corp', fr='Societe', it='Azienda', zh='企业')
add('perfil_label_comum', pt_br='Comum', en='Common', fr='Commun', it='Comune', zh='普通')
add('perfil_admin_global', pt_br='Administrador Global', en='Global Administrator', fr='Administrateur Global', it='Amministratore Globale', zh='全局管理员')
add('perfil_admin_corp', pt_br='Administrador Corporativo', en='Corporate Administrator', fr='Administrateur Corporate', it='Amministratore Aziendale', zh='企业管理员')
add('perfil_usuario_comum', pt_br='Usuário Comum', en='Common User', fr='Utilisateur Commun', it='Utente Comune', zh='普通用户')

# Modals
add('modal_criar_usuario', pt_br='Criar Usuário', en='Create User', fr='Creer l\'Utilisateur', it='Crea Utente', zh='创建用户')
add('modal_editar_usuario', pt_br='Editar Usuário', en='Edit User', fr='Modifier l\'Utilisateur', it='Modifica Utente', zh='编辑用户')
add('modal_senha', pt_br='Senha *', en='Password *', fr='Mot de passe *', it='Password *', zh='密码 *')
add('modal_nova_senha', pt_br='Nova Senha', en='New Password', fr='Nouveau Mot de Passe', it='Nuova Password', zh='新密码')
add('modal_deixar_vazio', pt_br='Deixar vazio = manter', en='Leave blank = keep', fr='Laisser vide = conserver', it='Lasciare vuoto = mantenere', zh='留空则不更改')
add('modal_id_corp', pt_br='ID Corporação', en='Corporation ID', fr='ID Societe', it='ID Azienda', zh='企业 ID')
add('modal_placeholder_corp', pt_br='Deixe em branco para nenhuma', en='Leave blank for none', fr='Laisser vide si aucun', it='Lasciare vuoto se nessuno', zh='无则留空')
add('modal_cancelar', pt_br='Cancelar', en='Cancel', fr='Annuler', it='Annulla', zh='取消')
add('modal_criar', pt_br='Criar', en='Create', fr='Creer', it='Crea', zh='创建')
add('modal_salvar', pt_br='Salvar', en='Save', fr='Sauvegarder', it='Salva', zh='保存')
add('modal_nome', pt_br='Nome *', en='Name *', fr='Nom *', it='Nome *', zh='名称 *')
add('modal_titulo', pt_br='Título', en='Title', fr='Titre', it='Titolo', zh='标题')
add('modal_descricao', pt_br='Descricao', en='Description', fr='Description', it='Descrizione', zh='描述')

# Logs
add('admin_logs_titulo', pt_br='Logs de Armazenamento (Arquivos OKF)', en='Storage Logs (OKF Files)', fr='Logs de Stockage (Fichiers OKF)', it='Log di Archiviazione (File OKF)', zh='存储日志（OKF 文件）')

# Flash messages
add('flash_criado', pt_br='criado com sucesso!', en='created successfully!', fr='cree avec succes !', it='creato con successo!', zh='创建成功！')
add('flash_atualizado', pt_br='atualizado com sucesso!', en='updated successfully!', fr='mis a jour avec succes !', it='aggiornato con successo!', zh='更新成功！')
add('flash_nao_encontrado', pt_br='não encontrado.', en='not found.', fr='non trouve.', it='non trovato.', zh='未找到。')
add('flash_reativado', pt_br='reativado.', en='reactivated.', fr='reactive.', it='riattivato.', zh='已重新激活。')
add('flash_suspenso', pt_br='suspenso.', en='suspended.', fr='suspendu.', it='sospeso.', zh='已暂停。')
add('flash_nao_excluir_admin', pt_br='Não é possível excluir o Administrador Geral.', en='Cannot delete the General Administrator.', fr='Impossible de supprimer l\'Administrateur General.', it='Impossibile eliminare l\'Amministratore Generale.', zh='无法删除全局管理员。')
add('flash_excluido', pt_br='e seus dados excluídos.', en='and their data deleted.', fr='et ses donnees supprimees.', it='e i suoi dati eliminati.', zh='及其数据已删除。')
add('flash_plano_ativado', pt_br='ativado com sucesso!', en='activated successfully!', fr='active avec succes !', it='attivato con successo!', zh='已成功激活！')
add('flash_plano_cancelado', pt_br='Assinatura cancelada. Você está no plano Gratuito.', en='Subscription cancelled. You are on the Free plan.', fr='Abonnement annule. Vous etes sur le plan Gratuit.', it='Abbonamento annullato. Sei sul piano Gratuito.', zh='订阅已取消。您在使用免费套餐。')
add('flash_plano_invalido', pt_br='Plano inválido.', en='Invalid plan.', fr='Forfait invalide.', it='Piano non valido.', zh='无效套餐。')
add('flash_pagamento_invalido', pt_br='Tipo de pagamento inválido.', en='Invalid payment type.', fr='Type de paiement invalide.', it='Tipo di pagamento non valido.', zh='无效支付类型。')
add('flash_plano_corp_restrito', pt_br='Plano corporativo disponível apenas para administradores corporativos.',
    en='Corporate plan only available for corporate administrators.',
    fr='Plan corporate disponible uniquement pour les administrateurs corporate.',
    it='Piano aziendale disponibile solo per amministratori aziendali.',
    zh='企业套餐仅适用于企业管理员。')

# ═════════════════════════════════════════════════════════════════════
#  ADMIN USER (Minha Conta)
# ═════════════════════════════════════════════════════════════════════

add('account_titulo', pt_br='Minha Conta', en='My Account', fr='Mon Compte', it='Il Mio Account', zh='我的账户')
add('account_dados_pessoais', pt_br='Dados Pessoais', en='Personal Data', fr='Donnees Personnelles', it='Dati Personali', zh='个人资料')
add('account_alterar_senha', pt_br='Alterar Senha', en='Change Password', fr='Changer le Mot de Passe', it='Cambia Password', zh='更改密码')
add('account_senha_atual', pt_br='Senha Atual', en='Current Password', fr='Mot de Passe Actuel', it='Password Attuale', zh='当前密码')
add('account_nova_senha', pt_br='Nova Senha', en='New Password', fr='Nouveau Mot de Passe', it='Nuova Password', zh='新密码')
add('account_confirmar_senha', pt_br='Confirmar', en='Confirm', fr='Confirmer', it='Conferma', zh='确认')
add('account_salvar', pt_br='Salvar Alterações', en='Save Changes', fr='Enregistrer les Modifications', it='Salva Modifiche', zh='保存更改')
add('account_info_perfil', pt_br='Informações do Perfil', en='Profile Information', fr='Informations du Profil', it='Informazioni Profilo', zh='角色信息')
add('account_plano', pt_br='Plano', en='Plan', fr='Forfait', it='Piano', zh='套餐')
add('account_gerenciar', pt_br='Gerenciar', en='Manage', fr='Gerer', it='Gestisci', zh='管理')
add('account_criado_em', pt_br='Criado em', en='Created at', fr='Cree le', it='Creato il', zh='创建于')
add('account_atualizado_em', pt_br='Atualizado em', en='Updated at', fr='Mis a jour le', it='Aggiornato il', zh='更新于')
add('account_armazenamento', pt_br='Armazenamento em Disco', en='Disk Storage', fr='Stockage sur Disque', it='Archiviazione su Disco', zh='磁盘存储')

# ═════════════════════════════════════════════════════════════════════
#  PLANOS
# ═════════════════════════════════════════════════════════════════════

add('planos_titulo', pt_br='Planos Kanban', en='Kanban Plans', fr='Forfaits Kanban', it='Piani Kanban', zh='看板套餐')
add('planos_seu_plano', pt_br='Seu plano atual:', en='Your current plan:', fr='Votre forfait actuel :', it='Il tuo piano attuale:', zh='您当前的套餐：')
add('planos_plano_atual', pt_br='Plano Atual', en='Current Plan', fr='Forfait Actuel', it='Piano Attuale', zh='当前套餐')
add('planos_cancelar_assinatura', pt_br='Cancelar Assinatura', en='Cancel Subscription', fr='Annuler l\'Abonnement', it='Annulla Abbonamento', zh='取消订阅')
add('planos_mais_popular', pt_br='MAIS POPULAR', en='MOST POPULAR', fr='LE PLUS POPULAIRE', it='PIU POPOLARE', zh='最受欢迎')
add('planos_gratuito', pt_br='Gratuito', en='Free', fr='Gratuit', it='Gratuito', zh='免费')
add('planos_comum', pt_br='Comum', en='Common', fr='Commun', it='Comune', zh='普通')
add('planos_corporativo', pt_br='Corporativo', en='Corporate', fr='Corporate', it='Aziendale', zh='企业')
add('planos_por_mes', pt_br='/mês', en='/month', fr='/mois', it='/mese', zh='/月')
add('planos_gratis_propaganda', pt_br='Grátis com Propaganda', en='Free with Ads', fr='Gratuit avec Pub', it='Gratuito con Pubblicita', zh='带广告免费')
add('planos_assinar', pt_br='Assinar', en='Subscribe', fr='S\'abonner', it='Abbonati', zh='订阅')
add('planos_cancelar', pt_br='Cancelar', en='Cancel', fr='Annuler', it='Annulla', zh='取消')
add('planos_comparativo', pt_br='Comparativo Completo', en='Full Comparison', fr='Comparaison Complete', it='Confronto Completo', zh='完整对比')
add('planos_recurso', pt_br='Recurso', en='Feature', fr='Fonctionnalite', it='Funzionalita', zh='功能')

add('planos_preco_gratuito', pt_br='R$ 0', en='$ 0', fr='0 EUR', it='EUR 0', zh='¥ 0')
add('planos_preco_comum', pt_br='R$ 6,99', en='$ 6.99', fr='6,99 EUR', it='EUR 6,99', zh='¥ 6.99')
add('planos_preco_corp', pt_br='R$ 3,99', en='$ 3.99', fr='3,99 EUR', it='EUR 3,99', zh='¥ 3.99')
add('planos_preco_cnpj', pt_br='+ R$ 20 CNPJ', en='+ $ 20', fr='+ 20 EUR', it='+ EUR 20', zh='+ ¥ 20')

add('planos_feat_quadros', pt_br='Quadros', en='Boards', fr='Tableaux', it='Lavagne', zh='看板')
add('planos_feat_cartoes', pt_br='Cartões por quadro', en='Cards per board', fr='Cartes par tableau', it='Carte per lavagna', zh='每看板卡片数')
add('planos_feat_drag', pt_br='Drag & Drop nativo', en='Native Drag & Drop', fr='Drag & Drop natif', it='Drag & Drop nativo', zh='原生拖放')
add('planos_feat_tema', pt_br='Tema escuro', en='Dark theme', fr='Theme sombre', it='Tema scuro', zh='深色主题')
add('planos_feat_gestao_corp', pt_br='Gestão corporativa', en='Corporate management', fr='Gestion corporate', it='Gestione aziendale', zh='企业管理')
add('planos_feat_suporte', pt_br='Suporte', en='Support', fr='Support', it='Supporto', zh='支持')
add('planos_feat_comunidade', pt_br='Comunitário', en='Community', fr='Communautaire', it='Community', zh='社区')
add('planos_feat_prioritario', pt_br='Prioritario', en='Priority', fr='Prioritaire', it='Prioritario', zh='优先')
add('planos_feat_multi_usuarios', pt_br='Múltiplos usuários', en='Multiple users', fr='Utilisateurs multiples', it='Utenti multipli', zh='多用户')
add('planos_feat_ver_equipe', pt_br='Visualizar quadros da equipe', en='View team boards', fr='Voir les tableaux de l\'equipe', it='Visualizza lavagne del team', zh='查看团队看板')
add('planos_feat_criar_usuarios', pt_br='Criar usuários sob sua corporação', en='Create users under your corporation', fr='Creer des utilisateurs sous votre societe', it='Crea utenti nella tua azienda', zh='创建企业下的用户')
add('planos_feat_limites', pt_br='Limites de quadros por usuario', en='Board limits per user', fr='Limites de tableaux par utilisateur', it='Limiti lavagne per utente', zh='每用户看板限制')
add('planos_feat_reordenacao', pt_br='Drag & Drop + reordenacao', en='Drag & Drop + reordering', fr='Drag & Drop + reorganisation', it='Drag & Drop + riordino', zh='拖放 + 重新排序')
add('planos_feat_todos_gratuito', pt_br='Todos os recursos do Gratuito', en='All Free features', fr='Toutes les fonctionnalites Gratuites', it='Tutte le funzionalita Gratuite', zh='所有免费功能')
add('planos_feat_suporte_prioritario', pt_br='Suporte prioritario', en='Priority support', fr='Support prioritaire', it='Supporto prioritario', zh='优先支持')

add('planos_feat_3quadros', pt_br='Ate 3 quadros Kanban', en='Up to 3 Kanban boards', fr="Jusqu'a 3 tableaux Kanban", it='Fino a 3 lavagne Kanban', zh='最多 3 个看板')
add('planos_feat_20cartoes', pt_br='Ate 20 cartoes por quadro', en='Up to 20 cards per board', fr="Jusqu'a 20 cartes par tableau", it='Fino a 20 carte per lavagna', zh='每看板最多 20 个卡片')
add('planos_feat_20quadros', pt_br='Ate 20 quadros Kanban', en='Up to 20 Kanban boards', fr="Jusqu'a 20 tableaux Kanban", it='Fino a 20 lavagne Kanban', zh='最多 20 个看板')
add('planos_feat_200cartoes', pt_br='Ate 200 cartoes por quadro', en='Up to 200 cards per board', fr="Jusqu'a 200 cartes par tableau", it='Fino a 200 carte per lavagna', zh='每看板最多 200 个卡片')
add('planos_feat_50quadros', pt_br='Ate 50 quadros Kanban', en='Up to 50 Kanban boards', fr="Jusqu'a 50 tableaux Kanban", it='Fino a 50 lavagne Kanban', zh='最多 50 个看板')

add('planos_desc_gratuito', pt_br='3 quadros, 20 cartoes', en='3 boards, 20 cards', fr='3 tableaux, 20 cartes', it='3 lavagne, 20 carte', zh='3 个看板，20 个卡片')
add('planos_desc_comum', pt_br='20 quadros, 200 cartoes', en='20 boards, 200 cards', fr='20 tableaux, 200 cartes', it='20 lavagne, 200 carte', zh='20 个看板，200 个卡片')
add('planos_desc_corporativo', pt_br='50 quadros, gestao corporativa', en='50 boards, corporate management', fr='50 tableaux, gestion corporate', it='50 lavagne, gestione aziendale', zh='50 个看板，企业管理')

add('planos_disponivel_corp', pt_br='Disponivel para Adm. Corporativo', en='Available for Corp. Admin', fr='Disponible pour Adm. Corporate', it='Disponibile per Admin Aziendale', zh='企业管理员可用')

# ═════════════════════════════════════════════════════════════════════
#  SISTEMA / ERROR
# ═════════════════════════════════════════════════════════════════════

add('error_403', pt_br='Acesso negado.', en='Access denied.', fr='Acces refuse.', it='Accesso negato.', zh='访问被拒绝。')
add('error_404', pt_br='Página não encontrada.', en='Page not found.', fr='Page non trouvee.', it='Pagina non trovata.', zh='页面未找到。')
add('error_429', pt_br='Muitas requisições. Aguarde e tente novamente.', en='Too many requests. Please wait and try again.', fr='Trop de requetes. Veuillez attendre et reessayer.', it='Troppe richieste. Attendere e riprovare.', zh='请求过多。请稍后再试。')
add('error_quadro_nao_encontrado', pt_br='Quadro nao encontrado.', en='Board not found.', fr='Tableau non trouve.', it='Lavagna non trovata.', zh='看板未找到。')
add('error_nome_invalido', pt_br='Nome do quadro invalido.', en='Invalid board name.', fr='Nom de tableau invalide.', it='Nome lavagna non valido.', zh='看板名称无效。')


# ═════════════════════════════════════════════════════════════════════
#  FUNCAO DE TRADUCAO
# ═════════════════════════════════════════════════════════════════════

_CACHE = {}

def get_text(key: str, lang: str = 'pt-BR') -> str:
    """Retorna o texto traduzido para a chave e idioma."""
    if not _CACHE:
        for lang_code in LANGUAGES:
            _CACHE[lang_code] = {}
        for k, translations in T.items():
            for lang_code, text in translations.items():
                if lang_code in _CACHE:
                    _CACHE[lang_code][k] = text

    if lang not in _CACHE:
        lang = 'pt-BR'
    return _CACHE.get(lang, {}).get(key, key)


def _(text: str, lang: str = 'pt-BR', **kwargs) -> str:
    """Funcao de traducao para templates: {{ _('key') }} ou {{ _('key', lang=...) }} """
    return get_text(text, lang)


def detect_language(accept_languages: str) -> str:
    """
    Detecta o melhor idioma baseado no header Accept-Language do browser.
    Exemplo: 'pt-BR,pt;q=0.9,en;q=0.8' -> 'pt-BR'
    """
    if not accept_languages:
        return 'pt-BR'

    locales = []
    for part in accept_languages.split(','):
        part = part.strip()
        if ';' in part:
            locale, q = part.split(';', 1)
            q = float(q.split('=')[1]) if 'q=' in q else 1.0
        else:
            locale = part
            q = 1.0
        locales.append((locale.strip(), q))

    locales.sort(key=lambda x: -x[1])

    for locale, _ in locales:
        lang_code = locale.split('-')[0].lower()
        if lang_code in BROWSER_LOCALE_MAP:
            return BROWSER_LOCALE_MAP[lang_code]

    return 'pt-BR'
