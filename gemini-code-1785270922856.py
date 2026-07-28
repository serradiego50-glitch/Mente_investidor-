import os
import logging
import asyncio
from google import genai
from google.genai import types
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# =========================================================
# 1. CHAVES DE ACESSO (PROTEGIDAS PELA NUVEM)
# =========================================================
TELEGRAM_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SEU_USERNAME_TELEGRAM = "Diegoserrazx"  # Sem o @ (ex: joaotrader)

# =========================================================
# 2. PRODUTOS DA KIWIFY (MENTE INVESTIDOR)
# =========================================================
PRODUTOS = {
    "prod1": {
        "nome": "Planilha de Controle Financeiro 2.0",
        "preco": "R$ 59,90",
        "link": "https://pay.kiwify.com.br/vTO5aL1?afid=XHGX9Thn",
        "descricao": "Organização total de gastos, receitas e metas no celular/PC. Saia das dívidas e faça o dinheiro sobrar."
    },
    "prod2": {
        "nome": "Pack do Investidor",
        "preco": "R$ 77,00",
        "link": "https://pay.kiwify.com.br/6juh7iG?afid=hoHLgPNn",
        "descricao": "Guia prático para sair do zero, montar carteira de Renda Fixa e Ações, com modelos prontos para investir com segurança."
    },
    "prod3": {
        "nome": "Como Comprar sua Primeira Criptomoeda",
        "preco": "R$ 99,97",
        "link": "https://pay.kiwify.com.br/cT8R1jT?afid=R5PeDy7E",
        "descricao": "Passo a passo descomplicado para entrar no mercado cripto sem cometer os erros clássicos de iniciante."
    }
}

# =========================================================
# 3. LOGS DO SISTEMA
# =========================================================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# =========================================================
# 4. CONFIGURAÇÃO DA IA (GEMINI)
# =========================================================
catalogo_texto = "\n".join([
    f"- **{p['nome']}** | Valor: {p['preco']}\n  Benefício: {p['descricao']}"
    for p in PRODUTOS.values()
])

SYSTEM_PROMPT = f"""
Você é o Mente Investidor, uma IA consultora de inteligência financeira e vendas.
Seu perfil é moderno, amigável, direto e focado em alta conversão.

Nosso Catálogo Exclusivo:
{catalogo_texto}

Regras Importantes:
1. Responda em até 2 ou 3 parágrafos curtos, ideais para leitura rápida no celular.
2. Use emojis marcantes (📊, 💰, 🚀, ⚡, 🛡️, ✅) com moderação.
3. Se o cliente falar sobre dívidas/organização de gastos, recomende a 'Planilha de Controle Financeiro 2.0'.
4. Se o cliente quer começar em Renda Fixa/Ações, recomende o 'Pack do Investidor'.
5. Se o cliente busca Criptomoedas, recomende o 'Como Comprar sua Primeira Criptomoeda'.
6. Reforce que os pagamentos são via Pix com aprovação imediata e 7 dias de garantia total pela Kiwify.
7. Encerre sempre convidando o usuário a clicar no botão correspondente abaixo ou a fazer o nosso Quiz Rápido.
"""

client = genai.Client(api_key=GEMINI_API_KEY)
user_chats = {}

def get_or_create_chat(user_id: int):
    if user_id not in user_chats:
        user_chats[user_id] = client.chats.create(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT
            )
        )
    return user_chats[user_id]

# =========================================================
# 5. MENUS DE BOTÕES INTERATIVOS
# =========================================================

def get_catalog_keyboard():
    """Menu principal dinâmico com todas as funcionalidades exclusivas."""
    keyboard = [
        [InlineKeyboardButton("🎯 Quiz: Descobrir o Material Ideal", callback_data="quiz_inicio")],
        [InlineKeyboardButton(f"📊 Planilha Financeira 2.0 • {PRODUTOS['prod1']['preco']}", url=PRODUTOS['prod1']['link'])],
        [InlineKeyboardButton(f"📈 Pack do Investidor • {PRODUTOS['prod2']['preco']}", url=PRODUTOS['prod2']['link'])],
        [InlineKeyboardButton(f"🪙 Guia Cripto Iniciante • {PRODUTOS['prod3']['preco']}", url=PRODUTOS['prod3']['link'])],
        [
            InlineKeyboardButton("⭐ Avaliações", callback_data="info_depoimentos"),
            InlineKeyboardButton("💬 Dúvidas (FAQ)", callback_data="info_faq")
        ],
        [
            InlineKeyboardButton("🎁 Bônus de Hoje", callback_data="info_bonus"),
            InlineKeyboardButton("👤 Atendente Humano", url=f"https://t.me/{SEU_USERNAME_TELEGRAM}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# =========================================================
# 6. COMANDOS E TRATAMENTO DE MENSAGENS
# =========================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mensagem de boas-vindas oficial do bot."""
    user_name = update.effective_user.first_name
    user_id = update.effective_user.id
    
    user_chats[user_id] = client.chats.create(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT
        )
    )
    
    boas_vindas = (
        f"🚀 **Seja muito bem-vindo(a), {user_name}!**\n\n"
        "Você acessou o **Mente Investidor** — seu ecossistema de inteligência e automação financeira.\n\n"
        "💡 **Como posso te ajudar hoje?**\n"
        "• Faça nosso **Quiz Rápido** para descobrir o material ideal para seu momento.\n"
        "• Tire suas dúvidas digitando uma mensagem direta no chat para nossa IA.\n\n"
        "👇 **Escolha uma opção ou selecione um produto abaixo:**"
    )
    
    await update.message.reply_text(
        text=boas_vindas,
        parse_mode="Markdown",
        reply_markup=get_catalog_keyboard()
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Atendimento com IA."""
    user_id = update.effective_user.id
    user_text = update.message.text
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        chat = get_or_create_chat(user_id)
        response = await asyncio.to_thread(chat.send_message, user_text)
        resposta_ia = response.text
        
        await update.message.reply_text(
            text=resposta_ia,
            parse_mode="Markdown",
            reply_markup=get_catalog_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Erro no Gemini: {e}")
        await update.message.reply_text(
            text="Escolha uma das opções abaixo para garantir seu acesso seguro via Pix pela Kiwify:",
            reply_markup=get_catalog_keyboard()
        )

# =========================================================
# 7. TRATAMENTO DOS BOTÕES (QUIZ, FAQ, BÔNUS, DEPOIMENTOS)
# =========================================================

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # --- 1. MINI-QUIZ INTERATIVO ---
    if query.data == "quiz_inicio":
        texto = "🎯 **Diagnóstico Rápido Mente Investidor**\n\nQual é o seu objetivo financeiro principal neste momento?"
        keyboard = [
            [InlineKeyboardButton("1️⃣ Organizar minhas contas e sair do caos", callback_data="quiz_res_1")],
            [InlineKeyboardButton("2️⃣ Começar a investir com segurança", callback_data="quiz_res_2")],
            [InlineKeyboardButton("3️⃣ Multiplicar capital no mercado Cripto", callback_data="quiz_res_3")]
        ]
        await query.message.reply_text(text=texto, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        
    elif query.data == "quiz_res_1":
        texto = (
            "📊 **Recomendação Perfeita para Você:**\n\n"
            "A **Planilha de Controle Financeiro 2.0** é o seu ponto de partida ideal! "
            "Com ela você descobre para onde vai cada centavo e faz o dinheiro sobrar todo mês."
        )
        kb = [[InlineKeyboardButton(f"👉 Adquirir Planilha por {PRODUTOS['prod1']['preco']}", url=PRODUTOS['prod1']['link'])]]
        await query.message.reply_text(text=texto, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

    elif query.data == "quiz_res_2":
        texto = (
            "📈 **Recomendação Perfeita para Você:**\n\n"
            "O **Pack do Investidor** foi feito para você! "
            "Aprenda a montar sua carteira do zero em Renda Fixa e Ações sem complicação."
        )
        kb = [[InlineKeyboardButton(f"👉 Adquirir Pack por {PRODUTOS['prod2']['preco']}", url=PRODUTOS['prod2']['link'])]]
        await query.message.reply_text(text=texto, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

    elif query.data == "quiz_res_3":
        texto = (
            "🪙 **Recomendação Perfeita para Você:**\n\n"
            "O guia **Como Comprar sua Primeira Criptomoeda** é o ideal! "
            "Entre no mercado cripto com o passo a passo seguro sem correr riscos de iniciante."
        )
        kb = [[InlineKeyboardButton(f"👉 Adquirir Guia Cripto por {PRODUTOS['prod3']['preco']}", url=PRODUTOS['prod3']['link'])]]
        await query.message.reply_text(text=texto, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

    # --- 2. FAQ (PERGUNTAS FREQUENTES) ---
    elif query.data == "info_faq":
        texto = (
            "💬 **DÚVIDAS FREQUENTES (FAQ)**\n\n"
            "📱 **Preciso de computador?**\n"
            "Não! Todos os materiais e planilhas funcionam perfeitamente no celular ou PC.\n\n"
            "⚡ **Como recebo o acesso?**\n"
            "O envio é automático e imediato no seu e-mail assim que o Pix/Cartão for aprovado.\n\n"
            "🔰 **Sou iniciante, vou conseguir aprender?**\n"
            "Com certeza! O conteúdo foi desenvolvido com linguagem simples e prática, sem termos difíceis.\n\n"
            "🛡️ **Possui garantia?**\n"
            "Sim, garantia total de 7 dias protegida pela Kiwify."
        )
        await query.message.reply_text(text=texto, parse_mode="Markdown", reply_markup=get_catalog_keyboard())

    # --- 3. CUPOM DE ESCASSEZ / BÔNUS ---
    elif query.data == "info_bonus":
        texto = (
            "🎁 **OFERTA ESPECIAL COM BÔNUS EXCLUSIVO**\n\n"
            "Garanta qualquer um dos materiais nas próximas **2 horas** e receba:\n"
            "✅ Atualizações gratuitas por 1 ano.\n"
            "✅ Suporte priorizado no checkout.\n"
            "✅ Garantia incondicional de 7 dias com risco zero.\n\n"
            "⏳ *Aproveite antes que o lote promocional encerre!*"
        )
        await query.message.reply_text(text=texto, parse_mode="Markdown", reply_markup=get_catalog_keyboard())

    # --- 4. PROVA SOCIAL / DEPOIMENTOS ---
    elif query.data == "info_depoimentos":
        texto = (
            "⭐ **O QUE DIZEM NOSSOS ALUNOS & CLIENTES:**\n\n"
            "💬 *'A planilha abriu meus olhos. Em menos de 2 semanas já identifiquei R$ 400 em gastos desnecessários.'* — **Lucas M.**\n\n"
            "💬 *'Comprei o Pack do Investidor e montei minha primeira carteira em 10 minutos.'* — **Fernanda S.**\n\n"
            "💬 *'Estava com medo de cripto, mas o guia me mostrou o passo a passo certinho na corretora.'* — **Thiago R.**"
        )
        await query.message.reply_text(text=texto, parse_mode="Markdown", reply_markup=get_catalog_keyboard())

# =========================================================
# 8. INICIALIZAÇÃO
# =========================================================
def main():
    print("🚀 Ligando o Mente Investidor com Quiz, FAQ e Prova Social...")
    
    if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
        print("\n❌ Erro: As variáveis de ambiente BOT_TOKEN ou GEMINI_API_KEY não foram encontradas!")
        return

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))

    print("✅ Bot Mente Investidor 100% online com novos recursos!")
    app.run_polling()

if __name__ == "__main__":
    main()