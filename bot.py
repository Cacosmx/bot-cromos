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

# --- BASE DE DATOS MASIVA DE CROMOS (PANINI, TOPPS, UPPER DECK, ETC.) ---
CROMOS_DATABASE = [
    # --- FÚTBOL MASCULINO (Panini Prizm / Topps Chrome) ---
    {"id": 1, "nombre": "Lionel Messi", "empresa": "Panini Prizm", "categoria": "⚽ Fútbol Masculino", "rareza": "Leyenda", "foto": "https://images.unsplash.com/photo-1508098682722-e99c43a406b2?w=500"},
    {"id": 2, "nombre": "Kylian Mbappé", "empresa": "Topps Chrome", "categoria": "⚽ Fútbol Masculino", "rareza": "Holográfica", "foto": "https://images.unsplash.com/photo-1518091043644-c1d4457512c6?w=500"},
    {"id": 3, "nombre": "Erling Haaland", "empresa": "Topps Chrome", "categoria": "⚽ Fútbol Masculino", "rareza": "Refractor", "foto": "https://images.unsplash.com/photo-1579952363873-27f3bade9f55?w=500"},
    {"id": 4, "nombre": "Jude Bellingham", "empresa": "Panini Adrenalyn", "categoria": "⚽ Fútbol Masculino", "rareza": "Especial", "foto": "https://images.unsplash.com/photo-1517466787929-bc90951d0974?w=500"},
    {"id": 5, "nombre": "Vinicius Jr", "empresa": "Topps Living", "categoria": "⚽ Fútbol Masculino", "rareza": "Refractor", "foto": "https://images.unsplash.com/photo-1560272564-6694ea693db1?w=500"},
    {"id": 6, "nombre": "Kevin De Bruyne", "empresa": "Panini Prizm", "categoria": "⚽ Fútbol Masculino", "rareza": "Base", "foto": "https://images.unsplash.com/photo-1508098682722-e99c43a406b2?w=500"},

    # --- FÚTBOL FEMENINO (Panini FIFA Women's / Topps) ---
    {"id": 7, "nombre": "Alexia Putellas", "empresa": "Panini FIFA", "categoria": "⚽ Fútbol Femenino", "rareza": "Leyenda", "foto": "https://images.unsplash.com/photo-1543326727-8a19280a97c4?w=500"},
    {"id": 8, "nombre": "Aitana Bonmatí", "empresa": "Topps Chrome", "categoria": "⚽ Fútbol Femenino", "rareza": "Holográfica", "foto": "https://images.unsplash.com/photo-1517466787929-bc90951d0974?w=500"},
    {"id": 9, "nombre": "Sam Kerr", "empresa": "Panini Prizm", "categoria": "⚽ Fútbol Femenino", "rareza": "Refractor", "foto": "https://images.unsplash.com/photo-1560272564-6694ea693db1?w=500"},
    {"id": 10, "nombre": "Trinity Rodman", "empresa": "Topps NWSL", "categoria": "⚽ Fútbol Femenino", "rareza": "Especial", "foto": "https://images.unsplash.com/photo-1543326727-8a19280a97c4?w=500"},
    {"id": 11, "nombre": "Alex Morgan", "empresa": "Panini Select", "categoria": "⚽ Fútbol Femenino", "rareza": "Base", "foto": "https://images.unsplash.com/photo-1517466787929-bc90951d0974?w=500"},

    # --- NBA (Panini Prizm / Hoops / Donruss) ---
    {"id": 12, "nombre": "LeBron James", "empresa": "Panini Prizm", "categoria": "🏀 NBA", "rareza": "Leyenda", "foto": "https://images.unsplash.com/photo-1546519638-68e109498ffc?w=500"},
    {"id": 13, "nombre": "Stephen Curry", "empresa": "Panini National Treasures", "categoria": "🏀 NBA", "rareza": "Holográfica", "foto": "https://images.unsplash.com/photo-1519766304817-4f37bda74a29?w=500"},
    {"id": 14, "nombre": "Luka Dončić", "empresa": "Panini Donruss", "categoria": "🏀 NBA", "rareza": "Refractor", "foto": "https://images.unsplash.com/photo-1518063319789-7217e6706b04?w=500"},
    {"id": 15, "nombre": "Victor Wembanyama", "empresa": "Panini Prizm Rookie", "categoria": "🏀 NBA", "rareza": "Leyenda", "foto": "https://images.unsplash.com/photo-1546519638-68e109498ffc?w=500"},
    {"id": 16, "nombre": "Giannis Antetokounmpo", "empresa": "Topps Chrome", "categoria": "🏀 NBA", "rareza": "Especial", "foto": "https://images.unsplash.com/photo-1519766304817-4f37bda74a29?w=500"},

    # --- NFL (Panini Mosaic / Donruss Optic) ---
    {"id": 17, "nombre": "Patrick Mahomes", "empresa": "Panini Mosaic", "categoria": "🏈 NFL", "rareza": "Leyenda", "foto": "https://images.unsplash.com/photo-1566577739112-5180d4bf9390?w=500"},
    {"id": 18, "nombre": "Travis Kelce", "empresa": "Panini Prizm", "categoria": "🏈 NFL", "rareza": "Holográfica", "foto": "https://images.unsplash.com/photo-1587280501635-68a0e82cd5ff?w=500"},
    {"id": 19, "nombre": "Joe Burrow", "empresa": "Donruss Optic", "categoria": "🏈 NFL", "rareza": "Refractor", "foto": "https://images.unsplash.com/photo-1566577739112-5180d4bf9390?w=500"},
    {"id": 20, "nombre": "Josh Allen", "empresa": "Panini Select", "categoria": "🏈 NFL", "rareza": "Especial", "foto": "https://images.unsplash.com/photo-1587280501635-68a0e82cd5ff?w=500"},

    # --- HOCKEY / NHL (Upper Deck Young Guns / Topps) ---
    {"id": 21, "nombre": "Connor McDavid", "empresa": "Upper Deck Young Guns", "categoria": "🏒 Hockey (NHL)", "rareza": "Leyenda", "foto": "https://images.unsplash.com/photo-1580748141549-71748dbe0bdc?w=500"},
    {"id": 22, "nombre": "Alex Ovechkin", "empresa": "Upper Deck Series 1", "categoria": "🏒 Hockey (NHL)", "rareza": "Holográfica", "foto": "https://images.unsplash.com/photo-1515703407324-5f753afd8be8?w=500"},
    {"id": 23, "nombre": "Sidney Crosby", "empresa": "Topps Hockey", "categoria": "🏒 Hockey (NHL)", "rareza": "Refractor", "foto": "https://images.unsplash.com/photo-1580748141549-71748dbe0bdc?w=500"},
    {"id": 24, "nombre": "Connor Bedard", "empresa": "Upper Deck Canvas", "categoria": "🏒 Hockey (NHL)", "rareza": "Leyenda", "foto": "https://images.unsplash.com/photo-1515703407324-5f753afd8be8?w=500"}
]

# --- VISTA PARA RECLAMAR DROPS AUTOMÁTICOS EN CANAL ---
class ClaimButton(discord.ui.View):
    def __init__(self, cromo):
        super().__init__(timeout=60)
        self.cromo = cromo
        self.reclamado = False

    @discord.ui.button(label="🎴 ¡Reclamar Cromo Único!", style=discord.ButtonStyle.green)
    async def claim_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.reclamado:
            await interaction.response.send_message("❌ Este cromo ya fue reclamado.", ephemeral=True)
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
            await interaction.followup.send(f"🎉 **{interaction.user.mention}** atrapó el cromo de **{self.cromo['nombre']}** ({self.cromo['empresa']})!")
        except sqlite3.IntegrityError:
            await interaction.response.send_message(f"⚠️ Ya tienes a **{self.cromo['nombre']}** en tu colección.", ephemeral=True)

@bot.event
async def on_ready():
    print(f'✅ Bot conectado correctamente como {bot.user.name}.')

# --- COMANDO DE SOBRES (8 CARTAS CADA 30 MINUTOS) ---
@bot.command(name="sobre")
async def abrir_sobre(ctx, deporte: str = None):
    if not deporte:
        await ctx.send("❌ Debes especificar el deporte. Opciones: `futbol_m`, `futbol_f`, `nba`, `nfl`, `nhl`.\nEjemplo: `!sobre nba`")
        return

    deporte = deporte.lower()
    mapping_deportes = {
        "futbol_m": "⚽ Fútbol Masculino",
        "futbol_f": "⚽ Fútbol Femenino",
        "nba": "🏀 NBA",
        "nfl": "🏈 NFL",
        "nhl": "🏒 Hockey (NHL)"
    }

    if deporte not in mapping_deportes:
        await ctx.send("❌ Deporte no válido. Usa: `futbol_m`, `futbol_f`, `nba`, `nfl` o `nhl`.")
        return

    categoria_seleccionada = mapping_deportes[deporte]
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
            await ctx.send(f"⏳ **{ctx.author.name}**, debes esperar **{minutos}m {segundos}s** para abrir otro sobre de este deporte.")
            return

    cursor.execute("INSERT OR REPLACE INTO cooldowns (user_id, deporte, ultimo_sobre) VALUES (?, ?, ?)", 
                   (user_id, deporte, ahora.isoformat()))
    conn.commit()

    cromos_disponibles = [c for c in CROMOS_DATABASE if c["categoria"] == categoria_seleccionada]
    sobre_cartas = random.choices(cromos_disponibles, k=8)

    for cromo in sobre_cartas:
        try:
            cursor.execute("INSERT INTO inventario (user_id, cromo_id) VALUES (?, ?)", (user_id, cromo["id"]))
        except sqlite3.IntegrityError:
            pass
    conn.commit()

    embed = discord.Embed(
        title=f"📦 ¡Sobre de {categoria_seleccionada} Abierto!",
        description=f"Has abierto un sobre oficial con **8 cartas**. ¡Nuevas adiciones registradas en tu álbum!",
        color=0xF1C40F
    )

    descripcion_cartas = ""
    for i, carta in enumerate(sobre_cartas, 1):
        descripcion_cartas += f"**{i}.** [{carta['empresa']}] **{carta['nombre']}** (*{carta['rareza']}*)\n"

    embed.add_field(name="🎴 Contenido del Sobre:", value=descripcion_cartas, inline=False)
    embed.set_image(url=sobre_cartas[0]["foto"])
    embed.set_footer(text="Patrocinado por Nike, Adidas, Puma, Reebok, Asics & Champions | Vuelve en 30 min.")

    await ctx.send(embed=embed)

# --- COMANDO DROP AUTOMÁTICO (ADMINS) ---
@bot.command(name="drop")
@commands.has_permissions(administrator=True)
async def drop_cromo(ctx):
    cromo = random.choice(CROMOS_DATABASE)
    embed = discord.Embed(
        title="✨ ¡CROMO ESPECIAL DE PATROCINADOR!",
        description=f"**Deporte:** {cromo['categoria']}\n**Edición:** {cromo['empresa']}\n**Jugador:** {cromo['nombre']}\n**Rareza:** {cromo['rareza']}\n\n¡Presiona el botón para reclamarlo!",
        color=0x3498DB
    )
    embed.set_image(url=cromo["foto"])
    embed.set_footer(text="Nike & Adidas Drop Oficial")
    view = ClaimButton(cromo)
    await ctx.send(embed=embed, view=view)

# --- COMANDO ÁLBUM ---
@bot.command(name="album")
async def ver_album(ctx):
    user_id = ctx.author.id
    cursor.execute("SELECT cromo_id FROM inventario WHERE user_id = ?", (user_id,))
    filas = cursor.fetchall()
    ids_obtenidos = [f[0] for f in filas]

    embed = discord.Embed(title=f"🎴 Álbum de Colección de {ctx.author.name}", color=0x9B59B6)
    
    descripcion = ""
    for cromo in CROMOS_DATABASE:
        if cromo["id"] in ids_obtenidos:
            descripcion += f"✅ **#{cromo['id']} {cromo['nombre']}** ({cromo['empresa']}) - *{cromo['rareza']}*\n"
        else:
            descripcion += f"❌ **#{cromo['id']} ???** ({cromo['categoria']})\n"

    embed.description = descripcion
    embed.set_footer(text=f"Total en propiedad: {len(ids_obtenidos)}/{len(CROMOS_DATABASE)} cartas.")
    await ctx.send(embed=embed)

# --- COMANDO INTERCAMBIO ---
@bot.command(name="trade")
async def intercambiar(ctx, usuario: discord.Member, tu_cromo_id: int, su_cromo_id: int):
    if usuario.id == ctx.author.id:
        await ctx.send("❌ No puedes tradear contigo mismo.")
        return

    cursor.execute("SELECT * FROM inventario WHERE user_id = ? AND cromo_id = ?", (ctx.author.id, tu_cromo_id))
    if not cursor.fetchone():
        await ctx.send("❌ No tienes esa carta en tu inventario.")
        return

    cursor.execute("SELECT * FROM inventario WHERE user_id = ? AND cromo_id = ?", (usuario.id, su_cromo_id))
    if not cursor.fetchone():
        await ctx.send(f"❌ {usuario.mention} no posee la carta solicitada.")
        return

    cursor.execute("DELETE FROM inventario WHERE user_id = ? AND cromo_id = ?", (ctx.author.id, tu_cromo_id))
    cursor.execute("DELETE FROM inventario WHERE user_id = ? AND cromo_id = ?", (usuario.id, su_cromo_id))
    cursor.execute("INSERT INTO inventario (user_id, cromo_id) VALUES (?, ?)", (ctx.author.id, su_cromo_id))
    cursor.execute("INSERT INTO inventario (user_id, cromo_id) VALUES (?, ?)", (usuario.id, tu_cromo_id))
    conn.commit()

    await ctx.send(f"🤝 ¡Intercambio completado con éxito entre {ctx.author.mention} y {usuario.mention}!")

# --- COMANDO DE CONFIGURACIÓN AUTOMÁTICA DE CANALES ---
@bot.command(name="setup_canales")
@commands.has_permissions(administrator=True)
async def setup_canales(ctx):
    guild = ctx.guild
    
    # Crear categoría principal
    categoria = await guild.create_category("🎴 JUEGO DE CROMOS")
    
    # Crear canales dentro de la categoría
    await guild.create_text_channel("general-cromos", category=categoria, topic="Canal general para hablar del juego de cromos.")
    await guild.create_text_channel("apertura-sobres", category=categoria, topic="Usa aquí el comando !sobre para abrir tus sobres.")
    await guild.create_text_channel("drops-especiales", category=categoria, topic="Canal donde aparecen los drops automáticos de patrocinadores.")
    await guild.create_text_channel("intercambios", category=categoria, topic="Usa aquí el comando !trade para tradear cartas.")
    
    await ctx.send("✅ ¡Categoría y canales de cromos creados con éxito!")

@setup_canales.error
async def setup_canales_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Necesitas permisos de Administrador para ejecutar este comando.")

# --- SERVIDOR WEB FLASK (KEEP-ALIVE PARA RENDER) ---
app = Flask('')

@app.route('/')
def home():
    print("¡Ping recibida! El bot sigue activo.")
    return "¡El bot de cromos está vivo y online!"

def run_web():
    app.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = Thread(target=run_web)
    t.start()

# --- EJECUCIÓN PRINCIPAL ---
if __name__ == "__main__":
    keep_alive()
    bot.run(os.environ.get("DISCORD_TOKEN"))
