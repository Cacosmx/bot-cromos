import discord
from discord.ext import commands
import random
import sqlite3
from datetime import datetime, timedelta
import os
from flask import Flask
from threading import Thread

# Configuración de Intents de Discord
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- BASE DE DATOS LOCAL ---
conn = sqlite3.connect("cromos_bot.db")
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS inventario (
    user_id INTEGER,
    cromo_id INTEGER,
    PRIMARY KEY (user_id, cromo_id)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS cooldowns (
    user_id INTEGER,
    deporte TEXT,
    ultimo_sobre TIMESTAMP,
    PRIMARY KEY (user_id, deporte)
)
''')
conn.commit()

# --- BASE DE DATOS DETALLADA ESTILO CROMO FÍSICO (ADRENALYN / TOPPS) ---
CROMOS_DATABASE = [
    # --- ⚽ FÚTBOL ---
    {
        "id": 1, "nombre": "Pedri", "equipo": "FC Barcelona", "nacionalidad": "🇪🇸 España",
        "categoria": "futbol", "genero": "Masculino", "edicion": "Balón de Oro 🥇", "rareza": "Leyenda 3D",
        "stats": "⚔️ ATA: 98 | 🛡️ DEF: 92 | ⚡ CTR: 100", "foto": "https://images.unsplash.com/photo-1508098682722-e99c43a406b2?w=500"
    },
    {
        "id": 2, "nombre": "Aitana Bonmatí", "equipo": "FC Barcelona", "nacionalidad": "🇪🇸 España",
        "categoria": "futbol", "genero": "Femenino", "edicion": "Balón de Oro 🥇", "rareza": "Leyenda 3D",
        "stats": "⚔️ ATA: 99 | 🛡️ DEF: 90 | ⚡ CTR: 100", "foto": "https://images.unsplash.com/photo-1517466787929-bc90951d0974?w=500"
    },
    {
        "id": 3, "nombre": "Kylian Mbappé", "empresa": "Real Madrid", "equipo": "Real Madrid", "nacionalidad": "🇫🇷 Francia",
        "categoria": "futbol", "genero": "Masculino", "edicion": "Supercrack 🔥", "rareza": "Holográfica 3D",
        "stats": "⚔️ ATA: 99 | 🛡️ DEF: 45 | ⚡ VEL: 100", "foto": "https://images.unsplash.com/photo-1518091043644-c1d4457512c6?w=500"
    },
    {
        "id": 4, "nombre": "Alexia Putellas", "equipo": "FC Barcelona", "nacionalidad": "🇪🇸 España",
        "categoria": "futbol", "genero": "Femenino", "edicion": "Mítica 🏆", "rareza": "Holográfica 3D",
        "stats": "⚔️ ATA: 96 | 🛡️ DEF: 88 | ⚡ CTR: 98", "foto": "https://images.unsplash.com/photo-1543326727-8a19280a97c4?w=500"
    },

    # --- 🏀 NBA / WNBA ---
    {
        "id": 5, "nombre": "LeBron James", "equipo": "Los Angeles Lakers", "nacionalidad": "🇺🇸 EE.UU.",
        "categoria": "nba", "genero": "Masculino", "edicion": "Titan Platinum 💎", "rareza": "Leyenda 3D",
        "stats": "🏀 ANOT: 99 | 🛡️ REB: 92 | ⚡ PAS: 96", "foto": "https://images.unsplash.com/photo-1546519638-68e109498ffc?w=500"
    },
    {
        "id": 6, "nombre": "Caitlin Clark", "equipo": "Indiana Fever", "nacionalidad": "🇺🇸 EE.UU.",
        "categoria": "nba", "genero": "Femenino", "edicion": "Rookie Gold 🌟", "rareza": "Holográfica 3D",
        "stats": "🏀 ANOT: 98 | 🛡️ REB: 80 | ⚡ PAS: 99", "foto": "https://images.unsplash.com/photo-1519766304817-4f37bda74a29?w=500"
    },

    # --- 🏈 NFL ---
    {
        "id": 7, "nombre": "Patrick Mahomes", "equipo": "Kansas City Chiefs", "nacionalidad": "🇺🇸 EE.UU.",
        "categoria": "nfl", "genero": "Masculino", "edicion": "MVP Diamond 🏈", "rareza": "Leyenda 3D",
        "stats": "🎯 PAS: 100 | 🏃 MOV: 92 | 💥 PWR: 95", "foto": "https://images.unsplash.com/photo-1566577739112-5180d4bf9390?w=500"
    },
    {
        "id": 8, "nombre": "Sarah Fuller", "equipo": "Vanderbilt / NFL Prospect", "nacionalidad": "🇺🇸 EE.UU.",
        "categoria": "nfl", "genero": "Femenino", "edicion": "Pioneer Special ⭐", "rareza": "Refractor 3D",
        "stats": "🎯 PAT: 94 | 🏃 VEL: 85 | 💥 PWR: 90", "foto": "https://images.unsplash.com/photo-1587280501635-68a0e82cd5ff?w=500"
    },

    # --- 🏒 HOCKEY (NHL / PWHL) ---
    {
        "id": 9, "nombre": "Connor McDavid", "equipo": "Edmonton Oilers", "nacionalidad": "🇨🇦 Canadá",
        "categoria": "hockey", "genero": "Masculino", "edicion": "Frozen Chrome 🧊", "rareza": "Leyenda 3D",
        "stats": "🏒 TIRO: 99 | 🛷 VEL: 100 | 🛡️ DEF: 85", "foto": "https://images.unsplash.com/photo-1580748141549-71748dbe0bdc?w=500"
    },
    {
        "id": 10, "nombre": "Marie-Philip Poulin", "equipo": "Montreal PWHL", "nacionalidad": "🇨🇦 Canadá",
        "categoria": "hockey", "genero": "Femenino", "edicion": "Captain Gold 🥇", "rareza": "Holográfica 3D",
        "stats": "🏒 TIRO: 98 | 🛷 VEL: 95 | 🛡️ DEF: 90", "foto": "https://images.unsplash.com/photo-1515703407324-5f753afd8be8?w=500"
    }
]

# --- VISTA INTERACTIVA PARA ABRIR Y REVELAR CARTAS TIPO CROMO ---
class InteractivePackView(discord.ui.View):
    def __init__(self, owner_id, cartas, deporte_nombre):
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.cartas = cartas
        self.deporte_nombre = deporte_nombre
        self.reveladas = [False] * len(cartas)
        
        self.btn_abrir = discord.ui.Button(label="✨ Romper Sobre Holográfico", style=discord.ButtonStyle.primary)
        self.btn_abrir.callback = self.abrir_sobre_callback
        self.add_item(self.btn_abrir)

    async def abrir_sobre_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("❌ Este sobre pertenece a otro usuario.", ephemeral=True)
            return

        self.clear_items()
        for idx, carta in enumerate(self.cartas):
            btn = discord.ui.Button(
                label=f"🎴 Carta #{idx+1} [Girar]", 
                style=discord.ButtonStyle.secondary, 
                custom_id=f"card_{idx}"
            )
            btn.callback = self.crear_card_callback(idx)
            self.add_item(btn)

        embed = discord.Embed(
            title=f"📦 ¡SOBRE ESPECIAL DE {self.deporte_nombre.upper()} ABIERTO!",
            description="Haz **clic izquierdo** en cada botón para **girar el cromo** y ver la foto, equipo y estadísticas en 3D.",
            color=0xFFD700
        )
        await interaction.response.edit_message(embed=embed, view=self)

    def crear_card_callback(self, idx):
        async def card_callback(interaction: discord.Interaction):
            if interaction.user.id != self.owner_id:
                await interaction.response.send_message("❌ No puedes interactuar con el sobre de otro usuario.", ephemeral=True)
                return

            self.reveladas[idx] = True
            carta = self.cartas[idx]

            self.children[idx].label = f"⭐ {carta['nombre']}"
            self.children[idx].style = discord.ButtonStyle.success
            self.children[idx].disabled = True

            embed = discord.Embed(
                title=f"✨ CROMO REVELADO: {carta['nombre']} ({carta['edicion']})",
                color=0xF1C40F
            )
            embed.add_field(name="👤 Atleta", value=f"**{carta['nombre']}** ({carta['genero']})", inline=True)
            embed.add_field(name="🛡️ Equipo / Selec.", value=carta['equipo'], inline=True)
            embed.add_field(name="🌍 Nacionalidad", value=carta['nacionalidad'], inline=True)
            embed.add_field(name="📊 Atributos 3D", value=carta['stats'], inline=False)
            embed.set_image(url=carta["foto"])
            embed.set_footer(text=f"Rareza: {carta['rareza']} | Colección Oficial 2026")

            await interaction.response.edit_message(embed=embed, view=self)

        return card_callback

@bot.event
async def on_ready():
    print(f'✅ Bot masivo conectado correctamente como {bot.user.name}.')

# --- COMANDO SOBRE ---
@bot.command(name="sobre")
async def abrir_sobre(ctx, deporte: str = None):
    if not deporte or deporte.lower() not in ["futbol", "nba", "nfl", "hockey"]:
        await ctx.send("❌ Uso correcto: `!sobre futbol`, `!sobre nba`, `!sobre nfl` o `!sobre hockey`.")
        return

    deporte = deporte.lower()
    user_id = ctx.author.id
    ahora = datetime.now()

    cursor.execute("SELECT ultimo_sobre FROM cooldowns WHERE user_id = ? AND deporte = ?", (user_id, deporte))
    resultado = cursor.fetchone()

    if resultado:
        ultimo_tiempo = datetime.fromisoformat(resultado[0])
        if ahora - ultimo_tiempo < timedelta(minutes=30):
            restante = timedelta(minutes=30) - (ahora - ultimo_tiempo)
            m, s = divmod(int(restante.total_seconds()), 60)
            await ctx.send(f"⏳ **{ctx.author.name}**, espera **{m}m {s}s** para tu próximo sobre de {deporte.upper()}.")
            return

    cursor.execute("INSERT OR REPLACE INTO cooldowns VALUES (?, ?, ?)", (user_id, deporte, ahora.isoformat()))
    conn.commit()

    cromos_disponibles = [c for c in CROMOS_DATABASE if c["categoria"] == deporte]
    sobre_cartas = random.choices(cromos_disponibles, k=8)

    for cromo in sobre_cartas:
        try:
            cursor.execute("INSERT INTO inventario VALUES (?, ?)", (user_id, cromo["id"]))
        except sqlite3.IntegrityError:
            pass
    conn.commit()

    view = InteractivePackView(user_id, sobre_cartas, deporte)
    embed = discord.Embed(
        title=f"📦 ¡SOBRE GOLD EDICIÓN 3D ({deporte.upper()})!",
        description=f"¡Hola **{ctx.author.name}**! Tienes 8 cromos sin abrir.\nHaz clic en el botón para romper el sello.",
        color=0xE67E22
    )
    await ctx.send(embed=embed, view=view)

# --- COMANDO TRADE ---
@bot.command(name="trade")
async def intercambiar(ctx, usuario: discord.Member, tu_cromo_id: int, su_cromo_id: int):
    if usuario.id == ctx.author.id:
        await ctx.send("❌ No puedes intercambiar contigo mismo.")
        return

    cursor.execute("SELECT * FROM inventario WHERE user_id = ? AND cromo_id = ?", (ctx.author.id, tu_cromo_id))
    if not cursor.fetchone():
        await ctx.send(f"❌ No tienes la carta #{tu_cromo_id}.")
        return

    cursor.execute("SELECT * FROM inventario WHERE user_id = ? AND cromo_id = ?", (usuario.id, su_cromo_id))
    if not cursor.fetchone():
        await ctx.send(f"❌ {usuario.mention} no tiene la carta #{su_cromo_id}.")
        return

    cursor.execute("DELETE FROM inventario WHERE user_id = ? AND cromo_id = ?", (ctx.author.id, tu_cromo_id))
    cursor.execute("DELETE FROM inventario WHERE user_id = ? AND cromo_id = ?", (usuario.id, su_cromo_id))
    cursor.execute("INSERT INTO inventario VALUES (?, ?)", (ctx.author.id, su_cromo_id))
    cursor.execute("INSERT INTO inventario VALUES (?, ?)", (usuario.id, tu_cromo_id))
    conn.commit()

    await ctx.send(f"🤝 **¡Intercambio Oficial Completado!**\n{ctx.author.mention} y {usuario.mention} han intercambiado sus cromos con éxito.")

# --- COMANDO REGLAS DE COMUNIDAD GRANDE (750k USUARIOS) ---
@bot.command(name="reglas")
async def mostrar_reglas(ctx):
    embed = discord.Embed(
        title="📜 REGLAMENTO OFICIAL DE LA COMUNIDAD (750.000+ MIEMBROS)",
        description="Para garantizar una convivencia sana y un juego justo, todos los miembros deben cumplir las siguientes normas:",
        color=0xE74C3C
    )
    embed.add_field(name="1. Respeto y Convivencia", value="Prohibido el acoso, discurso de odio, discriminación o insultos en cualquier canal.", inline=False)
    embed.add_field(name="2. Comercio e Intercambios", value="Usa exclusivamente el comando `!trade` en los canales `#intercambios-[deporte]`. Prohibida la venta de cartas por dinero real.", inline=False)
    embed.add_field(name="3. Spam y Contenido Multicuenta", value="Prohibido el uso de cuentas secundarias (bots o alts) para farmear sobres. Prohibido el spam y auto-promoción.", inline=False)
    embed.add_field(name="4. Canales Temáticos", value="Respeta la temática de cada canal (`#chat-[deporte]`, `#galeria-[deporte]`).", inline=False)
    embed.set_footer(text="El incumplimiento de las normas conllevará un silencio (mute) o baneo definitivo.")
    await ctx.send(embed=embed)

# --- CONFIGURACIÓN AUTOMÁTICA DE CANALES ---
@bot.command(name="setup_canales")
@commands.has_permissions(administrator=True)
async def setup_canales(ctx):
    guild = ctx.guild
    
    # 1. Categoría Principal y Anuncios
    cat_general = await guild.create_category("🎴 JUEGO DE CROMOS GENERAL")
    chan_reglas = await guild.create_text_channel("anuncios-y-reglas", category=cat_general)
    await guild.create_text_channel("drops-especiales", category=cat_general)

    # Publicar reglas en el canal recién creado
    embed_reglas = discord.Embed(
        title="📜 REGLAMENTO DE LA COMUNIDAD",
        description="Normas generales para mantener un entorno seguro e imparcial en el servidor.",
        color=0xE74C3C
    )
    embed_reglas.add_field(name="1. Respeto", value="No insultar ni acosar a otros usuarios.")
    embed_reglas.add_field(name="2. Uso de Comandos", value="Abre sobres solo en los chats correspondientes (`!sobre [deporte]`).")
    embed_reglas.add_field(name="3. Tradeo Seguro", value="Usa siempre `!trade` en los canales de intercambios.")
    await chan_reglas.send(embed=embed_reglas)

    # 2. Categorías Deportivas
    deportes = [("⚽ FÚTBOL", "futbol"), ("🏀 NBA", "nba"), ("🏈 NFL", "nfl"), ("🏒 HOCKEY", "hockey")]
    for titulo, prefijo in deportes:
        cat = await guild.create_category(titulo)
        await guild.create_text_channel(f"chat-{prefijo}", category=cat)
        await guild.create_text_channel(f"intercambios-{prefijo}", category=cat)
        await guild.create_text_channel(f"galeria-{prefijo}", category=cat)

    await ctx.send("✅ ¡Estructura para comunidad masiva y canales creados con éxito!")

# --- SERVIDOR WEB FLASK (KEEP-ALIVE RENDER) ---
app = Flask('')

@app.route('/')
def home():
    return "¡Servidor de cromos 3D activo 24/7!"

def run_web():
    app.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = Thread(target=run_web)
    t.start()

if __name__ == "__main__":
    keep_alive()
    bot.run(os.environ.get("DISCORD_TOKEN"))
