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

# --- BASE DE DATOS DE CROMOS (HOMBRES Y MUJERES CATEGORIZADOS POR DEPORTE) ---
CROMOS_DATABASE = [
    # --- ⚽ FÚTBOL ---
    {"id": 1, "nombre": "Lionel Messi", "empresa": "Panini Prizm", "categoria": "futbol", "genero": "Masculino", "rareza": "Leyenda", "foto": "https://images.unsplash.com/photo-1508098682722-e99c43a406b2?w=500"},
    {"id": 2, "nombre": "Kylian Mbappé", "empresa": "Topps Chrome", "categoria": "futbol", "genero": "Masculino", "rareza": "Holográfica", "foto": "https://images.unsplash.com/photo-1518091043644-c1d4457512c6?w=500"},
    {"id": 3, "nombre": "Erling Haaland", "empresa": "Topps Chrome", "categoria": "futbol", "genero": "Masculino", "rareza": "Refractor", "foto": "https://images.unsplash.com/photo-1579952363873-27f3bade9f55?w=500"},
    {"id": 4, "nombre": "Jude Bellingham", "empresa": "Panini Adrenalyn", "categoria": "futbol", "genero": "Masculino", "rareza": "Especial", "foto": "https://images.unsplash.com/photo-1517466787929-bc90951d0974?w=500"},
    {"id": 5, "nombre": "Alexia Putellas", "empresa": "Panini FIFA", "categoria": "futbol", "genero": "Femenino", "rareza": "Leyenda", "foto": "https://images.unsplash.com/photo-1543326727-8a19280a97c4?w=500"},
    {"id": 6, "nombre": "Aitana Bonmatí", "empresa": "Topps Chrome", "categoria": "futbol", "genero": "Femenino", "rareza": "Holográfica", "foto": "https://images.unsplash.com/photo-1517466787929-bc90951d0974?w=500"},
    {"id": 7, "nombre": "Sam Kerr", "empresa": "Panini Prizm", "categoria": "futbol", "genero": "Femenino", "rareza": "Refractor", "foto": "https://images.unsplash.com/photo-1560272564-6694ea693db1?w=500"},
    {"id": 8, "nombre": "Alex Morgan", "empresa": "Panini Select", "categoria": "futbol", "genero": "Femenino", "rareza": "Base", "foto": "https://images.unsplash.com/photo-1517466787929-bc90951d0974?w=500"},

    # --- 🏀 BALONCESTO / NBA / WNBA ---
    {"id": 9, "nombre": "LeBron James", "empresa": "Panini Prizm", "categoria": "nba", "genero": "Masculino", "rareza": "Leyenda", "foto": "https://images.unsplash.com/photo-1546519638-68e109498ffc?w=500"},
    {"id": 10, "nombre": "Stephen Curry", "empresa": "Panini National Treasures", "categoria": "nba", "genero": "Masculino", "rareza": "Holográfica", "foto": "https://images.unsplash.com/photo-1519766304817-4f37bda74a29?w=500"},
    {"id": 11, "nombre": "Luka Dončić", "empresa": "Panini Donruss", "categoria": "nba", "genero": "Masculino", "rareza": "Refractor", "foto": "https://images.unsplash.com/photo-1518063319789-7217e6706b04?w=500"},
    {"id": 12, "nombre": "Victor Wembanyama", "empresa": "Panini Prizm Rookie", "categoria": "nba", "genero": "Masculino", "rareza": "Leyenda", "foto": "https://images.unsplash.com/photo-1546519638-68e109498ffc?w=500"},
    {"id": 13, "nombre": "Caitlin Clark", "empresa": "Panini Instant WNBA", "categoria": "nba", "genero": "Femenino", "rareza": "Leyenda", "foto": "https://images.unsplash.com/photo-1546519638-68e109498ffc?w=500"},
    {"id": 14, "nombre": "A'ja Wilson", "empresa": "Panini Prizm WNBA", "categoria": "nba", "genero": "Femenino", "rareza": "Holográfica", "foto": "https://images.unsplash.com/photo-1519766304817-4f37bda74a29?w=500"},
    {"id": 15, "nombre": "Sabrina Ionescu", "empresa": "Panini Select WNBA", "categoria": "nba", "genero": "Femenino", "rareza": "Refractor", "foto": "https://images.unsplash.com/photo-1518063319789-7217e6706b04?w=500"},
    {"id": 16, "nombre": "Breanna Stewart", "empresa": "Panini Donruss WNBA", "categoria": "nba", "genero": "Femenino", "rareza": "Especial", "foto": "https://images.unsplash.com/photo-1546519638-68e109498ffc?w=500"},

    # --- 🏈 FÚTBOL AMERICANO / NFL ---
    {"id": 17, "nombre": "Patrick Mahomes", "empresa": "Panini Mosaic", "categoria": "nfl", "genero": "Masculino", "rareza": "Leyenda", "foto": "https://images.unsplash.com/photo-1566577739112-5180d4bf9390?w=500"},
    {"id": 18, "nombre": "Travis Kelce", "empresa": "Panini Prizm", "categoria": "nfl", "genero": "Masculino", "rareza": "Holográfica", "foto": "https://images.unsplash.com/photo-1587280501635-68a0e82cd5ff?w=500"},
    {"id": 19, "nombre": "Joe Burrow", "empresa": "Donruss Optic", "categoria": "nfl", "genero": "Masculino", "rareza": "Refractor", "foto": "https://images.unsplash.com/photo-1566577739112-5180d4bf9390?w=500"},
    {"id": 20, "nombre": "Josh Allen", "empresa": "Panini Select", "categoria": "nfl", "genero": "Masculino", "rareza": "Especial", "foto": "https://images.unsplash.com/photo-1587280501635-68a0e82cd5ff?w=500"},
    {"id": 21, "nombre": "Sarah Fuller", "empresa": "Panini Honors", "categoria": "nfl", "genero": "Femenino", "rareza": "Especial", "foto": "https://images.unsplash.com/photo-1566577739112-5180d4bf9390?w=500"},
    {"id": 22, "nombre": "Carli Lloyd (NFL Tryout)", "empresa": "Topps Special", "categoria": "nfl", "genero": "Femenino", "rareza": "Holográfica", "foto": "https://images.unsplash.com/photo-1587280501635-68a0e82cd5ff?w=500"},

    # --- 🏒 HOCKEY / NHL ---
    {"id": 23, "nombre": "Connor McDavid", "empresa": "Upper Deck Young Guns", "categoria": "hockey", "genero": "Masculino", "rareza": "Leyenda", "foto": "https://images.unsplash.com/photo-1580748141549-71748dbe0bdc?w=500"},
    {"id": 24, "nombre": "Alex Ovechkin", "empresa": "Upper Deck Series 1", "categoria": "hockey", "genero": "Masculino", "rareza": "Holográfica", "foto": "https://images.unsplash.com/photo-1515703407324-5f753afd8be8?w=500"},
    {"id": 25, "nombre": "Sidney Crosby", "empresa": "Topps Hockey", "categoria": "hockey", "genero": "Masculino", "rareza": "Refractor", "foto": "https://images.unsplash.com/photo-1580748141549-71748dbe0bdc?w=500"},
    {"id": 26, "nombre": "Connor Bedard", "empresa": "Upper Deck Canvas", "categoria": "hockey", "genero": "Masculino", "rareza": "Leyenda", "foto": "https://images.unsplash.com/photo-1515703407324-5f753afd8be8?w=500"},
    {"id": 27, "nombre": "Marie-Philip Poulin", "empresa": "Upper Deck PWHL", "categoria": "hockey", "genero": "Femenino", "rareza": "Leyenda", "foto": "https://images.unsplash.com/photo-1580748141549-71748dbe0bdc?w=500"},
    {"id": 28, "nombre": "Sarah Nurse", "empresa": "Upper Deck Series 2", "categoria": "hockey", "genero": "Femenino", "rareza": "Holográfica", "foto": "https://images.unsplash.com/photo-1515703407324-5f753afd8be8?w=500"},
    {"id": 29, "nombre": "Hilary Knight", "empresa": "Upper Deck PWHL", "categoria": "hockey", "genero": "Femenino", "rareza": "Refractor", "foto": "https://images.unsplash.com/photo-1580748141549-71748dbe0bdc?w=500"},
    {"id": 30, "nombre": "Kendall Coyne Schofield", "empresa": "Upper Deck Base", "categoria": "hockey", "genero": "Femenino", "rareza": "Base", "foto": "https://images.unsplash.com/photo-1515703407324-5f753afd8be8?w=500"}
]

# --- VISTA PARA RECLAMAR DROPS AUTOMÁTICOS ---
class ClaimButton(discord.ui.View):
    def __init__(self, cromo):
        super().__init__(timeout=60)
        self.cromo = cromo
        self.reclamado = False

    @discord.ui.button(label="🎴 ¡Reclamar Cromo Único!", style=discord.ButtonStyle.green)
    async def claim_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.reclamado:
            await interaction.response.send_message("❌ Este cromo ya fue reclamado por otro usuario.", ephemeral=True)
            return

        user_id = interaction.user.id
        try:
            cursor.execute("INSERT INTO inventario (user_id, cromo_id) VALUES (?, ?)", (user_id, self.cromo["id"]))
            conn.commit()
            self.reclamado = True
            button.disabled = True
            button.label = f"Reclamado por {interaction.user.name}"
            button.style = discord.ButtonStyle.secondary
            await interaction.response.edit_message(view=self)
            await interaction.followup.send(f"🎉 **{interaction.user.mention}** reclamó el cromo especial de **{self.cromo['nombre']}** ({self.cromo['genero']})!")
        except sqlite3.IntegrityError:
            await interaction.response.send_message(f"⚠️ Ya tienes a **{self.cromo['nombre']}** en tu colección.", ephemeral=True)

@bot.event
async def on_ready():
    print(f'✅ Bot conectado correctamente como {bot.user.name}.')

# --- COMANDO DE SOBRES (8 CARTAS CADA 30 MINUTOS) ---
@bot.command(name="sobre")
async def abrir_sobre(ctx, deporte: str = None):
    if not deporte:
        await ctx.send("❌ Debes especificar la categoría deportiva. Opciones: `futbol`, `nba`, `nfl`, `hockey`.\nEjemplo: `!sobre futbol`")
        return

    deporte = deporte.lower()
    validos = ["futbol", "nba", "nfl", "hockey"]

    if deporte not in validos:
        await ctx.send("❌ Deporte no válido. Elige entre: `futbol`, `nba`, `nfl` o `hockey`.")
        return

    user_id = ctx.author.id
    ahora = datetime.now()

    cursor.execute("SELECT ultimo_sobre FROM cooldowns WHERE user_id = ? AND deporte = ?", (user_id, deporte))
    resultado = cursor.fetchone()

    if resultado:
        ultimo_tiempo = datetime.fromisoformat(resultado[0])
        diferencia = ahora - ultimo_tiempo
        if diferencia < timedelta(minutes=30):
            tiempo_restante = timedelta(minutes=30) - diferencia
            minutos, segundos = divmod(int(tiempo_restante.total_seconds()), 60)
            await ctx.send(f"⏳ **{ctx.author.name}**, debes esperar **{minutos}m {segundos}s** para abrir otro sobre de {deporte.upper()}.")
            return

    cursor.execute("INSERT OR REPLACE INTO cooldowns (user_id, deporte, ultimo_sobre) VALUES (?, ?, ?)", 
                   (user_id, deporte, ahora.isoformat()))
    conn.commit()

    cromos_disponibles = [c for c in CROMOS_DATABASE if c["categoria"] == deporte]
    sobre_cartas = random.choices(cromos_disponibles, k=8)

    for cromo in sobre_cartas:
        try:
            cursor.execute("INSERT INTO inventario (user_id, cromo_id) VALUES (?, ?)", (user_id, cromo["id"]))
        except sqlite3.IntegrityError:
            pass
    conn.commit()

    embed = discord.Embed(
        title=f"📦 ¡Sobre de {deporte.upper()} Abierto!",
        description=f"Has recibido **8 cartas** (Masculinas y Femeninas). ¡Guardadas en tu álbum!",
        color=0xF1C40F
    )

    descripcion_cartas = ""
    for i, carta in enumerate(sobre_cartas, 1):
        descripcion_cartas += f"**{i}.** [{carta['empresa']}] **{carta['nombre']}** ({carta['genero']}) - *{carta['rareza']}*\n"

    embed.add_field(name="🎴 Contenido del Sobre:", value=descripcion_cartas, inline=False)
    embed.set_image(url=sobre_cartas[0]["foto"])
    embed.set_footer(text="Colección Oficial | Vuelve en 30 minutos.")

    await ctx.send(embed=embed)

# --- COMANDO INTERCAMBIO AUTOMÁTICO ENTRE USUARIOS ---
@bot.command(name="trade")
async def intercambiar(ctx, usuario: discord.Member, tu_cromo_id: int, su_cromo_id: int):
    if usuario.id == ctx.author.id:
        await ctx.send("❌ No puedes hacer intercambios contigo mismo.")
        return

    # Verificar que el usuario 1 tiene el cromo
    cursor.execute("SELECT * FROM inventario WHERE user_id = ? AND cromo_id = ?", (ctx.author.id, tu_cromo_id))
    if not cursor.fetchone():
        await ctx.send(f"❌ No posees el cromo con ID **#{tu_cromo_id}** en tu inventario.")
        return

    # Verificar que el usuario 2 tiene el cromo
    cursor.execute("SELECT * FROM inventario WHERE user_id = ? AND cromo_id = ?", (usuario.id, su_cromo_id))
    if not cursor.fetchone():
        await ctx.send(f"❌ {usuario.mention} no posee el cromo con ID **#{su_cromo_id}**.")
        return

    # Ejecutar el intercambio en la Base de Datos
    cursor.execute("DELETE FROM inventario WHERE user_id = ? AND cromo_id = ?", (ctx.author.id, tu_cromo_id))
    cursor.execute("DELETE FROM inventario WHERE user_id = ? AND cromo_id = ?", (usuario.id, su_cromo_id))
    cursor.execute("INSERT INTO inventario (user_id, cromo_id) VALUES (?, ?)", (ctx.author.id, su_cromo_id))
    cursor.execute("INSERT INTO inventario (user_id, cromo_id) VALUES (?, ?)", (usuario.id, tu_cromo_id))
    conn.commit()

    # Obtener nombres de los cromos para el mensaje
    cromo_1 = next(c for c in CROMOS_DATABASE if c["id"] == tu_cromo_id)
    cromo_2 = next(c for c in CROMOS_DATABASE if c["id"] == su_cromo_id)

    await ctx.send(f"🤝 **¡Intercambio Éxitoso!**\n{ctx.author.mention} entregó a **{cromo_1['nombre']}** y recibió a **{cromo_2['nombre']}** de {usuario.mention}.")

# --- COMANDO ÁLBUM ---
@bot.command(name="album")
async def ver_album(ctx):
    user_id = ctx.author.id
    cursor.execute("SELECT cromo_id FROM inventario WHERE user_id = ?", (user_id,))
    filas = cursor.fetchall()
    ids_obtenidos = [f[0] for f in filas]

    embed = discord.Embed(title=f"🎴 Colección Completa de {ctx.author.name}", color=0x9B59B6)
    
    descripcion = ""
    for cromo in CROMOS_DATABASE:
        if cromo["id"] in ids_obtenidos:
            descripcion += f"✅ **#{cromo['id']} {cromo['nombre']}** ({cromo['categoria'].upper()} - {cromo['genero']})\n"
        else:
            descripcion += f"❌ **#{cromo['id']} ???** ({cromo['categoria'].upper()})\n"

    embed.description = descripcion
    embed.set_footer(text=f"Progreso: {len(ids_obtenidos)}/{len(CROMOS_DATABASE)} cromos conseguidos.")
    await ctx.send(embed=embed)

# --- COMANDO DROP AUTOMÁTICO PARA ADMINS ---
@bot.command(name="drop")
@commands.has_permissions(administrator=True)
async def drop_cromo(ctx):
    cromo = random.choice(CROMOS_DATABASE)
    embed = discord.Embed(
        title="✨ ¡CROMO EXCLUSIVO APARECIÓ!",
        description=f"**Deporte:** {cromo['categoria'].upper()}\n**Atleta:** {cromo['nombre']}\n**Género:** {cromo['genero']}\n**Rareza:** {cromo['rareza']}\n\n¡Sé el primero en pulsar el botón para conseguirlo!",
        color=0x3498DB
    )
    embed.set_image(url=cromo["foto"])
    view = ClaimButton(cromo)
    await ctx.send(embed=embed, view=view)

# --- COMANDO CONFIGURACIÓN COMPLETA DE ESTRUCTURA Y CANALES ---
@bot.command(name="setup_canales")
@commands.has_permissions(administrator=True)
async def setup_canales(ctx):
    guild = ctx.guild
    
    # 1. Categoría General
    cat_general = await guild.create_category("🎴 JUEGO DE CROMOS GENERAL")
    await guild.create_text_channel("anuncios-y-reglas", category=cat_general)
    await guild.create_text_channel("drops-especiales", category=cat_general)

    # 2. Categorías por cada Deporte con sus 3 canales requeridos
    deportes_config = [
        ("⚽ FÚTBOL", "futbol"),
        ("🏀 NBA", "nba"),
        ("🏈 NFL", "nfl"),
        ("🏒 HOCKEY", "hockey")
    ]

    for titulo_categoria, prefijo in deportes_config:
        cat = await guild.create_category(titulo_categoria)
        
        # Chat de texto
        await guild.create_text_channel(
            f"chat-{prefijo}", 
            category=cat, 
            topic=f"Chat general para hablar de {prefijo.upper()} y usar !sobre {prefijo}."
        )
        
        # Canal de intercambios
        await guild.create_text_channel(
            f"intercambios-{prefijo}", 
            category=cat, 
            topic=f"Canal de tradeos. Usa !trade @usuario ID_tu_cromo ID_su_cromo"
        )
        
        # Galería
        await guild.create_text_channel(
            f"galeria-{prefijo}", 
            category=cat, 
            topic=f"Muestra aquí tus cartas conseguidas o usa !album."
        )

    await ctx.send("✅ ¡Estructura creada completamente! Se generaron las categorías de Fútbol, NBA, NFL y Hockey con sus canales de **Chat de texto**, **Intercambios** y **Galería**.")

@setup_canales.error
async def setup_canales_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Necesitas permisos de Administrador para ejecutar este comando.")

# --- SERVIDOR WEB FLASK (KEEP-ALIVE RENDER) ---
app = Flask('')

@app.route('/')
def home():
    print("¡Ping recibido! Servidor activo.")
    return "¡El bot de cromos está activo 24/7!"

def run_web():
    app.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = Thread(target=run_web)
    t.start()

# --- EJECUCIÓN PRINCIPAL ---
if __name__ == "__main__":
    keep_alive()
    bot.run(os.environ.get("DISCORD_TOKEN"))
