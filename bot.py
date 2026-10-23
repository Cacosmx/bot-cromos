import discord
from discord.ext import commands
import random
import sqlite3
from datetime import datetime, timedelta
import os
from flask import Flask
from threading import Thread

# Configuración de Intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- BASE DE DATOS LOCAL (INVENTARIO DE CROMOS, SOBRES Y COOLDOWNS) ---
conn = sqlite3.connect("cromos_bot.db")
cursor = conn.cursor()

# Tabla de cartas conseguidas
cursor.execute('''
CREATE TABLE IF NOT EXISTS inventario_cartas (
    user_id INTEGER,
    cromo_id TEXT,
    nombre TEXT,
    equipo TEXT,
    nacionalidad TEXT,
    categoria TEXT,
    genero TEXT,
    rareza TEXT,
    posicion TEXT,
    stats TEXT,
    foto TEXT,
    PRIMARY KEY (user_id, cromo_id)
)
''')

# Tabla de sobres guardados
cursor.execute('''
CREATE TABLE IF NOT EXISTS inventario_sobres (
    user_id INTEGER,
    deporte TEXT,
    cantidad INTEGER DEFAULT 0,
    PRIMARY KEY (user_id, deporte)
)
''')

# Tabla de tiempos de espera (cooldowns)
cursor.execute('''
CREATE TABLE IF NOT EXISTS cooldowns (
    user_id INTEGER,
    deporte TEXT,
    ultimo_sobre TIMESTAMP,
    PRIMARY KEY (user_id, deporte)
)
''')
conn.commit()

# --- BANCOS DE DATOS PARA EL GENERADOR ALGORÍTMICO ---
PAISES = {
    "futbol": ["🇪🇸 España", "🇦🇷 Argentina", "🇧🇷 Brasil", "🇫🇷 Francia", "🇬🇧 Inglaterra", "🇩🇪 Alemania", "🇮🇹 Italia", "🇳🇴 Noruega", "🇺🇸 EE.UU.", "🇲🇽 México"],
    "nba": ["🇺🇸 EE.UU.", "🇫🇷 Francia", "🇸🇮 Eslovenia", "🇷🇸 Serbia", "🇬🇷 Grecia", "🇨🇦 Canadá", "🇪🇸 España", "🇦🇺 Australia"],
    "nfl": ["🇺🇸 EE.UU.", "🇨🇦 Canadá", "🇦🇺 Australia", "🇲🇽 México", "🇬🇧 Inglaterra", "🇩🇪 Alemania"],
    "hockey": ["🇨🇦 Canadá", "🇺🇸 EE.UU.", "🇷🇺 Rusia", "🇸🇪 Suecia", "🇫🇮 Finlandia", "🇨🇿 Rep. Checa"]
}

EQUIPOS = {
    "futbol": ["FC Barcelona", "Real Madrid", "Manchester City", "Liverpool FC", "Inter Miami", "Bayern Múnich", "PSG", "Chelsea FC"],
    "nba": ["Los Angeles Lakers 🏀", "Golden State Warriors 🏀", "Boston Celtics 🏀", "Miami Heat 🏀", "Chicago Bulls 🏀", "Indiana Fever 🏀"],
    "nfl": ["Kansas City Chiefs 🏈", "San Francisco 49ers 🏈", "Dallas Cowboys 🏈", "Philadelphia Eagles 🏈", "Miami Dolphins 🏈"],
    "hockey": ["Edmonton Oilers 🏒", "Toronto Maple Leafs 🏒", "Montreal Canadiens 🏒", "Chicago Blackhawks 🏒", "Boston PWHL 🏒"]
}

POSICIONES = {
    "futbol": ["Portero", "Defensa Central", "Lateral", "Centrocampista", "Extremo", "Delantero Centro"],
    "nba": ["Base (PG)", "Escolta (SG)", "Alero (SF)", "Ala-Pívot (PF)", "Pívot (C)"],
    "nfl": ["Quarterback (QB)", "Wide Receiver (WR)", "Running Back (RB)", "Tight End (TE)", "Linebacker (LB)", "Kicker (K)"],
    "hockey": ["Centro (C)", "Extremo Izquierdo", "Extremo Derecho", "Defensa", "Portero (G)"]
}

NOMBRES_MASC = ["Mateo", "Lucas", "Liam", "Ethan", "Noah", "Gabriel", "Julian", "Alexander", "Leo", "Kylian", "Marcus", "Luka"]
APELLIDOS_MASC = ["García", "Smith", "Silva", "Dupont", "Müller", "Rossi", "Johnson", "Novak", "Williams", "Martínez"]

NOMBRES_FEM = ["Sofia", "Emma", "Olivia", "Mia", "Isabella", "Aria", "Chloe", "Zoe", "Elena", "Astrid", "Keira", "Camila"]
APELLIDOS_FEM = ["Rodriguez", "Brown", "Fernández", "Bernard", "Weber", "Ricci", "Davis", "Taylor", "Gómez", "Dubois"]

RAREZAS = [
    ("📦 Base Top", 60),
    ("💎 Special Edition", 25),
    ("🔥 Supercrack Holográfico 3D", 10),
    ("🌟 Leyenda 3D / Balón de Oro", 5)
]

FOTOS_DEMO = [
    "https://images.unsplash.com/photo-1508098682722-e99c43a406b2?w=500",
    "https://images.unsplash.com/photo-1517466787929-bc90951d0974?w=500",
    "https://images.unsplash.com/photo-1518091043644-c1d4457512c6?w=500",
    "https://images.unsplash.com/photo-1543326727-8a19280a97c4?w=500",
    "https://images.unsplash.com/photo-1546519638-68e109498ffc?w=500",
    "https://images.unsplash.com/photo-1566577739112-5180d4bf9390?w=500",
    "https://images.unsplash.com/photo-1580748141549-71748dbe0bdc?w=500"
]

def generar_cromo_dinamico(deporte):
    genero = random.choice(["Masculino", "Femenino"])
    if genero == "Masculino":
        nombre = f"{random.choice(NOMBRES_MASC)} {random.choice(APELLIDOS_MASC)}"
    else:
        nombre = f"{random.choice(NOMBRES_FEM)} {random.choice(APELLIDOS_FEM)}"

    equipo = random.choice(EQUIPOS[deporte])
    nacionalidad = random.choice(PAISES[deporte])
    posicion = random.choice(POSICIONES[deporte])
    rareza = random.choices([r[0] for r in RAREZAS], weights=[r[1] for r in RAREZAS])[0]

    if "Leyenda" in rareza:
        base = random.randint(95, 100)
    elif "Supercrack" in rareza:
        base = random.randint(90, 95)
    elif "Special" in rareza:
        base = random.randint(85, 90)
    else:
        base = random.randint(75, 84)

    stats = f"⚔️ ATA: {base} | 🛡️ DEF: {random.randint(base-10, base)} | ⚡ VEL: {random.randint(base-5, base)}"
    foto = random.choice(FOTOS_DEMO)
    cromo_id = f"{deporte[:2].upper()}-{random.randint(100000, 999999)}"

    return {
        "id": cromo_id, "nombre": nombre, "equipo": equipo, "nacionalidad": nacionalidad,
        "categoria": deporte, "genero": genero, "rareza": rareza, "posicion": posicion,
        "stats": stats, "foto": foto
    }

# --- VISTA INTERACTIVA PARA REVELAR CROMOS GIRANDO CADA CARTA ---
class FlipCardsPackView(discord.ui.View):
    def __init__(self, owner_id, cartas, deporte_nombre):
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.cartas = cartas
        self.deporte_nombre = deporte_nombre
        self.reveladas = [False] * len(cartas)

        # Generar los 8 botones de cartas ocultas desde el inicio
        for idx in range(len(self.cartas)):
            btn = discord.ui.Button(
                label=f"🎴 Carta #{idx+1} [Girar]", 
                style=discord.ButtonStyle.secondary, 
                custom_id=f"card_{idx}"
            )
            btn.callback = self.crear_card_callback(idx)
            self.add_item(btn)

    def crear_card_callback(self, idx):
        async def card_callback(interaction: discord.Interaction):
            if interaction.user.id != self.owner_id:
                await interaction.response.send_message("❌ Este sobre no te pertenece.", ephemeral=True)
                return

            if self.reveladas[idx]:
                await interaction.response.send_message("⚠️ Esta carta ya la has girado.", ephemeral=True)
                return

            self.reveladas[idx] = True
            carta = self.cartas[idx]

            # Actualizar botón
            self.children[idx].label = f"✨ {carta['nombre']}"
            self.children[idx].style = discord.ButtonStyle.success
            self.children[idx].disabled = True

            embed = discord.Embed(
                title=f"✨ CROMO GIRADO: {carta['nombre']} ({carta['rareza']})",
                color=0xF1C40F
            )
            embed.add_field(name="👤 Atleta", value=f"**{carta['nombre']}** ({carta['genero']})", inline=True)
            embed.add_field(name="🛡️ Equipo", value=carta['equipo'], inline=True)
            embed.add_field(name="🌍 País / Posición", value=f"{carta['nacionalidad']} | `{carta['posicion']}`", inline=True)
            embed.add_field(name="📊 Atributos 3D", value=carta['stats'], inline=False)
            embed.set_image(url=carta["foto"])
            embed.set_footer(text=f"Progreso del sobre: {sum(self.reveladas)}/8 cartas giradas | ID: {carta['id']}")

            await interaction.response.edit_message(embed=embed, view=self)

        return card_callback

@bot.event
async def on_ready():
    print(f'✅ Bot listo como {bot.user.name}.')

# --- COMANDO 1: RECLAMAR SOBRE Y GUARDARLO EN EL INVENTARIO ---
@bot.command(name="sobre")
async def conseguir_sobre(ctx, deporte: str = None):
    if not deporte or deporte.lower() not in ["futbol", "nba", "nfl", "hockey"]:
        await ctx.send("❌ Uso correcto: `!sobre futbol`, `!sobre nba`, `!sobre nfl` o `!sobre hockey`.")
        return

    deporte = deporte.lower()
    user_id = ctx.author.id
    ahora = datetime.now()

    # Comprobar tiempo de espera (30 minutos)
    cursor.execute("SELECT ultimo_sobre FROM cooldowns WHERE user_id = ? AND deporte = ?", (user_id, deporte))
    resultado = cursor.fetchone()

    if resultado:
        ultimo_tiempo = datetime.fromisoformat(resultado[0])
        if ahora - ultimo_tiempo < timedelta(minutes=30):
            restante = timedelta(minutes=30) - (ahora - ultimo_tiempo)
            m, s = divmod(int(restante.total_seconds()), 60)
            await ctx.send(f"⏳ **{ctx.author.name}**, debes esperar **{m}m {s}s** para reclamar otro sobre de {deporte.upper()}.")
            return

    # Registrar el cooldown y guardar el sobre en el inventario
    cursor.execute("INSERT OR REPLACE INTO cooldowns VALUES (?, ?, ?)", (user_id, deporte, ahora.isoformat()))
    cursor.execute("SELECT cantidad FROM inventario_sobres WHERE user_id = ? AND deporte = ?", (user_id, deporte))
    row = cursor.fetchone()
    
    nueva_cantidad = (row[0] + 1) if row else 1
    cursor.execute("INSERT OR REPLACE INTO inventario_sobres VALUES (?, ?, ?)", (user_id, deporte, nueva_cantidad))
    conn.commit()

    embed = discord.Embed(
        title="📦 ¡SOBRE RECLAMADO Y GUARDADO!",
        description=f"¡Hola **{ctx.author.name}**! Has guardado **1 sobre de {deporte.upper()}** en tu inventario.\n\nUsa `!mis_sobres` para ver tus sobres guardados o `!abrir {deporte}` para abrirlo y girar las cartas.",
        color=0x2ECC71
    )
    await ctx.send(embed=embed)

# --- COMANDO 2: VER MOCHILA / INVENTARIO DE SOBRES ---
@bot.command(name="mis_sobres")
async def ver_mis_sobres(ctx):
    user_id = ctx.author.id
    cursor.execute("SELECT deporte, cantidad FROM inventario_sobres WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()

    embed = discord.Embed(title=f"🎒 Inventario de Sobres de {ctx.author.name}", color=0x3498DB)
    texto = ""
    
    sobres_dict = {f[0]: f[1] for f in rows}
    deportes = ["futbol", "nba", "nfl", "hockey"]

    for dep in deportes:
        cant = sobres_dict.get(dep, 0)
        texto += f"📦 **{dep.upper()}:** {cant} sobres sin abrir\n"

    embed.description = texto
    embed.set_footer(text="Usa !abrir [deporte] para usar un sobre y girar las cartas.")
    await ctx.send(embed=embed)

# --- COMANDO 3: ABRIR SOBRE DEL INVENTARIO Y GIRAR CARTAS ---
@bot.command(name="abrir")
async def abrir_sobre_guardado(ctx, deporte: str = None):
    if not deporte or deporte.lower() not in ["futbol", "nba", "nfl", "hockey"]:
        await ctx.send("❌ Especifica qué sobre de tu inventario quieres abrir: `!abrir futbol`, `!abrir nba`, `!abrir nfl` o `!abrir hockey`.")
        return

    deporte = deporte.lower()
    user_id = ctx.author.id

    cursor.execute("SELECT cantidad FROM inventario_sobres WHERE user_id = ? AND deporte = ?", (user_id, deporte))
    row = cursor.fetchone()

    if not row or row[0] <= 0:
        await ctx.send(f"❌ No tienes ningún sobre de **{deporte.upper()}** en tu inventario. Consigue uno usando `!sobre {deporte}`.")
        return

    # Restar 1 sobre del inventario
    cursor.execute("UPDATE inventario_sobres SET cantidad = cantidad - 1 WHERE user_id = ? AND deporte = ?", (user_id, deporte))
    
    # Generar 8 cartas dinámicas
    sobre_cartas = [generar_cromo_dinamico(deporte) for _ in range(8)]

    # Guardar cartas obtenidas en la colección
    for cromo in sobre_cartas:
        cursor.execute('''
        INSERT OR IGNORE INTO inventario_cartas 
        (user_id, cromo_id, nombre, equipo, nacionalidad, categoria, genero, rareza, posicion, stats, foto) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, cromo['id'], cromo['nombre'], cromo['equipo'], cromo['nacionalidad'], 
              cromo['categoria'], cromo['genero'], cromo['rareza'], cromo['posicion'], cromo['stats'], cromo['foto']))
    conn.commit()

    # Desplegar la vista interactiva con las 8 cartas para darles la vuelta
    view = FlipCardsPackView(user_id, sobre_cartas, deporte)
    embed = discord.Embed(
        title=f"📦 ¡ABRIENDO SOBRE DE {deporte.upper()}!",
        description=f"Has abierto 1 sobre de tu mochila.\n**Haz clic en los botones de abajo para girar y revelar cada una de las 8 cartas.**",
        color=0xF1C40F
    )
    await ctx.send(embed=embed, view=view)

# --- COMANDO 4: INTERCAMBIO DIRECTO ---
@bot.command(name="trade")
async def intercambiar(ctx, usuario: discord.Member, tu_cromo_id: str, su_cromo_id: str):
    if usuario.id == ctx.author.id:
        await ctx.send("❌ No puedes hacer intercambios contigo mismo.")
        return

    cursor.execute("SELECT * FROM inventario_cartas WHERE user_id = ? AND cromo_id = ?", (ctx.author.id, tu_cromo_id))
    cromo_tu = cursor.fetchone()
    if not cromo_tu:
        await ctx.send(f"❌ No tienes la carta con ID `{tu_cromo_id}`.")
        return

    cursor.execute("SELECT * FROM inventario_cartas WHERE user_id = ? AND cromo_id = ?", (usuario.id, su_cromo_id))
    cromo_su = cursor.fetchone()
    if not cromo_su:
        await ctx.send(f"❌ {usuario.mention} no posee la carta con ID `{su_cromo_id}`.")
        return

    cursor.execute("UPDATE inventario_cartas SET user_id = ? WHERE user_id = ? AND cromo_id = ?", (usuario.id, ctx.author.id, tu_cromo_id))
    cursor.execute("UPDATE inventario_cartas SET user_id = ? WHERE user_id = ? AND cromo_id = ?", (ctx.author.id, usuario.id, su_cromo_id))
    conn.commit()

    await ctx.send(f"🤝 **¡Intercambio Completado!**\n{ctx.author.mention} dio a **{cromo_tu[2]}** y recibió a **{cromo_su[2]}** de {usuario.mention}.")

# --- CONFIGURACIÓN AUTOMÁTICA DE CANALES Y NORMAS ---
@bot.command(name="setup_canales")
@commands.has_permissions(administrator=True)
async def setup_canales(ctx):
    guild = ctx.guild
    
    cat_general = await guild.create_category("🎴 JUEGO DE CROMOS GENERAL")
    chan_reglas = await guild.create_text_channel("anuncios-y-reglas", category=cat_general)
    await guild.create_text_channel("drops-especiales", category=cat_general)

    embed_reglas = discord.Embed(
        title="📜 REGLAMENTO OFICIAL DE LA COMUNIDAD (750.000+ MIEMBROS)",
        description="Normas generales para mantener un entorno justo y libre de trampas:",
        color=0xE74C3C
    )
    embed_reglas.add_field(name="1. Respeto Absoluto", value="Prohibido el acoso, toxicidad, insultos o discriminación.", inline=False)
    embed_reglas.add_field(name="2. Sistema de Sobres", value="Usa `!sobre [deporte]` cada 30 min para guardar sobres y `!abrir [deporte]` para abrir los que tengas acumulados.", inline=False)
    embed_reglas.add_field(name="3. Intercambios Seguros", value="Usa exclusivamente `!trade @usuario ID_tu_cromo ID_su_cromo` en los canales de tradeo.", inline=False)
    embed_reglas.add_field(name="4. Anti-Multicuentas", value="Prohibido usar cuentas secundarias (alts) para acumular sobres.", inline=False)
    await chan_reglas.send(embed_reglas)

    deportes = [("⚽ FÚTBOL", "futbol"), ("🏀 NBA", "nba"), ("🏈 NFL", "nfl"), ("🏒 HOCKEY", "hockey")]
    for titulo, prefijo in deportes:
        cat = await guild.create_category(titulo)
        await guild.create_text_channel(f"chat-{prefijo}", category=cat)
        await guild.create_text_channel(f"intercambios-{prefijo}", category=cat)
        await guild.create_text_channel(f"galeria-{prefijo}", category=cat)

    await ctx.send("✅ ¡Estructura de canales creada y sistema de sobres por inventario activo!")

# --- SERVIDOR WEB FLASK (KEEP-ALIVE RENDER) ---
app = Flask('')

@app.route('/')
def home():
    return "¡Servidor de sobres y cromos activo 24/7!"

def run_web():
    app.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = Thread(target=run_web)
    t.start()

if __name__ == "__main__":
    keep_alive()
    bot.run(os.environ.get("DISCORD_TOKEN"))
